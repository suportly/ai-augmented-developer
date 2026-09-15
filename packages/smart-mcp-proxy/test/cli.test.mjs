// T002 — smart-bash CLI. Ollama is pointed at a closed port so long output
// takes the deterministic fallback path.
import { test } from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const cliJs = join(here, "..", "dist", "cli.js");
const env = { ...process.env, OLLAMA_URL: "http://127.0.0.1:9", OLLAMA_TIMEOUT_MS: "500", SMART_MCP_MAX_CHARS: "200" };

function run(args) {
  return spawnSync(process.execPath, [cliJs, ...args], { encoding: "utf8", env });
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
