# Implementation plan: Token economy & terse-mode (caveman-inspired)

> Produced by the `plan` skill from an approved `spec.md`. This file describes **how** the spec will be realized. Do not rewrite `spec.md` into `plan.md`.

**Branch:** `feature/token-economy-terse-mode`
**Date:** 2026-04-20
**Spec:** [spec.md](./spec.md)
**Plan version:** 2 <!-- v2: closes analysis.md gaps A/B/C/D/E/F (2026-04-20). -->

**Language:** en

---

## Summary

We will add an opt-in **terse-mode** to the three reviewer subagents (`spec-document-reviewer`, `plan-document-reviewer`, `code-reviewer`), wire a single project switch (`aiadev.terseMode` in `.claude/settings.json` with an `AIADEV_TERSE` env override), publish a drift-checked `/aia:help` quick-reference, and land a pinned Sonnet 4.6 benchmark fixture that proves ≥ 30 % output-token savings on reviewer turns. Work lands in `agents/`, `skills/`, `schemas/`, `scripts/`, `presets/*/`, plus the new benchmark directory under the current spec. Credit to `juliusbrussee/caveman` is added to `CREDITS.md`. Implementer subagents, non-Claude handlers, and commit-message compression are explicitly out of v1.

## Changes in plan v2 (2026-04-20)

Derived from `analysis.md`. Each item names the gap it closes.

- **Gap A · Help predecessor/successor links.** Phase 3 generator now reads each skill's `handoffs:` frontmatter and emits `→ <next>` per row.
- **Gap B · Tokenizer choice.** Technical-context row pins `anthropic.messages.count_tokens` for the help-budget drift check (cheap, non-inference). Benchmark delta continues to use live `usage.output_tokens`.
- **Gap C · Echo-mechanism reach.** Authoritative echo instruction lives **only** in `.claude/rules/terse-mode.md` (covers every `/aia:*` slash-command invocation via rule loading). `cli.py` intentionally has **no** echo — it exposes `validate/init/install/lang/sync/doctor/extension`, none of which are pipeline skills, so a shell-path mirror would be YAGNI (Article III). The "echo-consistency" test downgrades to a rule-file static check: asserts the rule contains the literal echo template and the three source labels.
- **Gap D · Dropped `terse_output_contract` frontmatter flag.** Resolved by documenting the scope reduction here: the contract lives in `agents/` + `schemas/terse-output.schema.json` only. Skill frontmatter is untouched. Spec's data-touched bullet accepted "names subject to plan"; this tightens it.
- **Gap E · CI secret for the benchmark.** Benchmark live runs (`AIADEV_RUN_BENCH=1`) execute only on `push` to `main` via a GitHub Actions workflow secret `ANTHROPIC_API_KEY_BENCHMARK` (scoped to the benchmark job). PRs — including PRs from forks — validate against the committed `benchmark/recorded/` golden files and never re-record. Operational note added to `benchmark/README.md`.
- **Gap F · Regression of existing validators.** New test `tests/test_existing_validators_regress.py` runs `scripts/validate_skills.py` with `AIADEV_TERSE=0` and then `AIADEV_TERSE=1`; both must exit 0. Paste both outputs in the PR per Article IV.

## Technical context

| Field | Value |
|---|---|
| Active preset | Framework-level (no consumer preset) — touches `skills/`, `agents/`, `schemas/`, `scripts/`, `presets/*/` indirectly via `aiadev sync`. |
| Language / runtime | Python 3.11+ for validators and benchmark runner; Markdown + YAML frontmatter for agents/skills. |
| Primary dependencies | `jsonschema` (already vendored) and the `anthropic` Python SDK. Two distinct token-count sources: (a) **benchmark delta** (Phase 4) uses the response's `usage.output_tokens` from live Sonnet 4.6 calls; (b) **help-budget drift check** (Phase 3) uses `anthropic.Anthropic().messages.count_tokens(model="claude-sonnet-4-6", messages=[…])`, which is a cheap non-inference endpoint. Both route through `benchmark/provider.py`; no `tiktoken` dependency. |
| Storage | File-system only. Benchmark artifacts (inputs + recorded outputs + token counts) checked into `specs/0009-token-economy-terse-mode/benchmark/`. |
| Testing framework | `pytest` for validators and drift checks; Markdown golden-file comparison for reviewer outputs. |
| Target platform(s) | Claude Code (v1). Non-Claude handlers deferred per spec `cl-6`. |
| Performance budget | Terse-mode reviewer responses: ≥ 30 % fewer output tokens than off-mode on the benchmark fixture (Sonnet 4.6). `/aia:help` (terse): ≤ 24 lines **and** ≤ 600 output tokens. |
| Security considerations | None beyond baseline. No new network egress, no new secrets, no new logs. Benchmark runs read the pinned Anthropic API via the existing provider pattern (Article V). |

## Constitution check

| Article | Applies? | Status | Evidence |
|---|---|---|---|
| I. Spec-first | Yes | PASS | `specs/0009-token-economy-terse-mode/spec.md` approved; zero `[NEEDS CLARIFICATION]` markers (grep clean on 2026-04-20). |
| II. Test-first | Yes | PASS | Every phase-task in `tasks.md` will begin with a failing test (terse-schema validator test, drift-check test, benchmark delta test, settings-resolution test). See `tasks` skill output. |
| III. Simplicity | Yes | PASS | One new config key (`aiadev.terseMode`) + one env var. No new config file. No new abstraction layer; reviewer agents opt into a shared terse-output contract stored in one place (`schemas/terse-output.schema.json`). No second provider added. |
| IV. Evidence over claims | Yes | PASS | Success = pinned benchmark fixture with recorded input prompts, output transcripts, and Anthropic-reported `usage.output_tokens`. PR test plan will paste the delta table. |
| V. Provider pattern | Yes | PASS | The framework has no prior LLM provider interface (it ships Markdown + packaging/CLI code only). Phase 4 **introduces** `specs/0009-token-economy-terse-mode/benchmark/provider.py` as a thin provider with a `complete(prompt, model) -> Completion` method. `benchmark/run_benchmark.py` depends on the interface, not on `anthropic.Anthropic()` directly. `tests/test_terse_output_schema.py` uses a `FakeProvider` returning canned transcripts; no network in unit tests. |
| VI. Privacy by design | Yes | N/A | No user data, no PII, no secrets in benchmark fixtures. The benchmark inputs are synthetic specs/plans with fake email `user@example.com`. |
| VII. Attribution | Yes | PASS | `CREDITS.md` gains a "Direct inspirations → juliusbrussee/caveman" entry naming the adapted concept (terse output contract for reviewer findings) and the repo URL + license snapshot. |
| Preset-specific articles | N/A | — | No preset-specific articles applied (framework-level change). |

No `FAIL` rows → `Complexity tracking` table below stays empty.

## Architecture decisions

- **Decision.** Terse-mode is an **output contract** expressed as a JSON schema (`schemas/terse-output.schema.json`) plus a short "When terse-mode is on, …" block appended to each reviewer agent definition.
  **Rationale.** Reviewers already produce semi-structured findings; codifying the contract in one schema lets the validator enforce it and keeps the three agent files symmetric. No runtime framework code is needed — the agent prompt carries the instruction, and the validator is a pytest check run in CI on the benchmark outputs.
  **Trade-offs.** We cannot *force* the model to obey at inference time; we detect violation after-the-fact. Acceptable because the benchmark fixture fails loudly in CI and the contract is simple (one line per finding, severity + location prefix).

- **Decision.** Switch lives in `.claude/settings.json` as `"aiadev.terseMode": boolean` (default `false`), with `AIADEV_TERSE` env var as a per-invocation override (env wins). A tiny helper `aiadev.config.resolve_terse_mode()` reads both and returns `(value, source)` so the hand-off message can echo "terse-mode: on (env)".
  **Rationale.** Aligns with the existing `update-config` skill; no new config file; env var satisfies spec Story 3 Scenario 3 without needing CLI arg parsing for `/aia:*` commands.
  **Trade-offs.** Settings-based toggles are per-project rather than per-run; env override mitigates that. An alternative — a dedicated `aiadev.toml` — was rejected to avoid a second source of truth.

- **Decision.** The `/aia:help` artifact is a **generated** Markdown file (`docs/pipeline-reference.md`) plus a thin `skills/help/SKILL.md` that reads and returns it. A pytest check in `scripts/validate_skills.py` (new function `check_help_matches_claude_md`) asserts the generated file lists the same pipeline skills as root `CLAUDE.md`.
  **Rationale.** Single source of truth lives in the skill catalog; generation keeps drift impossible to introduce silently. Terse-mode budget (≤ 24 lines, ≤ 600 tokens) is enforced by the same check.
  **Trade-offs.** One more generator to maintain. Acceptable because the alternative — manual maintenance of a second list — is precisely what caused the problem the spec calls out.

- **Decision.** The benchmark is a **synthetic 3-task micro-feature** under `specs/0009-token-economy-terse-mode/benchmark/` with pre-recorded model outputs committed to git. CI replays the prompts against pinned Sonnet 4.6, compares `usage.output_tokens`, and fails if the terse-mode run is not ≥ 30 % cheaper than the off-mode run on the same inputs.
  **Rationale.** Reproducible, cheap, attributable to a pinned model. Avoids measuring tokenizer approximations.
  **Trade-offs.** When Anthropic deprecates Sonnet 4.6, the benchmark must be re-pinned; that is a separate follow-up spec, not a hidden maintenance cost because the model id is a single constant in `benchmark/model.py`.

- **Decision.** No changes to implementer subagents, no commit-message compression, no non-Claude handler support. These are listed in spec Non-goals and the plan honours them.

## Project structure changes

```text
specs/0009-token-economy-terse-mode/plan.md                          (new — this file)
specs/0009-token-economy-terse-mode/benchmark/README.md              (new — documents the live-run gate (AIADEV_RUN_BENCH=1), the ANTHROPIC_API_KEY_BENCHMARK CI secret, and the "forks validate against golden files; only main re-records" policy)
.github/workflows/benchmark.yml                                      (new — push-to-main-only job that re-records on_/off_ transcripts using ANTHROPIC_API_KEY_BENCHMARK; PRs and forks skip this workflow)
specs/0009-token-economy-terse-mode/benchmark/model.py               (new — pins claude-sonnet-4-6)
specs/0009-token-economy-terse-mode/benchmark/inputs/spec_sample.md  (new)
specs/0009-token-economy-terse-mode/benchmark/inputs/plan_sample.md  (new)
specs/0009-token-economy-terse-mode/benchmark/inputs/diff_sample.md  (new)
specs/0009-token-economy-terse-mode/benchmark/recorded/off/*.json    (new — recorded transcripts)
specs/0009-token-economy-terse-mode/benchmark/recorded/on/*.json     (new — recorded transcripts)
specs/0009-token-economy-terse-mode/benchmark/provider.py            (new — LLM provider interface for Article V)
specs/0009-token-economy-terse-mode/benchmark/run_benchmark.py       (new — regenerates recorded/)
schemas/terse-output.schema.json                                     (new)
scripts/validate_skills.py                                           (modified — add check_help_matches_claude_md + terse-output validator + benchmark-delta check)
scripts/generate_pipeline_reference.py                               (new — emits docs/pipeline-reference.md from skill catalog)
docs/pipeline-reference.md                                           (new — generated + checked in; regenerated by a pre-commit hook and re-asserted in CI)
.pre-commit-config.yaml                                              (modified — add hook that runs scripts/generate_pipeline_reference.py)
skills/help/SKILL.md                                                 (new)
agents/spec-document-reviewer.md                                     (modified — append terse-mode block)
agents/plan-document-reviewer.md                                     (modified — append terse-mode block)
agents/code-reviewer.md                                              (modified — append terse-mode block)
src/aiadev/config.py                                                 (new — hosts resolve_terse_mode(); no prior config module exists)
<!-- removed: src/aiadev/cli.py shell-path echo — YAGNI, cli.py has no pipeline subcommands -->
rules/terse-mode.md                                                  (new — framework-root copy that aiadev sync ships to consumer projects via framework_artifacts.iter_framework_artifacts)
tests/test_terse_mode_config.py                                      (new)
tests/test_terse_output_schema.py                                    (new)
tests/test_pipeline_reference_drift.py                               (new)
tests/test_off_mode_unchanged.py                                     (new — golden-file check that off-mode reviewer output is byte-for-byte unchanged)
<!-- removed: test_terse_mode_echo_consistency.py — consistency check folded into test_terse_mode_rule.py -->
tests/test_existing_validators_regress.py                            (new — runs scripts/validate_skills.py with AIADEV_TERSE=0 and AIADEV_TERSE=1; both must exit 0 — closes spec success criterion 5)
tests/test_benchmark_delta.py                                        (new — asserts recorded on/off token delta ≥ 30 %; live run gated by AIADEV_RUN_BENCH=1)
CREDITS.md                                                           (modified — caveman attribution)
CLAUDE.md                                                            (modified — one-line "Quick reference: run /aia:help" inserted under the "What lives where" heading)
.claude/rules/terse-mode.md                                          (new — documents the switch (settings key + env var) and the hand-off line template; loaded by consumer projects via aiadev sync)
CHANGELOG.md                                                         (modified — [Unreleased] entry)
src/aiadev/_assets/rules/terse-mode.md                               (new — mirror of .claude/rules/terse-mode.md that aiadev sync ships to consumer projects)
```

## Phase breakdown

> Each phase is a checkpoint. Within a phase, tasks are independent enough that order does not matter — across phases, order does matter.

### Phase 1 — Contract & switch

Foundational pieces that every later phase depends on. Nothing user-visible yet.

- Terse-output JSON schema (`schemas/terse-output.schema.json`) with unit tests for valid / invalid samples.
- Config resolver `resolve_terse_mode()` in `src/aiadev/config.py`, plus tests covering: default off, settings-on, env-on, env-off-over-settings-on, invalid values.
- Attribution entry in `CREDITS.md` (front-loaded because Article VII blocks merge otherwise).

### Phase 2 — Reviewer opt-in

Apply the contract to the three reviewer agents and verify via schema.

- Append the terse-mode block to `agents/spec-document-reviewer.md`, `agents/plan-document-reviewer.md`, `agents/code-reviewer.md`. One-line-per-finding format with severity + location prefix.
- Schema validator test (`tests/test_terse_output_schema.py`) runs a table of sample reviewer outputs and asserts pass/fail correctly, including the "accidentally multi-paragraph" case required by Story 1 Scenario 3.
- Golden-file test `tests/test_off_mode_unchanged.py` replays a recorded off-mode reviewer transcript and asserts byte-for-byte equality against the committed golden file — protects Story 3 Scenario 1 (default behaviour preserved).

### Phase 3 — Help artifact & drift check

- Generator `scripts/generate_pipeline_reference.py` walks `skills/` + `presets/*/skills/`, reads each skill's YAML frontmatter (`name`, `description`, `handoffs`), and emits `docs/pipeline-reference.md` in the terse format **including a `→ <next-skill>` link per row** — directly fulfilling spec Story 2 Scenario 1's "predecessor/successor step" requirement. Skills with multiple hand-offs render as `→ a | b`. The drift test asserts every pipeline skill frontmatter present in `CLAUDE.md` is represented with its hand-offs.
- A `.pre-commit-config.yaml` hook re-runs the generator on every commit touching `skills/**` or `CLAUDE.md`; CI re-runs it and fails if `git diff` is non-empty. Regeneration is never manual.
- `skills/help/SKILL.md` reads and returns the generated file.
- Drift test `tests/test_pipeline_reference_drift.py` asserts (a) the generated file matches the pipeline commands table in root `CLAUDE.md` and (b) stays within 24 lines / 600 tokens (Sonnet 4.6 count, computed via the benchmark provider's tokenizer helper).
- Insert exactly this line under the root `CLAUDE.md` "What lives where" section, immediately after the bullet list: `> **Quick reference:** run \`/aia:help\` for a one-screen summary of the pipeline commands.`

### Phase 4 — Benchmark

- Synthetic inputs under `benchmark/inputs/` covering the three reviewer agents.
- `benchmark/run_benchmark.py` runs each input twice (off, on) against pinned Sonnet 4.6 via the existing provider interface, records transcripts + `usage.output_tokens` into `benchmark/recorded/{off,on}/*.json`.
- `tests/test_benchmark_delta.py` reads recorded files and asserts ≥ 30 % output-token reduction. Gated by `AIADEV_RUN_BENCH=1` so the live run is opt-in; the assertion on **recorded** numbers runs unconditionally in CI.

### Phase 5 — Integration, docs & changelog

- **Single echo surface.** `/aia:<name>` slash commands are routed via `.claude/commands/aiadev/*.md` and never reach `cli.py`, so the rule-loading path is the only place the echo can live without duplication.
  - **Authoritative instruction** lives in `.claude/rules/terse-mode.md` (with mirrors at `rules/terse-mode.md` — the framework-root copy that `framework_artifacts.iter_framework_artifacts` ships via `aiadev sync` — and at `src/aiadev/_assets/rules/terse-mode.md` — the packaged asset). The rule states: *"Before your first substantive line of output, emit exactly one line: `terse-mode: <on|off> (<source>)` where `<source>` is one of `default`, `settings`, `env`. Read the project's `.claude/settings.json` key `aiadev.terseMode` and the environment variable `AIADEV_TERSE` (env wins)."* Every Claude Code session loads rules from `.claude/rules/`, so every `/aia:*` invocation sees it.
  - **No shell-path mirror in `cli.py`.** The binary's existing subcommands (`validate`, `init`, `install`, `lang`, `sync`, `doctor`, `extension`) are not pipeline skills; echoing from them would be YAGNI. Dropped from this plan and from tasks.
  - `tests/test_terse_mode_rule.py` doubles as the echo-consistency check: asserts the rule file contains the literal echo template and the three source labels, and that the three rule copies (`.claude/rules/`, `rules/`, `src/aiadev/_assets/rules/`) are byte-for-byte identical.
- Propagate assets to consumer projects: confirm `src/aiadev/framework_artifacts.py` (and/or `install_manifest.py`) already walks `skills/` and `.claude/rules/`; add `src/aiadev/_assets/rules/terse-mode.md` + `skills/help/SKILL.md` to whichever manifest actually drives `aiadev sync` (located by reading the module before the task starts). If the manifest is auto-generated, no code change is needed and the task is a verification-only step with evidence pasted into the PR.
- Add `CHANGELOG.md` [Unreleased] entry. Run full `python3 scripts/validate_skills.py`, `pytest`, and `npx markdownlint-cli2 '**/*.md'`; paste output in the PR to satisfy Article IV.

## Risks and mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Terse reviewer output loses actionable nuance (one-liner hides *which* constitution article failed). | Med | Med | Contract requires severity + location prefix **and** reserves a 60-char rationale slot per line; unit test covers "article name present" for constitution-check failures. |
| Drift between `CLAUDE.md` skill table and `docs/pipeline-reference.md`. | Med | Low | Generator is the only writer of the reference file; drift test runs in CI on every PR. |
| ≥ 30 % reduction not achievable on some reviewer. | Low | High | Benchmark runs per-reviewer and in aggregate; if a single reviewer falls short, we adjust that agent's terse block (not the contract) and re-record. Fallback: renegotiate the success threshold in spec `cl-4` before merge, not during code review. |
| Sonnet 4.6 deprecation invalidates benchmark. | Low | Med | Model id isolated to `benchmark/model.py` constant; re-pin is a one-line change + re-record. Documented in benchmark README. |
| Env var override surprises (a CI job forgetting `AIADEV_TERSE=0` alters reviewer output). | Med | Low | Hand-off message always echoes resolved state + source; CI logs are searchable for "terse-mode:". |
| Rule file drifts between its three copies (`rules/`, `.claude/rules/`, `_assets/rules/`). | Low | Med | `tests/test_terse_mode_rule.py` asserts SHA-256 parity across all three copies; T017 instructs authoring from a single canonical source. |
| `ANTHROPIC_API_KEY_BENCHMARK` missing or expired in CI main-job. | Low | Med | Benchmark job fails loud; recorded golden files in the repo are the fallback evidence. PRs do not depend on the key. |
| Attribution delayed to the end and forgotten. | Low | High (Article VII is non-waivable) | `CREDITS.md` entry is a Phase 1 task, not Phase 5. |

## Complexity tracking

> Required when any Constitution Check row is `FAIL`. Empty table if no waivers.

| Article waived | Reason | Alternatives considered | Reviewer |
|---|---|---|---|
| (none) | | | |

## Hand-off to `tasks`

The next skill is `tasks`. It consumes this plan and produces `tasks.md`.
Pre-conditions before hand-off:

- [x] Constitution Check is fully populated, no blank rows.
- [x] Complexity tracking is filled or empty-and-justified.
- [x] Project structure delta is accurate.
