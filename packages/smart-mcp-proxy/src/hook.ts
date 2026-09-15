#!/usr/bin/env node
/**
 * smart-bash-hook — Claude Code PreToolUse hook for the Bash tool.
 *
 * Reads the hook payload on stdin and, for Bash calls, rewrites `command`
 * so it runs through `smart-bash`, which condenses long output before it
 * reaches the agent. Everything else passes untouched.
 *
 * Failure mode is "do nothing": any problem reading or parsing stdin ends
 * with exit 0 and no stdout, so a broken hook can never block the agent's
 * Bash tool. The hook never runs the command itself.
 *
 * Register in .claude/settings.json:
 *   { "hooks": { "PreToolUse": [ { "matcher": "Bash",
 *       "hooks": [ { "type": "command", "command": "smart-bash-hook", "timeout": 5 } ] } ] } }
 *
 * Environment:
 *   SMART_BASH_BIN   command used to invoke the CLI (default: node + this package's dist/cli.js)
 */

import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

interface HookInput {
  tool_name?: string;
  tool_input?: { command?: string; run_in_background?: boolean };
}

interface HookOutput {
  hookSpecificOutput: {
    hookEventName: "PreToolUse";
    updatedInput: { command: string };
  };
}

function defaultBin(): string {
  const here = dirname(fileURLToPath(import.meta.url));
  return `"${process.execPath}" "${join(here, "cli.js")}"`;
}

/** Pure decision: returns the rewritten command, or null to leave the call untouched. */
export function rewrite(input: HookInput, bin: string = process.env.SMART_BASH_BIN ?? defaultBin()): string | null {
  if (input.tool_name !== "Bash") return null;
  const command = input.tool_input?.command;
  if (typeof command !== "string" || command.trim() === "") return null;
  if (input.tool_input?.run_in_background) return null;
  // Idempotent: already routed through the CLI.
  if (/(^|[\s"'/])(smart-bash|cli\.js)(\s|"|$)/.test(command) && command.includes("--b64")) return null;
  const b64 = Buffer.from(command, "utf8").toString("base64");
  return `${bin} --b64 ${b64}`;
}

export function render(command: string): HookOutput {
  return { hookSpecificOutput: { hookEventName: "PreToolUse", updatedInput: { command } } };
}

async function readStdin(): Promise<string> {
  const chunks: Buffer[] = [];
  for await (const chunk of process.stdin) chunks.push(chunk as Buffer);
  return Buffer.concat(chunks).toString("utf8");
}

async function main(): Promise<void> {
  try {
    const raw = await readStdin();
    const input = JSON.parse(raw) as HookInput;
    const rewritten = rewrite(input);
    if (rewritten) process.stdout.write(JSON.stringify(render(rewritten)));
  } catch (error) {
    // Failure mode: leave the tool call untouched.
    process.stderr.write(`[smart-bash-hook] ignored: ${error instanceof Error ? error.message : String(error)}\n`);
  }
  process.exit(0);
}

// Only run when executed directly, so tests can import `rewrite` / `render`.
const invokedDirectly = process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1];
if (invokedDirectly) void main();
