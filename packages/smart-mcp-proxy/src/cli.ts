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
 * printed to stdout with the original command on the first line. The exit
 * code of the original command is always propagated.
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
  const c = await condense(command, output, statusLine(result));
  process.stdout.write(`[smart-bash] $ ${command}\n${c.text}\n${statusLine(result)}\n`);
  return exitCodeFor(result);
}

main().then(
  (code) => process.exit(code),
  (error) => {
    process.stderr.write(`[smart-bash] fatal: ${error instanceof Error ? error.message : String(error)}\n`);
    process.exit(1);
  },
);
