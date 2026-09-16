/**
 * Smart MCP Proxy — shared core.
 *
 * Everything that decides what an agent gets to see lives here, so the
 * MCP server, the `smart-bash` CLI and the `smart-bash-hook` PreToolUse hook
 * behave identically: run a command, return short output verbatim, condense
 * long output with a local Ollama model, and always append the
 * deterministic blocks (ERROR SIGNATURES, RAW TAIL) that the benchmark
 * showed were needed for the agent to trust the result.
 *
 * Configuration (environment variables, all optional):
 *   OLLAMA_URL                 Ollama base URL      (default: http://localhost:11434)
 *   OLLAMA_MODEL               Model to summarize   (default: qwen2.5-coder:3b)
 *   OLLAMA_TIMEOUT_MS          HTTP timeout         (default: 60000)
 *   SMART_MCP_MAX_CHARS        Raw-output budget    (default: 2000)
 *   SMART_MCP_MODE             "deterministic" = never call the model (signatures + excerpt only)
 *   SMART_MCP_EXEC_TIMEOUT_MS  Command timeout      (default: 300000)
 *   SMART_MCP_MAX_BUFFER       exec maxBuffer bytes (default: 50 MiB)
 */

import { exec } from "node:child_process";
import { promisify } from "node:util";
import axios from "axios";

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

export const CONFIG = {
  ollamaUrl: (process.env.OLLAMA_URL ?? "http://localhost:11434").replace(/\/+$/, ""),
  ollamaModel: process.env.OLLAMA_MODEL ?? "qwen2.5-coder:3b",
  ollamaTimeoutMs: envInt("OLLAMA_TIMEOUT_MS", 60_000),
  maxChars: envInt("SMART_MCP_MAX_CHARS", 2_000),
  /** SMART_MCP_MODE=deterministic: never call the model; condense with error signatures + head/tail excerpt only. */
  deterministic: (process.env.SMART_MCP_MODE ?? "").toLowerCase() === "deterministic",
  execTimeoutMs: envInt("SMART_MCP_EXEC_TIMEOUT_MS", 300_000),
  maxBufferBytes: envInt("SMART_MCP_MAX_BUFFER", 50 * 1024 * 1024),
} as const;

/**
 * Hard cap on how much raw text we send to the local model. Small models
 * have short context windows; sending an unbounded log would silently
 * truncate at the model side and lose the tail (where the error usually is).
 */
export const OLLAMA_INPUT_CAP = 24_000;

/** Max tokens the model may emit. A summary must stay small by construction. */
export const OLLAMA_NUM_PREDICT = 400;

/** Verbatim tail appended after every summary, so exit summaries survive even when the model drops them. */
export const RAW_TAIL_LINES = 8;

/** Cap on raw output returned via raw_id / force_raw, comparable to Claude Code's own Bash truncation. */
export const RAW_RETURN_CAP = 12_000;

export const LOG_SYSTEM_PROMPT = `You are a log filter, not an assistant. You never explain, never suggest fixes, never write code.
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

export const DIFF_SYSTEM_PROMPT = `You summarize a git diff of ONE file for a code reviewer.
Output ONLY 1 to 3 short bullet lines (each starting with "- "), naming what changed: functions/classes/config keys added, removed or renamed, and any behavior change. Use identifiers from the diff verbatim.
No code, no advice, no praise, no markdown fences, max 60 words total.`;

// ---------------------------------------------------------------------------
// Command execution
// ---------------------------------------------------------------------------

export interface CommandResult {
  stdout: string;
  stderr: string;
  exitCode: number | null;
  signal: string | null;
  timedOut: boolean;
}

export async function runCommand(command: string, cwd?: string): Promise<CommandResult> {
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

export function combineOutput(result: CommandResult): string {
  const parts: string[] = [];
  if (result.stdout.trim()) parts.push(result.stdout.trimEnd());
  if (result.stderr.trim()) parts.push(`--- stderr ---\n${result.stderr.trimEnd()}`);
  return parts.join("\n");
}

export function statusLine(result: CommandResult): string {
  if (result.timedOut) return `[exit: timed out after ${CONFIG.execTimeoutMs} ms]`;
  if (result.signal) return `[exit: killed by ${result.signal}]`;
  return `[exit code: ${result.exitCode ?? "unknown"}]`;
}

/** Exit code a wrapper process should propagate for this result. */
export function exitCodeFor(result: CommandResult): number {
  if (result.timedOut) return 124;
  if (result.exitCode !== null) return result.exitCode;
  return 1;
}

// ---------------------------------------------------------------------------
// Deterministic text helpers
// ---------------------------------------------------------------------------

/**
 * Keep the head and (mostly) the tail of an oversized log. Errors and final
 * results cluster at the end; the head keeps the command context.
 */
export function headTail(text: string, budget: number): string {
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
const ANSI_RE = /\[[0-9;?]*[ -/]*[@-~]/g;

/** Strip ANSI escapes and collapse runs of identical consecutive lines (spinners, repeated warnings). */
export function normalizeOutput(text: string): string {
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
export function cleanSummary(text: string): string {
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

/**
 * Extract distinct error-looking lines with occurrence counts, most frequent
 * first, each with the nearest project frame. Guarantees the root-cause line
 * survives even when the model summarizes only file lists.
 */
export function errorSignatures(text: string): string {
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

export function rawTail(text: string, lines: number): string {
  const all = text.trimEnd().split("\n");
  return all.slice(-lines).join("\n");
}

// ---------------------------------------------------------------------------
// Ollama
// ---------------------------------------------------------------------------

export async function ollamaGenerate(system: string, prompt: string): Promise<string> {
  if (CONFIG.deterministic) throw new Error("model disabled (SMART_MCP_MODE=deterministic)");
  const response = await axios.post(
    `${CONFIG.ollamaUrl}/api/generate`,
    {
      model: CONFIG.ollamaModel,
      system,
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

export async function summarizeLog(command: string, output: string): Promise<string> {
  const clipped = headTail(normalizeOutput(output), OLLAMA_INPUT_CAP);
  const prompt = `Command executed:\n${command}\n\nRaw output:\n${clipped}\n\nProduce the ERRORS / RESULT block and nothing else.`;
  return ollamaGenerate(LOG_SYSTEM_PROMPT, prompt);
}

export function describeOllamaError(error: unknown): string {
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

export interface CachedRaw {
  command: string;
  output: string;
  status: string;
}

export class RawCache {
  private readonly entries = new Map<string, CachedRaw>();
  private counter = 0;
  constructor(private readonly size = 20) {}

  put(entry: CachedRaw): string {
    const id = `r${++this.counter}`;
    this.entries.set(id, entry);
    if (this.entries.size > this.size) this.entries.delete(this.entries.keys().next().value as string);
    return id;
  }

  get(id: string): CachedRaw | undefined {
    return this.entries.get(id);
  }
}

// ---------------------------------------------------------------------------
// Condensation — the one decision function shared by every entry point
// ---------------------------------------------------------------------------

export type CondenseMode = "verbatim" | "condensed" | "excerpt" | "fallback" | "deterministic";

export interface Condensed {
  mode: CondenseMode;
  /** Full text to hand to the agent (without the status line). */
  text: string;
  rawId?: string;
}

/**
 * Decide what the agent gets for a command's combined output.
 *
 * - under `maxChars`: verbatim;
 * - otherwise the local model condenses it, and the deterministic
 *   ERROR SIGNATURES + RAW TAIL blocks are appended;
 * - a summary that is no shorter than a plain excerpt is replaced by the excerpt;
 * - if the model is unreachable, a truncated excerpt + signatures + warning;
 * - whatever was built, if it (plus the caller's `overhead`) is not smaller
 *   than the raw output, the raw output is returned verbatim (mode "verbatim").
 */
export async function condense(
  command: string,
  output: string,
  status: string,
  cache?: RawCache,
  /** Chars the caller will add around `text` (command echo, status line); counted by the size guard. */
  overhead = 0,
): Promise<Condensed> {
  if (output.length <= CONFIG.maxChars) {
    return { mode: "verbatim", text: output };
  }
  const envelope = await buildEnvelope(command, output, status, cache);
  // Seen in real sessions: output just above the budget (grep listings of
  // ~2.1k chars) came back as a 2.3k-char envelope — header, summary that
  // re-emitted the listing, and RAW TAIL together outgrew the raw output.
  // An envelope that saves nothing is worse than nothing: hand the output over as-is.
  if (envelope.text.length + overhead >= output.length) {
    return { mode: "verbatim", text: output };
  }
  return envelope;
}

async function buildEnvelope(
  command: string,
  output: string,
  status: string,
  cache?: RawCache,
): Promise<Condensed> {
  const rawId = cache?.put({ command, output, status });
  const idNote = rawId ? ` raw_id=${rawId}` : "";
  const signatures = errorSignatures(output);
  if (CONFIG.deterministic) {
    const lineCount = output.split("\n").length;
    const header = `[smart-mcp-proxy] ${output.length} chars / ${lineCount} lines condensed (error lines verbatim, head/tail excerpt).${idNote}`;
    const excerpt = `EXCERPT (head/tail, verbatim):\n${headTail(output, CONFIG.maxChars)}`;
    return { mode: "deterministic", rawId, text: [header, signatures, excerpt].filter(Boolean).join("\n\n") };
  }
  try {
    const summary = await summarizeLog(command, output);
    const excerpt = headTail(output, CONFIG.maxChars);
    if (summary.length >= excerpt.length) {
      const header = `[smart-mcp-proxy] Output was ${output.length} chars; ${CONFIG.ollamaModel} summary was not shorter than a plain excerpt, showing the excerpt instead.${idNote}`;
      return { mode: "excerpt", rawId, text: [header, excerpt, signatures].filter(Boolean).join("\n\n") };
    }
    const lineCount = output.split("\n").length;
    const header = `[smart-mcp-proxy] ${output.length} chars / ${lineCount} lines condensed (error lines verbatim).${idNote}`;
    const tail = `RAW TAIL (last ${RAW_TAIL_LINES} lines, verbatim):\n${rawTail(output, RAW_TAIL_LINES)}`;
    return { mode: "condensed", rawId, text: [header, summary, signatures, tail].filter(Boolean).join("\n\n") };
  } catch (error) {
    const reason = describeOllamaError(error);
    const header = `[smart-mcp-proxy] WARNING: summarization failed (${reason}). Showing a truncated excerpt of the ${output.length}-char output.${idNote}`;
    return { mode: "fallback", rawId, text: [header, headTail(output, CONFIG.maxChars), signatures].filter(Boolean).join("\n\n") };
  }
}

// ---------------------------------------------------------------------------
// Git diff summarization
// ---------------------------------------------------------------------------

export interface DiffFile {
  file: string;
  text: string;
}

/** Split a unified diff into per-file blocks, keyed by the `+++ b/<path>` (or `--- a/<path>` for deletions). */
export function splitDiffByFile(diff: string): DiffFile[] {
  const blocks = diff.split(/^(?=diff --git )/m).filter((b) => b.trim() !== "");
  return blocks.map((text) => {
    const header = /^diff --git a\/(.+?) b\/(.+)$/m.exec(text);
    const file = header ? header[2] : "(unknown)";
    return { file, text };
  });
}

/** Per-file input cap sent to the model; large files are head/tail clipped. */
export const DIFF_FILE_CAP = 6_000;
/** Total model input budget across files. */
export const DIFF_TOTAL_CAP = OLLAMA_INPUT_CAP;

export interface DiffSummary {
  stat: string;
  bullets: string[];
  skipped: string[];
  warning?: string;
}

export async function summarizeDiff(diff: string, stat: string): Promise<DiffSummary> {
  const files = splitDiffByFile(diff);
  const bullets: string[] = [];
  const skipped: string[] = [];
  let spent = 0;
  let warning: string | undefined;
  for (const f of files) {
    const clipped = headTail(f.text, DIFF_FILE_CAP);
    if (spent + clipped.length > DIFF_TOTAL_CAP) {
      skipped.push(f.file);
      continue;
    }
    spent += clipped.length;
    try {
      const out = await ollamaGenerate(DIFF_SYSTEM_PROMPT, `Diff of ${f.file}:\n${clipped}\n\nBullets:`);
      const lines = out
        .split("\n")
        .map((l) => l.trim())
        .filter((l) => l.startsWith("-"))
        .slice(0, 3);
      bullets.push(`${f.file}\n${(lines.length ? lines : [`- ${out.split("\n")[0]}`]).map((l) => `  ${l}`).join("\n")}`);
    } catch (error) {
      warning = `summarization stopped: ${describeOllamaError(error)}`;
      skipped.push(f.file, ...files.slice(files.indexOf(f) + 1).map((x) => x.file));
      break;
    }
  }
  return { stat, bullets, skipped, warning };
}

export function renderDiffSummary(range: string, s: DiffSummary): string {
  const parts = [`[smart-mcp-proxy] git diff ${range} — --stat verbatim, then one summary per file by ${CONFIG.ollamaModel}.`, s.stat.trimEnd()];
  if (s.bullets.length) parts.push(`SUMMARY BY FILE:\n${s.bullets.join("\n")}`);
  if (s.skipped.length) parts.push(`NOT SUMMARIZED (${s.skipped.length}, over the input budget or model unavailable):\n${s.skipped.map((f) => `  ${f}`).join("\n")}`);
  if (s.warning) parts.push(`WARNING: ${s.warning}`);
  return parts.join("\n\n");
}
