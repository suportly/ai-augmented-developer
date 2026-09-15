// T003 — PreToolUse hook contract. Pure functions are imported; the process
// entry is exercised end-to-end through stdin.
import { test } from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const hookJs = join(here, "..", "dist", "hook.js");
const { rewrite, isContentDump, render } = await import("../dist/hook.js");

function runHook(stdin, args = []) {
  return spawnSync(process.execPath, [hookJs, ...args], { input: stdin, encoding: "utf8" });
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

test("rewrite passes content dumps through untouched (cat/head/sed/jq chains)", () => {
  const bash = (command) => rewrite({ tool_name: "Bash", tool_input: { command } }, "smart-bash");
  assert.equal(bash("cat specs/0167-copilot-teaching-via-plays/tasks.md"), null);
  assert.equal(bash("cd MayCRMWeb && cat package.json; head -40 src/App.tsx | nl"), null);
  assert.equal(bash("FOO=1 sed -n '10,60p' plan.md"), null);
  assert.equal(bash("/bin/cat big.log"), null);
  // Anything that produces rather than dumps is still routed.
  assert.match(bash("cat a.log | grep -c ERROR"), /^smart-bash --b64 /);
  assert.match(bash("pytest -q"), /^smart-bash --b64 /);
  assert.match(bash("cd api && npm test"), /^smart-bash --b64 /);
});

test("SMART_BASH_PASSTHROUGH extends the pass-through list", () => {
  const prev = process.env.SMART_BASH_PASSTHROUGH;
  process.env.SMART_BASH_PASSTHROUGH = "rg, grep";
  try {
    assert.equal(rewrite({ tool_name: "Bash", tool_input: { command: "grep -rn teach src | head" } }, "smart-bash"), null);
    assert.equal(isContentDump("rg -n foo"), true);
    assert.equal(isContentDump("pytest"), false);
  } finally {
    if (prev === undefined) delete process.env.SMART_BASH_PASSTHROUGH; else process.env.SMART_BASH_PASSTHROUGH = prev;
  }
});

test("rewrite is idempotent", () => {
  const once = rewrite({ tool_name: "Bash", tool_input: { command: "npm test" } }, "smart-bash");
  assert.equal(rewrite({ tool_name: "Bash", tool_input: { command: once } }, "smart-bash"), null);
  const viaNode = rewrite({ tool_name: "Bash", tool_input: { command: "npm test" } }, '"/usr/bin/node" "/x/dist/cli.js"');
  assert.equal(rewrite({ tool_name: "Bash", tool_input: { command: viaNode } }, "smart-bash"), null);
});

test("render produces the PreToolUse updatedInput shape, without a permission decision by default", () => {
  assert.deepEqual(render("cmd"), {
    hookSpecificOutput: { hookEventName: "PreToolUse", updatedInput: { command: "cmd" } },
  });
});

test("render adds permissionDecision allow only when asked (Codex)", () => {
  assert.deepEqual(render("cmd", true), {
    hookSpecificOutput: { hookEventName: "PreToolUse", permissionDecision: "allow", updatedInput: { command: "cmd" } },
  });
});

test("process: --allow flag sets permissionDecision allow (Codex mode)", () => {
  const payload = JSON.stringify({ hook_event_name: "PreToolUse", tool_name: "Bash", tool_input: { command: "npm test" } });
  assert.equal(JSON.parse(runHook(payload).stdout).hookSpecificOutput.permissionDecision, undefined);
  assert.equal(JSON.parse(runHook(payload, ["--allow"]).stdout).hookSpecificOutput.permissionDecision, "allow");
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

test("process: runs when invoked through a symlink (npm global bin)", async () => {
  const { mkdtempSync, symlinkSync } = await import("node:fs");
  const { tmpdir } = await import("node:os");
  const dir = mkdtempSync(join(tmpdir(), "smart-bash-hook-"));
  const link = join(dir, "smart-bash-hook");
  symlinkSync(hookJs, link);
  const r = spawnSync(process.execPath, [link], {
    input: JSON.stringify({ tool_name: "Bash", tool_input: { command: "npm test" } }),
    encoding: "utf8",
  });
  assert.equal(r.status, 0);
  assert.match(r.stdout, /updatedInput/);
});

test("process: non-Bash tool exits 0 with no stdout", () => {
  const r = runHook(JSON.stringify({ tool_name: "Edit", tool_input: {} }));
  assert.equal(r.status, 0);
  assert.equal(r.stdout, "");
});
