# Tasks: Token economy & terse-mode (caveman-inspired)

> Produced by the `tasks` skill from an approved `plan.md` (v2). Consumed by `implement`.

**Branch:** `feature/token-economy-terse-mode`
**Plan:** [plan.md](./plan.md)
**Generated:** 2026-04-20
**Language:** en

---

## How to read this file

- Tasks are ordered. `implement` runs them top-to-bottom unless a parallel group applies.
- One task = one commit. Commit subject starts with the task id (`feat(<area>): T00N <title>`).
- Each task links back to the spec acceptance scenarios it exercises.
- `Status` is one of: `pending`, `in_progress`, `blocked`, `done`. Only `implement` mutates it.

---

## Task list

### T001 — Credit juliusbrussee/caveman in CREDITS.md

- **Status:** done
- **Depends on:** —
- **Files:**
  - modify: `CREDITS.md`
  - test: `tests/test_credits_attribution.py` (new) — asserts the file contains a `juliusbrussee/caveman` entry with the repo URL and license snapshot.
- **Spec scenarios:** — (Article VII gate, front-loaded per plan v2 Phase 1)
- **Acceptance:**
  - [ ] Failing test written (grep-based): fails on current `CREDITS.md`.
  - [ ] Add a "Direct inspirations → juliusbrussee/caveman" block naming the adapted concept (terse output contract for reviewer findings), link, license snapshot.
  - [ ] No other existing test regresses.
  - [ ] Commit: `docs(credits): T001 attribute juliusbrussee/caveman`.

### T002 — Terse-output JSON schema

- **Status:** done
- **Depends on:** —
- **Files:**
  - create: `schemas/terse-output.schema.json`
  - test: `tests/test_terse_output_schema.py` — parameterised table: valid one-line findings, multi-paragraph finding (must fail), missing severity prefix (must fail), missing location prefix (must fail).
- **Spec scenarios:** Story 1 scenario 3 (violating output → validation fails loudly).
- **Acceptance:**
  - [ ] Failing tests written (no schema exists yet).
  - [ ] Author schema: object with `findings: [{ severity: "🔴|🟡|🟢", location: "<file>:<line>", message: "<≤ 140 chars single line>" }]`. `additionalProperties: false`. Message regex forbids `\n`.
  - [ ] All table rows pass/fail as expected.
  - [ ] Commit: `feat(schemas): T002 add terse-output schema`.

### T003 — `resolve_terse_mode()` helper in `src/aiadev/config.py`

- **Status:** done
- **Depends on:** —
- **Files:**
  - create: `src/aiadev/config.py`
  - test: `tests/test_terse_mode_config.py` — cases: (a) default off when neither settings nor env set; (b) settings on, env unset → `(True, "settings")`; (c) env on, settings off → `(True, "env")`; (d) env `0`, settings on → `(False, "env")`; (e) malformed settings → raises `ValueError`.
- **Spec scenarios:** Story 3 scenarios 1 and 3.
- **Acceptance:**
  - [ ] Failing tests written (module doesn't exist).
  - [ ] Implement `resolve_terse_mode(settings_path: Path | None = None) -> tuple[bool, Literal["default","settings","env"]]`. Env wins.
  - [ ] Commit: `feat(config): T003 add resolve_terse_mode() with env override`.

### T004 — Append terse-mode block to spec-document-reviewer

- **Status:** done
- **Depends on:** T002
- **Files:**
  - modify: `agents/spec-document-reviewer.md`
  - test: `tests/test_agents_have_terse_block.py` (new, grows through T005/T006) — asserts each reviewer md file contains a `## Terse-mode output contract` section referencing `schemas/terse-output.schema.json`.
- **Spec scenarios:** Story 1 scenario 2, Story 3 scenario 2.
- **Acceptance:**
  - [ ] Failing test for spec-reviewer file.
  - [ ] Append the block with one-line-per-finding rule, severity glyphs, location prefix, schema pointer.
  - [ ] Commit: `feat(agents): T004 add terse-mode block to spec reviewer`.

### T005 — Append terse-mode block to plan-document-reviewer

- **Status:** done
- **Depends on:** T004 <!-- serialized to avoid fighting over the shared parametrize table in test_agents_have_terse_block.py -->
- **Files:**
  - modify: `agents/plan-document-reviewer.md`
  - modify: `tests/test_agents_have_terse_block.py` — append a new parametrize row: `("agents/plan-document-reviewer.md",)`.
- **Spec scenarios:** Story 1 scenarios 1, 2; Story 3 scenario 2.
- **Acceptance:**
  - [ ] Failing test row for plan-reviewer.
  - [ ] Append block identical in structure to T004's.
  - [ ] Commit: `feat(agents): T005 add terse-mode block to plan reviewer`.

### T006 — Append terse-mode block to code-reviewer

- **Status:** done
- **Depends on:** T005 <!-- serialized for the same reason as T005 -->
- **Files:**
  - modify: `agents/code-reviewer.md`
  - modify: `tests/test_agents_have_terse_block.py` — append `("agents/code-reviewer.md",)`.
- **Spec scenarios:** Story 1 scenario 2; Story 3 scenario 2.
- **Acceptance:**
  - [ ] Failing test row for code-reviewer.
  - [ ] Append block.
  - [ ] Commit: `feat(agents): T006 add terse-mode block to code reviewer`.

### T007 — Off-mode golden-file test

- **Status:** done <!-- Phase 4 deferred: fixtures are hand-crafted representatives today; the benchmark runner (T014) will overwrite them with live Sonnet 4.6 transcripts when Phase 4 lands, and the test keeps working. -->

- **Depends on:** T006
- **Files:**
  - create: `tests/test_off_mode_unchanged.py`
  - create: `tests/fixtures/off_mode/spec_reviewer_output.md`, `plan_reviewer_output.md`, `code_reviewer_output.md` — recorded transcripts captured from the three agents running off-mode on the synthetic benchmark inputs (T014); capture once locally before this task lands.
- **Spec scenarios:** Story 1 scenario 1; Story 3 scenario 1.
- **Acceptance:**
  - [ ] **RED step** (explicit, not auto-passing): before writing the fixtures, commit a deliberately-wrong fixture (e.g. `spec_reviewer_output.md` with a trailing `MUTATED\n`). Run the test → must fail with a clear byte-mismatch message naming the offending file. Record this red-run output in the task notes.
  - [ ] Replace the deliberately-wrong fixtures with the real recorded transcripts. Re-run the test → green.
  - [ ] **Mutation-proof check**: after green, append a space to one fixture in-memory (via monkeypatch) and re-assert — test must fail. This subtest lives inside `test_off_mode_unchanged.py` and catches future regressions of the comparison logic itself.
  - [ ] Commit: `test(reviewers): T007 pin off-mode reviewer output with mutation proof`.

### T008 — Pipeline reference generator with hand-off links

- **Status:** done
- **Depends on:** T002
- **Files:**
  - create: `scripts/generate_pipeline_reference.py`
  - create: `docs/pipeline-reference.md` (committed output)
  - test: `tests/test_generate_pipeline_reference.py` — fixture skill catalog → expected markdown (includes `→ <next>` rows and `→ a | b` for multi-handoff skills).
- **Spec scenarios:** Story 2 scenario 1.
- **Acceptance:**
  - [ ] Failing test comparing fixture-driven output.
  - [ ] Generator reads `skills/` + `presets/*/skills/` frontmatter (`name`, `description`, `handoffs`) and emits terse-format table with hand-off column.
  - [ ] `docs/pipeline-reference.md` committed.
  - [ ] Commit: `feat(docs): T008 generate pipeline reference with handoff links`.

### T009 — `skills/help/SKILL.md`

- **Status:** done
- **Depends on:** T008
- **Files:**
  - create: `skills/help/SKILL.md`
  - test: `tests/test_help_skill.py` — (1) frontmatter validates against `schemas/skill-frontmatter.schema.json`; (2) body contains the literal instruction string `Read \`docs/pipeline-reference.md\` and return its contents verbatim.`; (3) body contains the line `**Announce at start:**` (house style for all SKILL.md files).
- **Spec scenarios:** Story 2 scenario 1.
- **Acceptance:**
  - [ ] Failing test.
  - [ ] Write `skills/help/SKILL.md` as a prompt-style Markdown document (like every other SKILL.md; this is not executable code). Frontmatter: `name: help`, `description: Print the pipeline quick-reference.`, `inputs: []`, `outputs: [{type: text, description: "pipeline reference markdown"}]`, `handoffs: []`. Body announces, then a one-step Loop: *"Read `docs/pipeline-reference.md` and return its contents verbatim. Do not reformat, paraphrase, or add commentary."*
  - [ ] Commit: `feat(skills): T009 add help skill`.

### T010 — Help drift + budget test (uses `anthropic.messages.count_tokens`)

- **Status:** done <!-- token-budget assertion skipped (requires T013 provider); drift + line-budget + clean-regeneration checks live and enforced. -->

- **Depends on:** T008, T013
- **Files:**
  - create: `tests/test_pipeline_reference_drift.py`
  - modify: `pyproject.toml` — add `[tool.pytest.ini_options]\npythonpath = ["specs/0009-token-economy-terse-mode"]` so the test can `from benchmark.provider import count_tokens`.
- **Spec scenarios:** Story 2 scenarios 2, 3.
- **Acceptance:**
  - [ ] Failing test.
  - [ ] Assertion 1: the set of pipeline commands in the "What you're doing | Skill to invoke" table of root `CLAUDE.md` equals the set rendered in `docs/pipeline-reference.md`.
  - [ ] Assertion 2 (terse-mode budget): `docs/pipeline-reference.md` has ≤ 24 non-empty lines AND ≤ 600 tokens. Token count is obtained via the provider from T013; make it importable by adding this to `pyproject.toml`: `[tool.pytest.ini_options]\npythonpath = ["specs/0009-token-economy-terse-mode"]` — then the test imports `from benchmark.provider import count_tokens`. `count_tokens` results are cached in `.cache/terse-mode/reference.tokens.json` keyed by the file's SHA-256; cache miss requires `AIADEV_RUN_BENCH=1` (CI without the benchmark secret hits the committed cache).
  - [ ] Commit: `test(docs): T010 drift + budget check for pipeline reference`.

### T011 — Pre-commit hook + CI drift enforcement

- **Status:** done
- **Depends on:** T008
- **Files:**
  - create: `.pre-commit-config.yaml` (absent today — confirm via `ls` before starting; switch to "modify" if a prior task added it)
  - create: `.github/workflows/pipeline-reference-drift.yml`
  - test: `tests/test_precommit_config.py` — asserts the hook entry exists and runs on `skills/**` or `CLAUDE.md` changes.
- **Spec scenarios:** Story 2 scenario 2.
- **Acceptance:**
  - [ ] Failing test.
  - [ ] Hook: `repo: local`, id `pipeline-reference`, entry `python scripts/generate_pipeline_reference.py`, pass_filenames: false, stages: [commit].
  - [ ] CI workflow: runs the generator, fails if `git diff --exit-code docs/pipeline-reference.md` is non-zero.
  - [ ] Commit: `ci(docs): T011 enforce pipeline-reference drift`.

### T012 — Root `CLAUDE.md` quick-reference pointer

- **Status:** done
- **Depends on:** T009
- **Files:**
  - modify: `CLAUDE.md`
- **Spec scenarios:** Story 2 scenario 1.
- **Acceptance:**
  - [ ] Failing grep-based test (`tests/test_claude_md_pointer.py`) — asserts the exact line is present.
  - [ ] Insert, immediately after the bullet list under `## What lives where`: `> **Quick reference:** run \`/aia:help\` for a one-screen summary of the pipeline commands.`
  - [ ] Commit: `docs(root): T012 point to /aia:help`.

### T013 — Benchmark provider interface + FakeProvider

- **Status:** pending
- **Depends on:** —
- **Files:**
  - create: `specs/0009-token-economy-terse-mode/benchmark/__init__.py`
  - create: `specs/0009-token-economy-terse-mode/benchmark/provider.py`
  - create: `specs/0009-token-economy-terse-mode/benchmark/model.py` (pins `MODEL = "claude-sonnet-4-6"`)
  - test: `tests/test_benchmark_provider.py` — uses `FakeProvider`, verifies `complete()` and `count_tokens()` contract shapes.
- **Spec scenarios:** — (Article V gate for Phase 4)
- **Acceptance:**
  - [ ] Failing test.
  - [ ] Define `class Provider(Protocol)` with `complete(messages, model) -> Completion` and `count_tokens(messages, model) -> int`. Implement `AnthropicProvider` (imports `anthropic` inside class body only) and `FakeProvider` (returns canned transcripts / counts).
  - [ ] Commit: `feat(benchmark): T013 add provider interface and fake`.

### T014 — Benchmark inputs + `run_benchmark.py`

- **Status:** pending
- **Depends on:** T013, T004, T005, T006
- **Files:**
  - create: `specs/0009-token-economy-terse-mode/benchmark/inputs/spec_sample.md`, `plan_sample.md`, `diff_sample.md`
  - create: `specs/0009-token-economy-terse-mode/benchmark/run_benchmark.py`
  - create: `specs/0009-token-economy-terse-mode/benchmark/README.md` (documents `AIADEV_RUN_BENCH=1` gate, `ANTHROPIC_API_KEY_BENCHMARK` secret, fork policy)
  - test: `tests/test_run_benchmark.py` — runs the script with `FakeProvider`, asserts it writes `recorded/on/*.json` and `recorded/off/*.json` with `usage.output_tokens` field.
- **Spec scenarios:** Story 1 scenario 2 (benchmark produces evidence).
- **Acceptance:**
  - [ ] Failing test.
  - [ ] Three synthetic inputs sized to exercise each reviewer realistically.
  - [ ] `run_benchmark.py`: loads provider, iterates inputs × modes (off/on), records transcript + `usage.output_tokens` + sha of input to `benchmark/recorded/{on,off}/<input>.json`.
  - [ ] README documents the secret + fork policy.
  - [ ] Commit: `feat(benchmark): T014 add synthetic inputs and runner`.

### T015 — GitHub Actions benchmark workflow

- **Status:** pending
- **Depends on:** T014
- **Files:**
  - create: `.github/workflows/benchmark.yml`
  - test: `tests/test_benchmark_workflow.py` — YAML structural asserts: triggers on `push` to `main` only; job uses `ANTHROPIC_API_KEY_BENCHMARK`; skipped for PRs from forks.
- **Spec scenarios:** — (Gap E resolution)
- **Acceptance:**
  - [ ] Failing test.
  - [ ] Workflow: `on: push: branches: [main]`; job runs `AIADEV_RUN_BENCH=1 python specs/0009-token-economy-terse-mode/benchmark/run_benchmark.py`; opens auto-PR if `recorded/` diff exists (or fails loud — pick and document).
  - [ ] Commit: `ci(benchmark): T015 add push-to-main benchmark workflow`.

### T016 — Benchmark delta test (≥ 30 % token reduction)

- **Status:** pending
- **Depends on:** T014
- **Files:**
  - create: `tests/test_benchmark_delta.py`
  - create: `specs/0009-token-economy-terse-mode/benchmark/recorded/off/*.json` + `recorded/on/*.json`
- **Spec scenarios:** Story 1 scenario 2 (≥ 30 % token reduction).
- **Acceptance:**
  - [ ] **RED step** (explicit): commit *placeholder* recorded files first — three `off/*.json` files with `usage.output_tokens: 100` each, three `on/*.json` files with `usage.output_tokens: 100` each (ratio = 1.0, exceeds the 0.70 threshold). Run the test → must fail with "ratio 1.00 > 0.70". Record red output.
  - [ ] Locally, run `AIADEV_RUN_BENCH=1 python specs/0009-.../benchmark/run_benchmark.py` against pinned Sonnet 4.6 to overwrite the placeholders with real transcripts. Commit the real recorded files.
  - [ ] Re-run the test → green. Per-reviewer soft assertion (logs, does not fail) reports which reviewer carries the win.
  - [ ] Default CI run asserts against committed files only (no API key needed); live re-recording is gated by `AIADEV_RUN_BENCH=1` and only runs in the main-branch workflow from T015.
  - [ ] Commit (combined RED + GREEN as two commits on the same branch): `test(benchmark): T016 assert ≥30% output-token reduction`.

### T017 — Terse-mode rule (three synchronized copies)

- **Status:** done
- **Depends on:** T003
- **Files:**
  - create: `rules/terse-mode.md` — **framework-root copy** shipped by `aiadev sync` via `framework_artifacts.iter_framework_artifacts` (scans `rules/*.md` at repo root).
  - create: `.claude/rules/terse-mode.md` — local copy so the framework repo's own Claude Code sessions load the rule.
  - create: `src/aiadev/_assets/rules/terse-mode.md` — packaged asset used by `aiadev init` when bootstrapping consumer projects.
  - test: `tests/test_terse_mode_rule.py` — asserts (a) all **three** files exist, (b) their SHA-256 digests all match, (c) body contains the literal echo template `terse-mode: <on|off> (<source>)` and the three source labels (`default`, `settings`, `env`), (d) body mentions both `aiadev.terseMode` settings key and `AIADEV_TERSE` env var with "env wins" precedence.
- **Spec scenarios:** Story 3 scenarios 2, 3.
- **Acceptance:**
  - [ ] Failing test.
  - [ ] Write the rule once, then copy byte-for-byte to the two mirror paths. Consider adding a pre-commit hook (T011 extension) that re-copies from the canonical source; defer that refinement if not trivially landable.
  - [ ] Commit: `feat(rules): T017 add terse-mode rule with framework/local/packaged copies`.

<!-- T018 removed in tasks v2 (2026-04-20): cli.py has no pipeline subcommands;
     echoing from validate/init/install/sync/doctor/extension would be YAGNI.
     The rule-file path (T017) covers every /aia:* slash invocation via
     Claude Code rule loading. Plan.md Phase 5 updated to match.
     Task ids T019–T021 kept stable to preserve commit-message traceability. -->


### T019 — Propagate new rule + help skill via `aiadev sync`

- **Status:** done <!-- verification-only: framework_artifacts.iter_framework_artifacts auto-discovers rules/*.md and skills/*/SKILL.md; no manifest code change needed, test asserts the coverage. -->

- **Depends on:** T009, T017
- **Files:**
  - modify: `src/aiadev/framework_artifacts.py` **or** `src/aiadev/install_manifest.py` (whichever is the manifest driver — inspect before editing; if both are auto-generated from the file system, no code change and the task becomes verification-only)
  - test: `tests/test_sync_ships_terse_assets.py` — runs `aiadev sync` into a temp dir and asserts `.claude/rules/terse-mode.md` and `.claude/skills/help/SKILL.md` land in the target.
- **Spec scenarios:** Story 3 scenario 2 (switch must be reachable in consumer projects).
- **Acceptance:**
  - [ ] Failing test.
  - [ ] Inspect the manifest modules; add the two paths if explicit enumeration is needed; otherwise, paste in the PR the evidence that auto-discovery covers them.
  - [ ] Commit: `feat(sync): T019 ship terse-mode rule and help skill to consumer projects`.

### T020 — Existing-validators regression test

- **Status:** pending
- **Depends on:** T017
- **Files:**
  - create: `tests/test_existing_validators_regress.py`
- **Spec scenarios:** Success criterion 5 (no regression in existing validators).
- **Acceptance:**
  - [ ] Failing test.
  - [ ] Test invokes `python3 scripts/validate_skills.py` twice: once with `AIADEV_TERSE=0`, once with `AIADEV_TERSE=1`. Asserts exit code 0 for both. Captures both outputs for PR evidence.
  - [ ] Commit: `test(validators): T020 assert terse-mode does not regress existing checks`.

### T022 — Rename slash-command prefix `/aiadev:` → `/aia:` (breaking)

- **Status:** done <!-- added mid-implementation per user request; part of the terse-mode release -->
- **Depends on:** —
- **Files:**
  - modify: 5 platform handlers (`src/aiadev/platforms/{claude_code,codex,cursor,gemini,opencode}.py`) — change `"aiadev"` subdir segment to `"aia"`.
  - modify: `tests/test_install_command_and_agent_roles.py` — 5 parametrize rows.
  - modify: 13 Markdown / Python files carrying the 67 occurrences of `/aiadev:` prose (generator, CLAUDE.md, rules, help skill, docs, spec/plan/tasks, agents, articles, CHANGELOG). Bulk sed-equivalent.
  - rename (local, gitignored): `.claude/commands/aiadev/` → `.claude/commands/aia/`.
- **Spec scenarios:** — (framework-wide rename; improves terse-mode theme but is not itself an acceptance criterion).
- **Acceptance:**
  - [x] Every platform handler routes commands under `<platform>/commands/aia/`.
  - [x] Install tests still pass (489 passed, 1 skipped).
  - [x] Regenerated `docs/pipeline-reference.md` uses the new prefix and drift test passes.
  - [x] No `/aiadev:` remains in tracked code or docs (HTML markers like `aiadev:auto-stack` are internal — left untouched).
  - [x] Commit: `feat!: rename /aiadev: slash prefix to /aia:`.

### T021 — CHANGELOG entry + final gate

- **Status:** pending
- **Depends on:** T001–T020, T022
- **Files:**
  - modify: `CHANGELOG.md`
  - test: `tests/test_changelog_entry.py` — asserts `[Unreleased]` contains a line mentioning `terse-mode` and the `0009` spec id.
- **Spec scenarios:** — (final bookkeeping)
- **Acceptance:**
  - [ ] Failing test.
  - [ ] Add `[Unreleased] → Added` bullet: terse-mode reviewer contract, `/aia:help` pipeline reference, pinned Sonnet 4.6 benchmark. Link to spec 0009.
  - [ ] Run full gate: `pytest && python3 scripts/validate_skills.py && npx markdownlint-cli2 '**/*.md'`. Paste outputs in the PR.
  - [ ] Commit: `docs(changelog): T021 record 0009 terse-mode feature`.

---

## Parallelization hints

- **Parallel group A (independent foundations):** T001, T002, T003, T013. Touch disjoint files (`CREDITS.md`, `schemas/`, `src/aiadev/config.py`, `benchmark/provider.py` + `model.py`).
- **Serial elsewhere.** T004 → T005 → T006 are serialized on the shared `tests/test_agents_have_terse_block.py` parametrize table. T007 waits for T006. T010 waits for T008 + T013. T011/T012 wait for T008 (T012 also on T009). T014 waits for T013 + T006. T015 waits for T014. T016 waits for T014. T019 waits for T009 + T017. T020 waits for T017. T021 is last.

---

## Spec-scenario coverage (for grep-check)

| Scenario | Tasks |
|---|---|
| S1.1 (off-mode preserved) | T007 |
| S1.2 (terse on: one-line + ≥ 30 %) | T004, T005, T006, T014, T016 |
| S1.3 (violating output fails validation) | T002 |
| S2.1 (help lists commands + pred/succ) | T008, T009, T012 |
| S2.2 (CI fails on drift) | T010, T011 |
| S2.3 (help within 24 lines / 600 tokens) | T010 |
| S3.1 (off by default, byte-for-byte) | T003, T007 |
| S3.2 (switch on: reviewers + visible hand-off) | T004, T005, T006, T017, T019 |
| S3.3 (env override wins, source echoed) | T003, T017 |
| Success criterion 5 (no validator regression) | T020 |

Every acceptance scenario maps to ≥ 1 task. Article I Test 3 passes.

---

## Post-task checklist

After every task:

- [ ] Commit message references the task id.
- [ ] Status in this file updated by `implement`.

After all tasks:

- [ ] Full test suite passes: `pytest && python3 scripts/validate_skills.py && npx markdownlint-cli2 '**/*.md'`.
- [ ] `analyze` skill runs and reports no drift vs spec / plan.
- [ ] Hand off to `requesting-code-review` to open the PR.
