#!/usr/bin/env node
/**
 * Smart MCP Proxy — ai-augmented-developer
 *
 * Exposes a single MCP tool, `smart_bash_execute`, that runs a shell
 * command and returns its output. When the combined stdout + stderr
 * exceeds a safe character budget, the output is condensed by a local
 * Ollama model (root error, clean stack trace, final result) before it
 * is handed back to the calling agent, so huge logs never flood the
 * agent's context window.
 *
 * Configuration (environment variables, all optional):
 *   OLLAMA_URL            Ollama base URL      (default: http://localhost:11434)
 *   OLLAMA_MODEL          Model to summarize   (default: qwen2.5-coder:3b)
 *   OLLAMA_TIMEOUT_MS     HTTP timeout         (default: 60000)
 *   SMART_MCP_MAX_CHARS   Raw-output budget    (default: 2000)
 *   SMART_MCP_EXEC_TIMEOUT_MS  Command timeout (default: 300000)
 *   SMART_MCP_MAX_BUFFER  exec maxBuffer bytes (default: 50 MiB)
 */

import { exec } from "node:child_process";
import { promisify } from "node:util";
import axios from "axios";
import { z } from "zod";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";

const execAsync = promisify(exec);

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

function envInt(name: string, fallback: number): number {
  const raw = process.env[name];
  if (raw === undefined || raw.trim() === "") return fallback;
  const parsed = Number.parseInt(raw, 10);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
}

const CONFIG = {
  ollamaUrl: (process.env.OLLAMA_URL ?? "http://localhost:11434").replace(/\/+$/, ""),
  ollamaModel: process.env.OLLAMA_MODEL ?? "qwen2.5-coder:3b",
  ollamaTimeoutMs: envInt("OLLAMA_TIMEOUT_MS", 60_000),
  maxChars: envInt("SMART_MCP_MAX_CHARS", 2_000),
  execTimeoutMs: envInt("SMART_MCP_EXEC_TIMEOUT_MS", 300_000),
  maxBufferBytes: envInt("SMART_MCP_MAX_BUFFER", 50 * 1024 * 1024),
} as const;

/**
 * Hard cap on how much raw text we send to the local model. Small models
 * have short context windows; sending an unbounded log would silently
 * truncate at the model side and lose the tail (where the error usually is).
 */
const OLLAMA_INPUT_CAP = 24_000;

const SYSTEM_PROMPT = `You are a log filter, not an assistant. You never explain, never suggest fixes, never write code.
Input: the raw output of a shell command. Output: ONLY the lines that matter, copied verbatim, in exactly this format:

ERRORS:
<verbatim lines, or "none">
RESULT:
<verbatim lines, or "none">

What counts as ERRORS (always include when present):
- Exception / error messages and their stack frames (keep frames in project files; drop frames inside node_modules, site-packages, /usr/lib).
- Failing tests: lines marked ✕, ✗, FAIL, FAILED, ERROR, ●, and the assertion detail that follows (expect/Expected/Received/AssertionError/diff lines, and the "at file:line" frame).
- Compiler / linter / type errors with file:line.
What counts as RESULT:
- Final summary lines: test counts (passed/failed), build success/failure, exit summaries, produced artifacts, warnings that affect correctness.
Never include: progress bars, download/compile progress, spinners, timestamps, passing-test lines (✓), repeated lines.
Never add commentary, explanations, advice or markdown fences.`;

/** Max tokens the model may emit. A summary must stay small by construction. */
const OLLAMA_NUM_PREDICT = 400;

/** Verbatim tail appended after every summary, so exit summaries survive even when the model drops them. */
const RAW_TAIL_LINES = 8;

// ---------------------------------------------------------------------------
// Command execution
// ---------------------------------------------------------------------------

interface CommandResult {
  stdout: string;
  stderr: string;
  exitCode: number | null;
  signal: string | null;
  timedOut: boolean;
}

async function runCommand(command: string, cwd?: string): Promise<CommandResult> {
  try {
    const { stdout, stderr } = await execAsync(command, {
      cwd,
      timeout: CONFIG.execTimeoutMs,
      maxBuffer: CONFIG.maxBufferBytes,
      encoding: "utf8",
      shell: process.env.SHELL || undefined,
    });
    return { stdout, stderr, exitCode: 0, signal: null, timedOut: false };
  } catch (error: unknown) {
    // `exec` rejects on non-zero exit, on timeout and on maxBuffer overflow.
    // In every case the error object carries whatever output was captured.
    const err = error as NodeJS.ErrnoException & {
      stdout?: string;
      stderr?: string;
      code?: number | string;
      signal?: string;
      killed?: boolean;
    };
    const exitCode = typeof err.code === "number" ? err.code : null;
    const timedOut = err.killed === true && err.signal === "SIGTERM";
    const stderr =
      (err.stderr ?? "") +
      (typeof err.code === "string" ? `\n[smart-mcp-proxy] exec error: ${err.code} ${err.message}` : "");
    return {
      stdout: err.stdout ?? "",
      stderr,
      exitCode,
      signal: err.signal ?? null,
      timedOut,
    };
  }
}

function combineOutput(result: CommandResult): string {
  const parts: string[] = [];
  if (result.stdout.trim()) parts.push(result.stdout.trimEnd());
  if (result.stderr.trim()) parts.push(`--- stderr ---\n${result.stderr.trimEnd()}`);
  return parts.join("\n");
}

function statusLine(result: CommandResult): string {
  if (result.timedOut) return `[exit: timed out after ${CONFIG.execTimeoutMs} ms]`;
  if (result.signal) return `[exit: killed by ${result.signal}]`;
  return `[exit code: ${result.exitCode ?? "unknown"}]`;
}

// ---------------------------------------------------------------------------
// Ollama summarization
// ---------------------------------------------------------------------------

/**
 * Keep the head and (mostly) the tail of an oversized log. Errors and final
 * results cluster at the end; the head keeps the command context.
 */
function headTail(text: string, budget: number): string {
  if (text.length <= budget) return text;
  const headBudget = Math.floor(budget * 0.25);
  const tailBudget = budget - headBudget;
  const omitted = text.length - headBudget - tailBudget;
  return (
    text.slice(0, headBudget) +
    `\n\n[... ${omitted} characters omitted ...]\n\n` +
    text.slice(text.length - tailBudget)
  );
}

// eslint-disable-next-line no-control-regex
const ANSI_RE = /\u001b\[[0-9;?]*[ -/]*[@-~]/g;

/** Strip ANSI escapes and collapse runs of identical consecutive lines (spinners, repeated warnings). */
function normalizeOutput(text: string): string {
  const lines = text.replace(ANSI_RE, "").replace(/\r(?!\n)/g, "\n").split("\n");
  const out: string[] = [];
  let prev: string | undefined;
  let repeats = 0;
  const flush = () => {
    if (repeats > 1) out.push(`[previous line repeated ${repeats - 1} more time(s)]`);
    repeats = 0;
  };
  for (const line of lines) {
    if (line === prev && line.trim() !== "") {
      repeats++;
      continue;
    }
    flush();
    out.push(line);
    prev = line;
    repeats = 1;
  }
  flush();
  return out.join("\n");
}

/** Small models sometimes wrap the answer in fences or add a label line; strip both. */
function cleanSummary(text: string): string {
  return text
    .split("\n")
    .filter((line) => !/^\s*```[a-z]*\s*$/i.test(line))
    .filter((line) => !/^\s*ERRORS \/ RESULT block:\s*$/i.test(line))
    .join("\n")
    .trim();
}

/** Lines that look like error signatures. Deterministic, model-independent. */
const ERROR_LINE_RE =
  /(\b[A-Za-z_][\w.]*(?:Error|Exception|Failure)\b\s*[:(]|^\s*Traceback \(most recent call last\)|^\s*(?:FAIL|FAILED|ERROR|E)\b\s+\S|^\s*(?:fatal|panic|error)\s*(?:\[[\w-]+\])?\s*:|^\s*npm ERR!|^\s*[✕✗●]\s+\S)/i;
const MAX_SIGNATURES = 6;

/**
 * Extract distinct error-looking lines with occurrence counts, most frequent first.
 * Guarantees the root-cause line survives even when the model summarizes only file lists.
 */
const FRAME_RE = /((?:[A-Za-z]:)?[\w@./-]+\.[A-Za-z]{1,6}):(\d+)(?::\d+)?/;
/** Python-style frame: File "path", line N */
const PY_FRAME_RE = /File "([^"]+)", line (\d+)/;
/** A line that already names a file path (e.g. "ERROR tests/x.py") needs no frame lookup. */
const HAS_PATH_RE = /(?:^|[\s("'])[\w@.-]*\/[\w@./-]*\.[A-Za-z]{1,6}\b/;
const VENDOR_RE = /node_modules|site-packages|dist-packages|\/usr\/lib\/|\/opt\/homebrew\/Cellar|<frozen/;
const FRAME_LOOKBACK = 12;

/** Nearest project file:line reference around an error line (looks back, then forward for JS-style stacks). */
function nearestFrame(lines: string[], idx: number): string | undefined {
  const scan = (from: number, to: number, step: number) => {
    for (let i = from; step > 0 ? i <= to : i >= to; i += step) {
      const line = lines[i];
      if (!line || VENDOR_RE.test(line)) continue;
      const m = PY_FRAME_RE.exec(line) ?? FRAME_RE.exec(line);
      if (m) return `${m[1]}:${m[2]}`;
    }
    return undefined;
  };
  return (
    scan(Math.max(0, idx - 1), Math.max(0, idx - FRAME_LOOKBACK), -1) ??
    scan(idx + 1, Math.min(lines.length - 1, idx + FRAME_LOOKBACK), 1)
  );
}

function errorSignatures(text: string): string {
  const lines = text.split("\n");
  const counts = new Map<string, { n: number; frame?: string }>();
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim().slice(0, 200);
    if (!line || !ERROR_LINE_RE.test(line)) continue;
    const entry = counts.get(line) ?? { n: 0 };
    entry.n++;
    if (!entry.frame) {
      // Skip when the line itself already carries a location.
      entry.frame = FRAME_RE.test(line) || HAS_PATH_RE.test(line) ? undefined : nearestFrame(lines, i);
    }
    counts.set(line, entry);
  }
  if (counts.size === 0) return "";
  const top = [...counts.entries()].sort((a, b) => b[1].n - a[1].n).slice(0, MAX_SIGNATURES);
  const rest = counts.size - top.length;
  const out = top.map(([line, { n, frame }]) => `${line}${n > 1 ? `   (x${n})` : ""}${frame ? `\n    ↳ at ${frame}` : ""}`);
  if (rest > 0) out.push(`... and ${rest} more distinct error-like line(s)`);
  return `ERROR SIGNATURES (deterministic grep of error-like lines; ${counts.size} distinct line(s), one failure may produce several):\n${out.join("\n")}`;
}

function rawTail(text: string, lines: number): string {
  const all = text.trimEnd().split("\n");
  return all.slice(-lines).join("\n");
}

async function summarizeWithOllama(command: string, output: string): Promise<string> {
  const clipped = headTail(normalizeOutput(output), OLLAMA_INPUT_CAP);
  const prompt = `Command executed:\n${command}\n\nRaw output:\n${clipped}\n\nProduce the ERRORS / RESULT block and nothing else.`;

  const response = await axios.post(
    `${CONFIG.ollamaUrl}/api/generate`,
    {
      model: CONFIG.ollamaModel,
      system: SYSTEM_PROMPT,
      prompt,
      stream: false,
      options: { temperature: 0, num_predict: OLLAMA_NUM_PREDICT },
    },
    { timeout: CONFIG.ollamaTimeoutMs },
  );

  const text: unknown = response.data?.response;
  if (typeof text !== "string" || text.trim() === "") {
    throw new Error("Ollama returned an empty response");
  }
  return cleanSummary(text);
}

function describeOllamaError(error: unknown): string {
  if (axios.isAxiosError(error)) {
    if (error.code === "ECONNREFUSED") return `Ollama unreachable at ${CONFIG.ollamaUrl} (connection refused)`;
    if (error.code === "ECONNABORTED") return `Ollama timed out after ${CONFIG.ollamaTimeoutMs} ms`;
    if (error.response) {
      const body = typeof error.response.data === "object" ? JSON.stringify(error.response.data) : String(error.response.data);
      return `Ollama HTTP ${error.response.status}: ${body.slice(0, 300)}`;
    }
    return `Ollama request failed: ${error.message}`;
  }
  return error instanceof Error ? error.message : String(error);
}

// ---------------------------------------------------------------------------
// Raw output cache — lets the agent fetch the full output of a previous call
// without re-executing the command (re-running tests/deploys is not free).
// ---------------------------------------------------------------------------

const RAW_CACHE_SIZE = 20;
/** Cap on raw output returned via raw_id / force_raw, comparable to Claude Code's own Bash truncation. */
const RAW_RETURN_CAP = 12_000;
const rawCache = new Map<string, { command: string; output: string; status: string }>();
let rawCounter = 0;

function cacheRaw(command: string, output: string, status: string): string {
  const id = `r${++rawCounter}`;
  rawCache.set(id, { command, output, status });
  if (rawCache.size > RAW_CACHE_SIZE) rawCache.delete(rawCache.keys().next().value as string);
  return id;
}

// ---------------------------------------------------------------------------
// MCP server
// ---------------------------------------------------------------------------

const server = new McpServer({
  name: "ai-augmented-dev-smart-mcp",
  version: "0.1.0",
});

server.tool(
  "smart_bash_execute",
  [
    "Run a shell command and return its output.",
    `If stdout+stderr exceed ${CONFIG.maxChars} characters, the output is condensed by a local`,
    `Ollama model (${CONFIG.ollamaModel}) down to root errors, clean stack traces and final results.`,
    "Use it for noisy commands (test suites, builds, installs, long logs) to protect the context window.",
    "Condensed responses copy error lines verbatim and append a deterministic ERROR SIGNATURES block and the raw tail;",
    "treat them as sufficient for root-cause answers. Only if something essential is missing, pass raw_id (from the header)",
    "to read the cached raw output without re-running the command.",
  ].join(" "),
  {
    command: z.string().min(1).describe("The shell command to execute."),
    cwd: z.string().optional().describe("Working directory for the command. Defaults to the server's cwd."),
    force_raw: z
      .boolean()
      .optional()
      .describe("If true, skip summarization and return the raw output even when it is long (it will still be truncated at the input cap)."),
    raw_id: z
      .string()
      .optional()
      .describe("Return the cached raw output of a previous call (id from its response header) WITHOUT re-running any command. `command` is ignored when set."),
  },
  async ({ command, cwd, force_raw, raw_id }) => {
    if (raw_id) {
      const cached = rawCache.get(raw_id);
      if (!cached) {
        return { isError: true, content: [{ type: "text", text: `[smart-mcp-proxy] no cached output for raw_id=${raw_id} (cache keeps the last ${RAW_CACHE_SIZE} calls).` }] };
      }
      const header = `[smart-mcp-proxy] cached raw output of: ${cached.command} (${cached.output.length} chars)`;
      return { isError: false, content: [{ type: "text", text: `${header}\n\n${headTail(cached.output, RAW_RETURN_CAP)}\n\n${cached.status}` }] };
    }

    const result = await runCommand(command, cwd);
    const output = combineOutput(result);
    const status = statusLine(result);
    const isError = result.exitCode !== 0;

    // Short output: return verbatim.
    if (output.length <= CONFIG.maxChars) {
      return {
        isError,
        content: [{ type: "text", text: output ? `${output}\n${status}` : status }],
      };
    }

    // Explicit opt-out of summarization.
    if (force_raw) {
      return {
        isError,
        content: [{ type: "text", text: `${headTail(output, RAW_RETURN_CAP)}\n${status}` }],
      };
    }

    // Long output: summarize with Ollama, fall back to a truncated excerpt.
    try {
      const summary = await summarizeWithOllama(command, output);
      const excerpt = headTail(output, CONFIG.maxChars);
      // A summary that is no shorter than the excerpt defeats its purpose; prefer the deterministic excerpt.
      if (summary.length >= excerpt.length) {
        const id = cacheRaw(command, output, status);
        const header = `[smart-mcp-proxy] Output was ${output.length} chars; ${CONFIG.ollamaModel} summary was not shorter than a plain excerpt, showing the excerpt instead. Full output cached as raw_id=${id}.`;
        return { isError, content: [{ type: "text", text: `${header}\n\n${excerpt}\n\n${status}` }] };
      }
      const lineCount = output.split("\n").length;
      const id = cacheRaw(command, output, status);
      const header = `[smart-mcp-proxy] ${output.length} chars / ${lineCount} lines condensed (error lines verbatim). raw_id=${id}`;
      const tail = `RAW TAIL (last ${RAW_TAIL_LINES} lines, verbatim):\n${rawTail(output, RAW_TAIL_LINES)}`;
      const signatures = errorSignatures(output);
      const body = [summary, signatures, tail].filter(Boolean).join("\n\n");
      return {
        isError,
        content: [{ type: "text", text: `${header}\n\n${body}\n\n${status}` }],
      };
    } catch (error) {
      const reason = describeOllamaError(error);
      const id = cacheRaw(command, output, status);
      const header = `[smart-mcp-proxy] WARNING: summarization failed (${reason}). Showing a truncated excerpt of the ${output.length}-char output. Full output cached as raw_id=${id}.`;
      const body = [headTail(output, CONFIG.maxChars), errorSignatures(output)].filter(Boolean).join("\n\n");
      return {
        isError,
        content: [{ type: "text", text: `${header}\n\n${body}\n\n${status}` }],
      };
    }
  },
);

async function main(): Promise<void> {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  // stdout is the MCP channel; diagnostics must go to stderr.
  console.error(
    `[smart-mcp-proxy] ready — model=${CONFIG.ollamaModel} url=${CONFIG.ollamaUrl} maxChars=${CONFIG.maxChars}`,
  );
}

main().catch((error) => {
  console.error("[smart-mcp-proxy] fatal:", error);
  process.exit(1);
});
