// T003 — PreToolUse hook contract. Pure functions are imported; the process
// entry is exercised end-to-end through stdin.
import { test } from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const hookJs = join(here, "..", "dist", "hook.js");
const { rewrite, render } = await import("../dist/hook.js");

function runHook(stdin) {
  return spawnSync(process.execPath, [hookJs], { input: stdin, encoding: "utf8" });
}

test("rewrite routes a Bash command through the CLI with base64", () => {
  const out = rewrite({ tool_name: "Bash", tool_input: { command: "npm test" } }, "smart-bash");
  assert.equal(out, `smart-bash --b64 ${Buffer.from("npm test").toString("base64")}`);
});

test("rewrite leaves non-Bash tools, empty and background commands alone", () => {
  assert.equal(rewrite({ tool_name: "Read", tool_input: { command: "x" } }, "smart-bash"), null);
  assert.equal(rewrite({ tool_name: "Bash", tool_input: { command: "  " } }, "smart-bash"), null);
  assert.equal(rewrite({ tool_name: "Bash", tool_input: { command: "npm test", run_in_background: true } }, "smart-bash"), null);
});

test("rewrite is idempotent", () => {
  const once = rewrite({ tool_name: "Bash", tool_input: { command: "npm test" } }, "smart-bash");
  assert.equal(rewrite({ tool_name: "Bash", tool_input: { command: once } }, "smart-bash"), null);
  const viaNode = rewrite({ tool_name: "Bash", tool_input: { command: "npm test" } }, '"/usr/bin/node" "/x/dist/cli.js"');
  assert.equal(rewrite({ tool_name: "Bash", tool_input: { command: viaNode } }, "smart-bash"), null);
});

test("render produces the PreToolUse updatedInput shape", () => {
  assert.deepEqual(render("cmd"), {
    hookSpecificOutput: { hookEventName: "PreToolUse", updatedInput: { command: "cmd" } },
  });
});

test("process: Bash payload on stdin yields JSON with the rewritten command", () => {
  const r = runHook(JSON.stringify({ hook_event_name: "PreToolUse", tool_name: "Bash", tool_input: { command: "pytest -q" } }));
  assert.equal(r.status, 0);
  const out = JSON.parse(r.stdout);
  assert.equal(out.hookSpecificOutput.hookEventName, "PreToolUse");
  assert.match(out.hookSpecificOutput.updatedInput.command, /cli\.js" --b64 [A-Za-z0-9+/=]+$/);
});

test("process: invalid stdin exits 0 with no stdout (failure mode)", () => {
  const r = runHook("not json");
  assert.equal(r.status, 0);
  assert.equal(r.stdout, "");
  assert.match(r.stderr, /ignored/);
});

test("process: non-Bash tool exits 0 with no stdout", () => {
  const r = runHook(JSON.stringify({ tool_name: "Edit", tool_input: {} }));
  assert.equal(r.status, 0);
  assert.equal(r.stdout, "");
});
