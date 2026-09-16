// T001 / T005 — core helpers. Runs against the compiled dist/ (npm test builds first).
// No model is involved: condense() is pure text processing.
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

test("condense returns verbatim when the envelope would not be smaller than the output", async () => {
  // Output just above the budget: header + excerpt + signatures would exceed it.
  const output = Array.from({ length: 60 }, (_, i) => `line ${i} ${"x".repeat(30)}`).join("\n").slice(0, core.CONFIG.maxChars + 40);
  assert.ok(output.length > core.CONFIG.maxChars);
  const c = await core.condense("grep -n foo", output, "[exit code: 0]");
  assert.equal(c.mode, "verbatim");
  assert.equal(c.text, output);
});

test("condense returns ERROR SIGNATURES + verbatim EXCERPT, no rewriting", async () => {
  // Well above the 2000-char budget so the envelope is genuinely smaller.
  const output = Array.from({ length: 400 }, (_, i) => `line ${i} ${"x".repeat(20)}`).join("\n") + "\nRuntimeError: boom\n";
  const c = await core.condense("npm test", output, "[exit code: 1]");
  assert.equal(c.mode, "condensed");
  assert.ok(c.text.length < output.length);
  assert.match(c.text, /condensed \(error lines verbatim, head\/tail excerpt\)/);
  assert.match(c.text, /ERROR SIGNATURES[\s\S]*RuntimeError: boom/);
  assert.match(c.text, /EXCERPT \(head\/tail, verbatim\)/);
  // Every non-header line must come from the original output.
  const body = c.text.split("EXCERPT (head/tail, verbatim):\n")[1];
  for (const line of body.split("\n")) {
    if (line.trim() === "" || /characters omitted/.test(line)) continue;
    assert.ok(output.includes(line), `invented line: ${line}`);
  }
});

test("condense counts the caller's overhead in the size guard", async () => {
  const output = Array.from({ length: 12 }, (_, i) => `row ${i} ${"y".repeat(30)}`).join("\n");
  assert.ok(output.length > core.CONFIG.maxChars);
  const without = await core.condense("cmd", output, "[exit code: 0]");
  const withOverhead = await core.condense("cmd", output, "[exit code: 0]", undefined, 900);
  assert.equal(without.mode, "condensed");
  assert.equal(withOverhead.mode, "verbatim");
});
