# Drift analysis — 0009-token-economy-terse-mode

> Produced by the `analyze` skill on 2026-04-20. Surfaces gaps; does not fix them.

**Scope.** `spec.md` ↔ `plan.md` only. `tasks.md` does not exist yet (pipeline is at `plan → tasks`). No code on branch — `git diff main...HEAD` is empty; the two spec artifacts are untracked. "Task without code" and "Code without task" classes are N/A at this point.

---

## 1. Spec → Plan coverage map

| # | Spec acceptance scenario | Plan coverage | Status |
|---|---|---|---|
| S1.1 | Terse off → current multi-paragraph format preserved | Phase 2 · `tests/test_off_mode_unchanged.py` golden-file check | ✅ covered |
| S1.2 | Terse on → one-line-per-issue + ≥ 30 % fewer tokens | Phase 2 · terse-mode block in 3 reviewer agents; Phase 4 · benchmark delta test | ✅ covered |
| S1.3 | Terse on + violating output → schema validation fails loudly | Phase 1 · `schemas/terse-output.schema.json`; Phase 2 · `tests/test_terse_output_schema.py` | ✅ covered |
| S2.1 | Help lists every `/aiadev:*` pipeline command + **predecessor / successor** step | Phase 3 · `generate_pipeline_reference.py` walks skill catalog | ⚠️ partial — see gap A |
| S2.2 | CI fails when help drifts from `CLAUDE.md` | Phase 3 · `tests/test_pipeline_reference_drift.py` + pre-commit hook + CI diff | ✅ covered |
| S2.3 | Terse on → help within 24 lines / 600 tokens; enforced on every change | Phase 3 · drift test dual assertion | ⚠️ partial — see gap B |
| S3.1 | No config → off by default; artifacts byte-for-byte unchanged | Phase 1 · `resolve_terse_mode()` default `false`; Phase 2 · `test_off_mode_unchanged.py` | ✅ covered |
| S3.2 | Switch on → in-scope reviewers adopt contract; switch state in hand-off | Phase 2 · terse blocks; Phase 5 · `cli.py` echoes resolved line | ⚠️ partial — see gap C |
| S3.3 | Per-invocation env override wins; hand-off explains resolved level | Phase 1 · `resolve_terse_mode()` returns `(value, source)` with env > settings; Phase 5 · hand-off echoes source | ✅ covered |

---

## 2. Gaps (spec → plan)

### A. Predecessor/successor links missing from generator contract

**Evidence.** `spec.md` Story 2 Scenario 1 requires the help output to list each command **"with its one-line purpose and the expected predecessor/successor step."** `plan.md` Phase 3 describes `generate_pipeline_reference.py` as walking `skills/` + `presets/*/skills/` and emitting the terse format, but does not commit to extracting predecessor/successor links from skill frontmatter `handoffs:` or the pipeline diagram in root `CLAUDE.md`.

**Impact.** If the generator ships without this, the drift test against `CLAUDE.md` may still pass (since the table in `CLAUDE.md` does not list hand-offs either) while silently missing an acceptance criterion.

**Suggested next skill.** `plan` — amend Phase 3 to state the generator reads each skill's `handoffs:` frontmatter key and emits `→ <next>` next to every command.

### B. Token-count mechanism for the help budget is unresolved

**Evidence.** Plan Technical-context row says token counts come from the Anthropic API's `usage.output_tokens` field (to avoid tokenizer drift). Plan Phase 3 says the drift test asserts the help artifact "stays within 24 lines / 600 tokens (Sonnet 4.6 count, computed via the benchmark provider's tokenizer helper)." These are incompatible: `usage.output_tokens` only exists after a live inference call; CI cannot make one per PR without an API key, and doing so on every drift test is wasteful.

**Impact.** Without a concrete offline tokenizer (or a recorded/cached count refreshed only by `benchmark/run_benchmark.py`), the drift test is not implementable as described — Phase 3 risks being blocked in implementation.

**Suggested next skill.** `plan` — pick one: (a) adopt `anthropic` SDK's client-side token counter (`client.messages.count_tokens`), (b) vendor a Sonnet 4.6 BPE table, (c) store a pinned token count per generated file and refresh only via the benchmark runner with the `AIADEV_RUN_BENCH=1` gate.

### C. Slash-command path vs `cli.py` echo mechanism

**Evidence.** Plan Phase 5 says `src/aiadev/cli.py` prints the `terse-mode: <on|off> (<source>)` line before each pipeline command's output. In Claude Code, `/aiadev:<name>` slash commands are routed through `.claude/commands/aiadev/<name>.md` (Markdown prompts), **not** through `cli.py`. `cli.py` is invoked when the user runs `aiadev <subcommand>` from a shell, which is a different entry point.

**Impact.** If the hand-off line is emitted only from `cli.py`, users invoking skills via `/aiadev:plan` inside Claude Code never see the "switch state visible" guarantee required by Story 3 Scenario 2.

**Suggested next skill.** `plan` — either (a) move the echo into each `.claude/commands/aiadev/<name>.md` template as a literal first-line instruction (rendered by the agent), or (b) add the echo instruction to the shared `.claude/rules/terse-mode.md` that every skill loads. Keeping the `cli.py` echo is still valuable for the shell path but is not sufficient on its own.

---

## 3. Secondary drifts (lower severity)

### D. Spec's `terse_output_contract` frontmatter flag not adopted by plan

**Evidence.** `spec.md` Data-touched bullet says "Skill frontmatter under `skills/` and `presets/*/skills/` — may gain a new `terse_output_contract` capability flag (names subject to plan)." Plan does not introduce any skill-frontmatter flag; the contract lives in agent prompts + one JSON schema.

**Impact.** This is a deliberate scope reduction (reviewers are agents, not skills) but it is unannounced. The drift is benign but the spec's data-touched bullet is now inaccurate.

**Suggested next skill.** `plan` — update plan's Data-touched comment, **or** prefer: update `spec.md` Data-touched to reflect the final decision (contract lives in `agents/` + `schemas/`, not skill frontmatter). The spec bullet explicitly said "names subject to plan," so tightening it is in-bounds.

### E. Article-IV evidence requires an Anthropic API key in CI

**Evidence.** `plan.md` Phase 4 runs the benchmark against pinned Sonnet 4.6; `tests/test_benchmark_delta.py` is gated by `AIADEV_RUN_BENCH=1`, but re-generating `recorded/` requires live calls. Neither `plan.md` nor `spec.md` names where the `ANTHROPIC_API_KEY` for CI comes from, or who pays for it.

**Impact.** Benchmark is reproducible locally but may not be reproducible by every contributor's PR CI — which means Article IV ("evidence is non-negotiable") hinges on a secret that is not yet provisioned.

**Suggested next skill.** `plan` — add a one-line operational note naming the secret, who manages it, and what happens when a PR from a fork cannot access it (typical pattern: benchmark runs on `push` to `main`, PRs compare against the committed `recorded/` without re-recording).

### F. Spec success criterion 5 is not re-asserted as a regression test

**Evidence.** `spec.md` success criterion 5: *"No regression in artifact schema validation: every existing `scripts/validate_skills.py` and schema check still passes with terse-mode on and off."* Plan modifies `validate_skills.py` (adds three new checks) but does not explicitly commit to running the pre-existing checks with terse-mode toggled.

**Impact.** Minor. The existing checks are stateless w.r.t. terse-mode, so the risk is theoretical. Still, the spec asks for the regression check and the plan is silent.

**Suggested next skill.** `tasks` — ensure one task in the final list explicitly runs `python3 scripts/validate_skills.py` with `AIADEV_TERSE=0` and then `AIADEV_TERSE=1`, and pastes both outputs in the PR.

---

## 4. Constitution re-check

| Article | Plan status | Still passing given current drift? |
|---|---|---|
| I · Spec-first | PASS | Yes — spec approved, 0 markers. |
| II · Test-first | PASS | Yes — every phase names a preceding failing test. |
| III · Simplicity | PASS | Yes, but **gap C** (slash-command path) risks a second echo mechanism; resolve before it becomes an abstraction. |
| IV · Evidence | PASS | At risk — **gap E** exposes a CI/secret dependency that could silently block evidence production. |
| V · Provider pattern | PASS | Yes — `benchmark/provider.py` introduced; `FakeProvider` used in unit tests. |
| VI · Privacy | N/A | Unchanged. |
| VII · Attribution | PASS (scheduled) | `CREDITS.md` entry is a Phase 1 task; still unwritten. Flag re-opens if that task is deferred. |

No silent `FAIL` slips.

---

## 5. Recommendation

Close gaps **A**, **B**, **C** (blocking — they affect acceptance criteria directly) with a `plan` iteration before running `tasks`. Gaps **D**, **E**, **F** can be absorbed during `tasks` or as small plan tweaks — they do not block task decomposition.

Suggested next skill: `plan` (amend Phase 3 for gap A, resolve gap B's tokenizer choice, widen gap C's echo mechanism). After that → `tasks`.
