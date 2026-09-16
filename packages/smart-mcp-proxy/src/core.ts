/**
 * Smart MCP Proxy — shared core.
 *
 * Everything that decides what an agent gets to see lives here, so the
 * MCP server, the `smart-bash` CLI and the `smart-bash-hook` PreToolUse hook
 * behave identically: run a command, return short output verbatim, and
 * condense long output deterministically — error lines extracted verbatim
 * with the nearest project frame, plus a head/tail excerpt.
 *
 * No model is involved. A local-model summarizer existed until 0.3.0; it was
 * removed in 0.4.0 after measurement: BENCHMARK.md showed it matched this
 * path's accuracy while costing ~4 s per call, and two independent studies of
 * an equivalent tool (JetBrains, 425 trials; Quesma, 1,740 attempts) found
 * such preprocessing raises cost per task because it inflates turn count.
 * Nothing here may rewrite output: every byte an agent sees is copied verbatim
 * from the command it ran.
 *
 * Configuration (environment variables, all optional):
 *   SMART_MCP_MAX_CHARS        Raw-output budget    (default: 2000)
 *   SMART_MCP_EXEC_TIMEOUT_MS  Command timeout      (default: 300000)
 *   SMART_MCP_MAX_BUFFER       exec maxBuffer bytes (default: 50 MiB)
 */

import { exec } from "node:child_process";
import { promisify } from "node:util";

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
  maxChars: envInt("SMART_MCP_MAX_CHARS", 2_000),
  execTimeoutMs: envInt("SMART_MCP_EXEC_TIMEOUT_MS", 300_000),
  maxBufferBytes: envInt("SMART_MCP_MAX_BUFFER", 50 * 1024 * 1024),
} as const;

/** Verbatim tail of the output, kept available for callers that want the last lines. */
export const RAW_TAIL_LINES = 8;

/** Cap on raw output returned via raw_id / force_raw, comparable to Claude Code's own Bash truncation. */
export const RAW_RETURN_CAP = 12_000;

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
 * survives regardless of how much of the output is excerpted.
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

export type CondenseMode = "verbatim" | "condensed";

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
 * - otherwise: ERROR SIGNATURES (verbatim error lines + nearest project frame)
 *   plus a head/tail EXCERPT, both copied from the output, never rewritten;
 * - if that envelope (plus the caller's `overhead`) would not be smaller than
 *   the raw output, the raw output is returned verbatim.
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
  const rawId = cache?.put({ command, output, status });
  const idNote = rawId ? ` raw_id=${rawId}` : "";
  const signatures = errorSignatures(output);
  const lineCount = output.split("\n").length;
  const header = `[smart-mcp-proxy] ${output.length} chars / ${lineCount} lines condensed (error lines verbatim, head/tail excerpt).${idNote}`;
  const excerpt = `EXCERPT (head/tail, verbatim):\n${headTail(output, CONFIG.maxChars)}`;
  const text = [header, signatures, excerpt].filter(Boolean).join("\n\n");
  // An envelope that saves nothing is worse than nothing: hand the output over as-is.
  // Seen in real sessions: grep listings just above the budget came back larger than the raw output.
  if (text.length + overhead >= output.length) {
    return { mode: "verbatim", text: output };
  }
  return { mode: "condensed", rawId, text };
}
