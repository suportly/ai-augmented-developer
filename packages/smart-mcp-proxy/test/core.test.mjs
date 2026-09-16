// T001 / T005 — core helpers. Runs against the compiled dist/ (npm test builds first).
// Ollama is pointed at a closed port so `condense` exercises the fallback path deterministically.
process.env.OLLAMA_URL = "http://127.0.0.1:9";
process.env.OLLAMA_TIMEOUT_MS = "500";
process.env.SMART_MCP_MAX_CHARS = "200";

import { test } from "node:test";
import assert from "node:assert/strict";

const core = await import("../dist/core.js");

test("headTail keeps head and tail within budget", () => {
  const text = "A".repeat(500) + "B".repeat(500);
  const out = core.headTail(text, 200);
  assert.ok(out.startsWith("AAAAA"));
  assert.ok(out.endsWith("BBBBB"));
  assert.match(out, /\[\.\.\. \d+ characters omitted \.\.\.\]/);
  assert.equal(core.headTail("short", 200), "short");
});

test("normalizeOutput strips ANSI and collapses repeats", () => {
  const out = core.normalizeOutput("[32mok[0m\nsame\nsame\nsame\nend");
  assert.equal(out, "ok\nsame\n[previous line repeated 2 more time(s)]\nend");
});

test("cleanSummary drops fences and label line", () => {
  assert.equal(core.cleanSummary("```\nERRORS / RESULT block:\nKeyError: x\n```"), "KeyError: x");
});

test("errorSignatures counts, ranks and attaches nearest project frame", () => {
  const log = [
    "ERROR collecting tests/test_a.py",
    "tests/test_a.py:22: in <module>",
    "    from aiadev.commands.install import install_command",
    "E   ModuleNotFoundError: No module named 'aiadev'",
    "ERROR collecting tests/test_b.py",
    "tests/test_b.py:9: in <module>",
    "E   ModuleNotFoundError: No module named 'aiadev'",
  ].join("\n");
  const sig = core.errorSignatures(log);
  assert.match(sig, /ModuleNotFoundError: No module named 'aiadev'   \(x2\)/);
  assert.match(sig, /↳ at tests\/test_a\.py:22/);
  // Lines that already carry a path get no frame.
  assert.doesNotMatch(sig, /ERROR collecting tests\/test_a\.py\n\s+↳/);
});

test("errorSignatures recognizes Python frames and skips vendor paths", () => {
  const log = [
    "Traceback (most recent call last):",
    '  File "/usr/lib/python3.12/os.py", line 685, in __getitem__',
    '  File "/app/config/settings.py", line 87, in <module>',
    "KeyError: 'DJANGO_SECRET_KEY'",
  ].join("\n");
  const sig = core.errorSignatures(log);
  assert.match(sig, /KeyError: 'DJANGO_SECRET_KEY'\n\s+↳ at \/app\/config\/settings\.py:87/);
});

test("errorSignatures is empty for clean output", () => {
  assert.equal(core.errorSignatures("Compiled 3 files\nBuild succeeded"), "");
});

test("condense returns verbatim under the budget", async () => {
  const c = await core.condense("echo hi", "hi", "[exit code: 0]");
  assert.equal(c.mode, "verbatim");
  assert.equal(c.text, "hi");
});

test("condense falls back to excerpt + signatures when Ollama is unreachable", async () => {
  const output = "progress line\n".repeat(40) + "TypeError: boom\n    at f (src/x.ts:4:2)";
  const c = await core.condense("npm test", output, "[exit code: 1]");
  assert.equal(c.mode, "fallback");
  assert.match(c.text, /WARNING: summarization failed/);
  assert.match(c.text, /ERROR SIGNATURES/);
  assert.match(c.text, /TypeError: boom/);
  assert.ok(c.text.length < output.length);
});

test("condense records raw output in the cache when one is given", async () => {
  const cache = new core.RawCache(2);
  const output = "x\n".repeat(300);
  const c = await core.condense("cmd", output, "[exit code: 0]", cache);
  assert.ok(c.rawId);
  assert.equal(cache.get(c.rawId).output, output);
  // Eviction keeps the newest entries.
  await core.condense("cmd2", output, "s", cache);
  await core.condense("cmd3", output, "s", cache);
  assert.equal(cache.get(c.rawId), undefined);
});

test("splitDiffByFile names each block", () => {
  const diff = [
    "diff --git a/src/a.py b/src/a.py",
    "--- a/src/a.py",
    "+++ b/src/a.py",
    "@@ -1 +1 @@",
    "-x",
    "+y",
    "diff --git a/docs/b.md b/docs/b.md",
    "--- a/docs/b.md",
    "+++ b/docs/b.md",
    "@@ -1 +1 @@",
    "+z",
  ].join("\n");
  const files = core.splitDiffByFile(diff);
  assert.deepEqual(files.map((f) => f.file), ["src/a.py", "docs/b.md"]);
  assert.ok(files[1].text.startsWith("diff --git a/docs/b.md"));
});

test("summarizeDiff lists every file as skipped when the model is unreachable", async () => {
  const diff = "diff --git a/x b/x\n+++ b/x\n+1\ndiff --git a/y b/y\n+++ b/y\n+2";
  const s = await core.summarizeDiff(diff, " x | 1 +\n y | 1 +\n");
  assert.deepEqual(s.skipped, ["x", "y"]);
  assert.equal(s.bullets.length, 0);
  assert.match(s.warning, /unreachable|failed|timed out/);
  const rendered = core.renderDiffSummary("HEAD", s);
  assert.match(rendered, /NOT SUMMARIZED \(2/);
});

test("condense returns verbatim when the envelope would not be smaller than the output", async () => {
  // Output just above the budget: header + excerpt + signatures would exceed it.
  const output = Array.from({ length: 60 }, (_, i) => `line ${i} ${"x".repeat(30)}`).join("\n").slice(0, core.CONFIG.maxChars + 40);
  assert.ok(output.length > core.CONFIG.maxChars);
  const c = await core.condense("grep -n foo", output, "[exit code: 0]");
  assert.equal(c.mode, "verbatim");
  assert.equal(c.text, output);
});

test("condense counts the caller's overhead in the size guard", async () => {
  const output = Array.from({ length: 12 }, (_, i) => `row ${i} ${"y".repeat(30)}`).join("\n");
  assert.ok(output.length > core.CONFIG.maxChars);
  const without = await core.condense("cmd", output, "[exit code: 0]");
  const withOverhead = await core.condense("cmd", output, "[exit code: 0]", undefined, 500);
  assert.equal(without.mode, "fallback");
  assert.equal(withOverhead.mode, "verbatim");
});

test("SMART_MCP_MODE=deterministic condenses without the model and without a warning", async () => {
  process.env.SMART_MCP_MODE = "deterministic";
  try {
    const det = await import("../dist/core.js?deterministic");
    const output = Array.from({ length: 80 }, (_, i) => `line ${i}`).join("\n") + "\nRuntimeError: boom\n";
    const c = await det.condense("npm test", output, "[exit code: 1]");
    assert.equal(c.mode, "deterministic");
    assert.match(c.text, /condensed \(error lines verbatim, head\/tail excerpt\)/);
    assert.match(c.text, /ERROR SIGNATURES[\s\S]*RuntimeError: boom/);
    assert.match(c.text, /EXCERPT \(head\/tail, verbatim\)/);
    assert.doesNotMatch(c.text, /WARNING|failed/);
  } finally {
    delete process.env.SMART_MCP_MODE;
  }
});
