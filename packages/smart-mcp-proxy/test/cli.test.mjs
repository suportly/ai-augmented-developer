// T002 — smart-bash CLI. Ollama is pointed at a closed port so long output
// takes the deterministic fallback path.
import { test } from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const cliJs = join(here, "..", "dist", "cli.js");
// Model path (Ollama unreachable → deterministic fallback with a warning) unless a test overrides the mode.
const env = { ...process.env, SMART_MCP_MODE: "model", OLLAMA_URL: "http://127.0.0.1:9", OLLAMA_TIMEOUT_MS: "500", SMART_MCP_MAX_CHARS: "200" };
const envDefault = { ...env }; delete envDefault.SMART_MCP_MODE;

function run(args, e = env) {
  return spawnSync(process.execPath, [cliJs, ...args], { encoding: "utf8", env: e });
}
const b64 = (s) => Buffer.from(s).toString("base64");

test("short output is byte-identical and the exit code is propagated", () => {
  const r = run(["--b64", b64("echo hi; echo err >&2; exit 3")]);
  assert.equal(r.status, 3);
  assert.equal(r.stdout, "hi\n");
  assert.equal(r.stderr, "err\n");
});

test("-c and -- forms work", () => {
  assert.equal(run(["-c", "echo one"]).stdout, "one\n");
  assert.equal(run(["--", "echo", "two"]).stdout, "two\n");
});

test("long output is condensed (fallback path), shows the original command, keeps exit code", () => {
  const cmd = "for i in $(seq 1 100); do echo \"line $i\"; done; echo 'RuntimeError: nope' >&2; exit 2";
  const r = run(["--b64", b64(cmd)]);
  assert.equal(r.status, 2);
  assert.ok(r.stdout.startsWith("[smart-bash] $ for i in"));
  assert.match(r.stdout, /WARNING: summarization failed/);
  assert.match(r.stdout, /ERROR SIGNATURES[\s\S]*RuntimeError: nope/);
  assert.match(r.stdout, /\[exit code: 2\]\n$/);
  assert.ok(r.stdout.length < 100 * 9 + 200);
});

test("usage error exits 64", () => {
  assert.equal(run([]).status, 64);
});

test("output just above the budget is printed verbatim, not wrapped", () => {
  // 230 chars > 200 budget, but any envelope would be larger than the raw output.
  const r = run(["--b64", b64("for i in $(seq 1 23); do echo \"line $i xx\"; done")]);
  assert.equal(r.status, 0);
  assert.ok(!r.stdout.includes("[smart-bash]"), r.stdout.slice(0, 120));
  assert.equal(r.stdout.split("\n").length, 24);
});

test("the command echo on the first line is truncated", () => {
  const long = "for i in $(seq 1 100); do echo \"line $i\"; done # " + "padding ".repeat(40);
  const r = run(["--b64", b64(long)]);
  const first = r.stdout.split("\n")[0];
  assert.ok(first.startsWith("[smart-bash] $ for i in"));
  assert.ok(first.length < 110, `first line is ${first.length} chars`);
  assert.ok(first.endsWith("…"));
});

test("the size guard counts the CLI's own echo and status lines", () => {
  // 447 chars: the condense() envelope alone (~330) is smaller than the output,
  // but with the echo + status lines the CLI would print more than it received.
  const r = run(["--b64", b64("for i in $(seq 1 38); do echo \"row $i xxxx\"; done")]);
  assert.equal(r.status, 0);
  assert.ok(!r.stdout.includes("[smart-bash]"), r.stdout.slice(0, 160));
  assert.equal(r.stdout.split("\n").length, 39);
});

test("default mode: long output is condensed deterministically, no model, no warning", () => {
  const cmd = "for i in $(seq 1 100); do echo \"line $i\"; done; echo 'RuntimeError: nope' >&2; exit 2";
  const r = run(["--b64", b64(cmd)], envDefault);
  assert.equal(r.status, 2);
  assert.match(r.stdout, /condensed \(error lines verbatim, head\/tail excerpt\)/);
  assert.match(r.stdout, /ERROR SIGNATURES[\s\S]*RuntimeError: nope/);
  assert.match(r.stdout, /EXCERPT \(head\/tail, verbatim\)/);
  assert.doesNotMatch(r.stdout, /WARNING|summarization failed/);
  assert.ok(r.stdout.length < 100 * 9 + 200);
});
