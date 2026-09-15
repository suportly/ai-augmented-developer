#!/usr/bin/env node
/**
 * smart-bash — run a command and print its output condensed.
 *
 * Usage:
 *   smart-bash --b64 <base64-encoded command>   (what the PreToolUse hook emits)
 *   smart-bash -c "<command>"
 *   smart-bash -- <command words...>
 *
 * Short output (≤ SMART_MCP_MAX_CHARS) is printed byte-for-byte: stdout to
 * stdout, stderr to stderr. Long output is condensed through core.ts and
 * printed to stdout with a truncated echo of the command on the first line;
 * if the condensed envelope would not be smaller than the raw output, the
 * raw output is printed byte-for-byte instead. The exit code of the
 * original command is always propagated.
 */

import { CONFIG, combineOutput, condense, exitCodeFor, runCommand, statusLine } from "./core.js";

function parseArgs(argv: string[]): string | null {
  const [flag, ...rest] = argv;
  if (flag === "--b64" && rest[0]) return Buffer.from(rest[0], "base64").toString("utf8");
  if (flag === "-c" && rest[0] !== undefined) return rest[0];
  if (flag === "--" && rest.length) return rest.join(" ");
  if (flag && !flag.startsWith("-")) return argv.join(" ");
  return null;
}

async function main(): Promise<number> {
  const command = parseArgs(process.argv.slice(2));
  if (!command) {
    process.stderr.write("usage: smart-bash --b64 <base64> | -c <command> | -- <command...>\n");
    return 64;
  }
  const result = await runCommand(command, process.cwd());
  const output = combineOutput(result);
  if (output.length <= CONFIG.maxChars) {
    // Verbatim: preserve the stream split so callers see exactly what the command produced.
    if (result.stdout) process.stdout.write(result.stdout);
    if (result.stderr) process.stderr.write(result.stderr);
    return exitCodeFor(result);
  }
  const status = statusLine(result);
  const echo = `[smart-bash] $ ${shortCommand(command)}`;
  const c = await condense(command, output, status, undefined, echo.length + status.length + 3);
  if (c.mode === "verbatim") {
    // Condensing would not have saved anything (output barely over the budget).
    if (result.stdout) process.stdout.write(result.stdout);
    if (result.stderr) process.stderr.write(result.stderr);
    return exitCodeFor(result);
  }
  process.stdout.write(`${echo}\n${c.text}\n${status}\n`);
  return exitCodeFor(result);
}

/**
 * The agent already knows the command it issued; echoing all of it (chained
 * commands run to 400+ chars) was pure duplication inside the context window.
 * Keep enough to orient, not the whole thing.
 */
const ECHO_CAP = 80;
function shortCommand(command: string): string {
  const one = command.replace(/\s+/g, " ").trim();
  return one.length > ECHO_CAP ? `${one.slice(0, ECHO_CAP)}…` : one;
}

main().then(
  (code) => process.exit(code),
  (error) => {
    process.stderr.write(`[smart-bash] fatal: ${error instanceof Error ? error.message : String(error)}\n`);
    process.exit(1);
  },
);
