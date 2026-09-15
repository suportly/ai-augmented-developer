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
 * Codex CLI (.codex/hooks.json) uses the same payload and matcher, but only
 * applies `updatedInput` when the hook also returns `permissionDecision:
 * "allow"`. Pass `--allow` there. Do NOT pass it under Claude Code unless
 * you intend to auto-approve every Bash call: "allow" skips the permission
 * prompt.
 *
 * Environment:
 *   SMART_BASH_BIN          command used to invoke the CLI (default: node + this package's dist/cli.js)
 *   SMART_BASH_PASSTHROUGH  extra commands (comma list) whose output is passed through untouched
 */

import { realpathSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

interface HookInput {
  tool_name?: string;
  tool_input?: { command?: string; run_in_background?: boolean };
}

interface HookOutput {
  hookSpecificOutput: {
    hookEventName: "PreToolUse";
    permissionDecision?: "allow";
    updatedInput: { command: string };
  };
}

function defaultBin(): string {
  const here = dirname(fileURLToPath(import.meta.url));
  return `"${process.execPath}" "${join(here, "cli.js")}"`;
}

/**
 * Commands whose output IS the content the agent asked for (file excerpts,
 * listings). Condensing those loses information instead of noise: seen live,
 * `cat specs/.../tasks.md` (22,707 chars) came back as 2,061 chars of invented
 * lines and the agent re-read the whole file with Read four seconds later; a
 * chain of `sed -n` excerpts from four files ending in a `grep` lost three of
 * the four excerpts and the agent Read all four files.
 *
 * Rule: split the command into pipelines (`;`, `&&`, `||`); each pipeline's
 * output is its last stage's, skipping piped-into limiters and dumps
 * (`| head -20`, `| cat`). If any pipeline ends in a DUMP command, or in
 * `git diff` / `git show` / `git blame`, the whole
 * output carries content the agent wants → pass through. If every pipeline
 * ends in a DUMP or NEUTRAL command (echo, ls, pwd…) → pass through too.
 * Otherwise (something builds, tests, greps…) → route through smart-bash.
 * Extend DUMP with SMART_BASH_PASSTHROUGH (comma list).
 */
const DUMP = new Set(["cat", "head", "tail", "less", "more", "bat", "sed", "nl", "jq"]);
const NEUTRAL = new Set(["cd", "echo", "printf", "ls", "pwd", "wc", "true", "cut", "sort", "uniq", "tr", "date"]);
/** Trailing pipeline stages that only limit or reshape what came before (`grep … | head -20`). */
const FILTER = new Set(["head", "tail", "cut", "sort", "uniq", "wc", "nl", "tr", "tee"]);

function dumpSet(): Set<string> {
  const extra = (process.env.SMART_BASH_PASSTHROUGH ?? "").split(",").map((w) => w.trim()).filter(Boolean);
  return extra.length ? new Set([...DUMP, ...extra]) : DUMP;
}

/** `git diff`, `git show`, `git blame`: the agent reads that content (its own change, a file at a revision). */
const GIT_DUMP = /^git\s+(?:--no-pager\s+)?(?:diff|show|blame)\b/;

function firstWord(stage: string): string {
  const words = stage.trim().split(/\s+/);
  while (words.length && /^[A-Za-z_][A-Za-z0-9_]*=/.test(words[0])) words.shift(); // env assignments
  return (words[0] ?? "").replace(/^.*\//, "");
}

function stripEnv(stage: string): string {
  return stage.trim().replace(/^(?:[A-Za-z_][A-Za-z0-9_]*=\S*\s+)*/, "");
}

/** Drop heredoc bodies (`<<'EOF' … EOF`): they are data, not shell segments. */
function stripHeredocs(command: string): string {
  return command.replace(/<<-?\s*(['"]?)(\w+)\1[^\n]*\n[\s\S]*?\n\s*\2[ \t]*(?=\n|$)/g, "<<HEREDOC");
}

/** True when the command's output is content the agent asked for rather than noise to condense. */
export function isContentDump(command: string): boolean {
  const dump = dumpSet();
  // Newlines separate commands too (once heredoc bodies are gone).
  const pipelines = stripHeredocs(command).split(/\s*(?:;|&&|\|\||\n)\s*/).map((p) => p.trim()).filter(Boolean);
  if (!pipelines.length) return false;
  const lastStages = pipelines.map((p) => {
    const stages = p.split(/\s*\|\s*/);
    const words = stages.map(firstWord);
    let i = words.length - 1;
    // `… | head -20`, `… | cat` (pager off), `… | sed s/x/y/`: a piped-into dump or
    // filter only reshapes what feeds it, so classify by the stage before it.
    while (i > 0 && (FILTER.has(words[i]) || dump.has(words[i]))) i--;
    return GIT_DUMP.test(stripEnv(stages[i] ?? "")) ? "git-dump" : (words[i] ?? "");
  });
  if (lastStages.some((w) => w === "git-dump" || dump.has(w))) return true;
  return lastStages.every((w) => NEUTRAL.has(w));
}

/** Pure decision: returns the rewritten command, or null to leave the call untouched. */
export function rewrite(input: HookInput, bin: string = process.env.SMART_BASH_BIN ?? defaultBin()): string | null {
  if (input.tool_name !== "Bash") return null;
  const command = input.tool_input?.command;
  if (typeof command !== "string" || command.trim() === "") return null;
  if (input.tool_input?.run_in_background) return null;
  if (isContentDump(command)) return null;
  // Idempotent: already routed through the CLI.
  if (/(^|[\s"'/])(smart-bash|cli\.js)(\s|"|$)/.test(command) && command.includes("--b64")) return null;
  const b64 = Buffer.from(command, "utf8").toString("base64");
  return `${bin} --b64 ${b64}`;
}

/**
 * @param allow  also return `permissionDecision: "allow"` (required by Codex CLI
 *               for a rewrite to apply; under Claude Code it auto-approves the call).
 */
export function render(command: string, allow = false): HookOutput {
  return {
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      ...(allow ? { permissionDecision: "allow" as const } : {}),
      updatedInput: { command },
    },
  };
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
    const allow = process.argv.includes("--allow");
    if (rewritten) process.stdout.write(JSON.stringify(render(rewritten, allow)));
  } catch (error) {
    // Failure mode: leave the tool call untouched.
    process.stderr.write(`[smart-bash-hook] ignored: ${error instanceof Error ? error.message : String(error)}\n`);
  }
  process.exit(0);
}

// Only run when executed directly, so tests can import `rewrite` / `render`.
// Compare real paths: npm bin entries are symlinks, so argv[1] and this
// module's URL differ textually under a global install.
function invokedDirectly(): boolean {
  const entry = process.argv[1];
  if (!entry) return false;
  try {
    return realpathSync(entry) === realpathSync(fileURLToPath(import.meta.url));
  } catch {
    return false;
  }
}
if (invokedDirectly()) void main();
