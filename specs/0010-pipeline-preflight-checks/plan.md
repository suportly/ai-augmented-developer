# Implementation plan: Pipeline pre-flight checks

> Produced by the `plan` skill from an approved `spec.md`. This file describes **how** the spec will be realized. Do not rewrite `spec.md` into `plan.md`.

**Branch:** `feature/pipeline-preflight-checks`
**Date:** 2026-04-20
**Spec:** [spec.md](./spec.md)
**Plan version:** 2
**Language:** en

---

## Summary

Add a single `aiadev.preflight` module that, given a pipeline skill name and a feature slug, verifies required upstream artifacts exist, carry the required section anchors, share a consistent `Language:` header, and match the current git branch. Expose it as `aiadev preflight <skill> --feature <slug>` (and `aiadev preflight --all`) for CI, and as a first-line invocation from each pipeline skill's SKILL.md. The work lands in roughly twelve tasks: one checker module, one Click subcommand, one SKILL.md edit in `requesting-code-review` to emit `.aiadev/review.yaml`, one SKILL.md edit in `finishing-a-branch` to gate on it, preflight call-outs in five other pipeline skills, and three test files.

## Technical context

| Field | Value |
|---|---|
| Active preset | framework (no consumer preset) |
| Language / runtime | Python 3.11+ |
| Primary dependencies | click, pyyaml, jsonschema (all already pinned) |
| Storage | filesystem only (reads `specs/<slug>/…`, reads `.aiadev/review.yaml`) |
| Testing framework | pytest (flat layout under `tests/`) |
| Target platform(s) | Linux + macOS developer workstations, GitHub Actions CI |
| Performance budget | ≤ 500 ms wall-clock on reference feature dir (spec.md + plan.md + tasks.md + schemas/) |
| Security considerations | read-only checker; no shell-out; YAML parsed via `yaml.safe_load`; diagnostics echo only literal anchor names, slugs, and skill names |

## Constitution check

| Article | Applies? | Status | Evidence |
|---|---|---|---|
| I. Spec-first | Yes | PASS | `specs/0010-pipeline-preflight-checks/spec.md` approved 2026-04-20, zero `[NEEDS CLARIFICATION]` markers |
| II. Test-first | Yes | PENDING | asserted in tasks.md — every task row ships its failing pytest first; Phase 1 tasks below name the exact test files and functions that must be red before implementation lands |
| III. Simplicity | Yes | PASS | one module (`src/aiadev/preflight.py`), one CLI subcommand, no new abstractions beyond the existing Click / pyyaml stack; env var `AIADEV_PREFLIGHT=warn` has a named user (CI debug) |
| IV. Evidence over claims | Yes | PASS | PR test plan enumerates `pytest tests/test_preflight.py`, `pytest tests/test_preflight_pipeline.py`, `aiadev preflight plan --feature 0010-pipeline-preflight-checks`, and the 500 ms timing assertion in `test_preflight_pipeline.py::test_reference_dir_completes_under_500ms` |
| V. Provider pattern | No | N/A | no external network boundary introduced |
| VI. Privacy by design | Yes | PASS | diagnostics echo only anchor names, slugs, and skill names — never feature content; no new log lines |
| VII. Attribution | No | N/A | no material adapted from another project |

## Architecture decisions

- **Decision:** Single `aiadev.preflight.check(skill, feature_dir, *, env=os.environ, repo_root=Path.cwd())` function returns a list of `PreflightIssue` dataclasses; the CLI and the skill prose both call it.
  **Rationale:** Keeps the contract between in-skill invocation and CI identical (spec Success criterion #2). Avoids duplicating the rules in two places.
  **Trade-offs:** Adds one public symbol to `aiadev`; worth it for parity.

- **Decision:** Rules are a static table keyed by skill name (`REQUIREMENTS: dict[str, SkillRequirements]`), not derived from SKILL.md frontmatter `inputs:` templates.
  **Rationale:** Frontmatter inputs are template strings (`specs/<branch>/spec.md`), not machine-checkable rules. A static table is explicit and cheap to extend.
  **Trade-offs:** Frontmatter + table must stay in sync; `tests/test_preflight_requirements_coverage.py` asserts every pipeline skill under `skills/` has a row and every anchor in `REQUIREMENTS.spec_anchors` exists in `templates/spec-template.md` (and likewise for plan/tasks).

- **Decision:** Section-anchor validation uses literal per-artifact lists (`SPEC_ANCHORS`, `PLAN_ANCHORS`, `TASKS_ANCHORS`) rather than parsing the current template at run time.
  **Rationale:** Pre-flight must stay deterministic across framework versions checked into different consumer projects.
  **Trade-offs:** Template additions require a matching edit to `preflight.py`; caught by `test_preflight_requirements_coverage.py`.

- **Decision:** Review approval signal lives at the **repo root** `.aiadev/review.yaml` (matching the spec's Breaking-Changes wording verbatim). `requesting-code-review` writes it; `finishing-a-branch` reads it.
  **Rationale:** The spec's Breaking-Changes clause (line 47) and Clarification cl-3 (line 92) both use `.aiadev/review.yaml` without a `specs/<slug>/` prefix. Pre-flight honours the spec literally.
  **Trade-offs:** Only one feature at a time can hold an approved review; acceptable because branches are one-at-a-time in this repo's workflow (git-workflow rule).

- **Decision:** `AIADEV_PREFLIGHT=warn` downgrades only the abort, not the message format — the single-line diagnostic is byte-identical in `abort` and `warn` modes.
  **Rationale:** CI that tails stderr can switch modes without re-parsing.
  **Trade-offs:** None meaningful.

- **Decision:** `aiadev preflight --all` iterates `specs/*/` and runs the **last completed stage** check for each feature dir (inferred from which artifacts are present), not every check for every dir.
  **Rationale:** Matches the spec's "one-shot migration command" intent (Breaking changes, line 46) — a user runs it once to discover which in-flight branches need manual attention.
  **Trade-offs:** Ambiguous when a feature dir is mid-stage; documented in `docs/articles/preflight.md` as "checks through the highest artifact present".

## Project structure changes

```text
src/aiadev/preflight.py                              (new)
src/aiadev/commands/preflight.py                     (new)
src/aiadev/cli.py                                    (modified — register subcommand)
skills/requesting-code-review/SKILL.md               (modified — write .aiadev/review.yaml step)
skills/finishing-a-branch/SKILL.md                   (modified — preflight call-out + review.yaml gate)
skills/clarify/SKILL.md                              (modified — preflight call-out)
skills/plan/SKILL.md                                 (modified — preflight call-out)
skills/tasks/SKILL.md                                (modified — preflight call-out)
skills/implement/SKILL.md                            (modified — preflight call-out)
skills/analyze/SKILL.md                              (modified — preflight call-out)
tests/test_preflight.py                              (new — unit tests for check())
tests/test_preflight_requirements_coverage.py       (new — frontmatter / template / table coverage)
tests/test_preflight_pipeline.py                     (new — E2E + CLI + timing)
docs/articles/preflight.md                           (new — migration note, AIADEV_PREFLIGHT semantics)
CHANGELOG.md                                         (modified — Added / Changed / Breaking)
```

## Phase breakdown

### Phase 1 — Checker core (Story 1 scenarios 1-6, Story 2 scenarios 1-3)

Each bullet is one task: write the test, run `pytest -x <file>::<function>`, observe RED with the listed failure, then implement.

- `tests/test_preflight.py::test_missing_tasks_md_emits_run_tasks_message` — Story 1 sc1. Expected RED: `ModuleNotFoundError: aiadev.preflight`.
- `tests/test_preflight.py::test_missing_spec_aborts_all_downstream_skills` — Story 1 sc2. Parametrised over `clarify, plan, tasks, implement, analyze, requesting-code-review, finishing-a-branch`.
- `tests/test_preflight.py::test_needs_clarification_markers_block_plan` — Story 1 sc3. Asserts message `pre-flight: spec.md has 2 unresolved [NEEDS CLARIFICATION] markers — run /aiadev:clarify first`.
- `tests/test_preflight.py::test_missing_review_yaml_blocks_finishing_branch` — Story 1 sc4.
- `tests/test_preflight.py::test_branch_slug_mismatch_aborts` — Story 1 sc5. Git branch is read via `git rev-parse --abbrev-ref HEAD` shelled through `subprocess.run` with `check=False`; tests monkeypatch the call.
- `tests/test_preflight.py::test_env_warn_downgrades_to_stderr_diagnostic` — Story 1 sc6.
- `tests/test_preflight.py::test_missing_section_anchor_in_spec_aborts_plan` — Story 2 sc1.
- `tests/test_preflight.py::test_language_header_mismatch_spec_vs_plan_aborts_tasks` — Story 2 sc2.
- `tests/test_preflight.py::test_plan_branch_header_mismatch_aborts_tasks` — Story 2 sc3.
- Implement `src/aiadev/preflight.py` — `PreflightIssue`, `check()`, `REQUIREMENTS`, `SPEC_ANCHORS` / `PLAN_ANCHORS` / `TASKS_ANCHORS`, `_language_of()`, `_count_needs_clarification()`, `_current_branch()`. Each helper is introduced only by the test that first needs it.

### Phase 2 — CLI surface (Story 3 scenarios 1-3) and template coverage test

- `tests/test_preflight.py::test_cli_happy_path_exits_zero_silently` — Story 3 sc1. Uses `click.testing.CliRunner`. Expected RED: `aiadev preflight` subcommand not registered.
- `tests/test_preflight.py::test_cli_reports_same_message_as_in_skill_check` — Story 3 sc2. Asserts byte-identical output between `check()` return and CLI stderr line.
- `tests/test_preflight.py::test_cli_unknown_skill_lists_known_skills` — Story 3 sc3.
- `tests/test_preflight.py::test_cli_all_flag_iterates_every_feature_dir` — covers `aiadev preflight --all` required by spec Breaking-Changes line 46.
- `tests/test_preflight_requirements_coverage.py::test_every_pipeline_skill_has_a_requirements_row` — mitigates the sync-drift risk in ADR #2.
- `tests/test_preflight_requirements_coverage.py::test_every_anchor_exists_in_its_template` — round-trips `SPEC_ANCHORS` against `templates/spec-template.md`, ditto plan and tasks templates.
- Implement `src/aiadev/commands/preflight.py` and wire it into `cli.py`.

### Phase 3 — SKILL.md hand-offs (Success criterion #1 end-to-end)

Each SKILL.md change is observable behaviour (the skill now aborts where it did not before) and is covered by the E2E test in Phase 4. Task order: write the E2E test first (Phase 4 task 1), confirm RED, then do the doc edits in this phase, then re-run to reach GREEN.

- Edit `skills/clarify/SKILL.md` Preconditions: add `"Invoke pre-flight: aiadev preflight clarify --feature <slug>. Abort on non-zero unless AIADEV_PREFLIGHT=warn."`.
- Same edit in `skills/plan/SKILL.md`, `skills/tasks/SKILL.md`, `skills/implement/SKILL.md`, `skills/analyze/SKILL.md`.
- Edit `skills/requesting-code-review/SKILL.md` to add an explicit step: "On review approval, write `.aiadev/review.yaml` at the repo root with keys `status: approved` and `timestamp: <ISO-8601 UTC>`. On changes-requested, write `status: changes_requested` and a one-line `reason:`."
- Edit `skills/finishing-a-branch/SKILL.md` Preconditions: add the preflight call-out **and** an explicit `"Abort unless .aiadev/review.yaml has status: approved."`

### Phase 4 — E2E integration, migration, changelog

- `tests/test_preflight_pipeline.py::test_deleting_tasks_md_causes_implement_preflight_failure` — the canonical Success-criterion-#5 scenario (spec line 32). Builds a temp feature dir, deletes `tasks.md`, runs `aiadev preflight implement --feature …`, asserts exit ≠ 0 and the actionable single-line message.
- `tests/test_preflight_pipeline.py::test_deleting_each_prior_artifact_fails_the_next_skill` — parametrised over every `(skill, deleted_artifact)` pair required by the Success-criterion-#5 wording "deleting any prior-stage artifact causes the immediately following pipeline skill to fail".
- `tests/test_preflight_pipeline.py::test_reference_dir_completes_under_500ms` — Success criterion #3. Uses `time.perf_counter()` around `check("analyze", reference_fixture)` and asserts `< 0.5`. Reference fixture lives in `tests/fixtures/preflight/reference/`.
- `tests/test_preflight_pipeline.py::test_review_yaml_approved_lets_finishing_branch_pass` — closes the Story 1 sc4 loop end-to-end through the CLI.
- Write `docs/articles/preflight.md` — covers: what pre-flight checks; the `AIADEV_PREFLIGHT=warn` debug-only switch; the one-shot `aiadev preflight --all` migration command; the expected diagnostic format.
- Append `CHANGELOG.md [Unreleased]`: `Added` (preflight module + CLI), `Changed` (seven SKILL.md files), `Breaking` (in-flight feature dirs must satisfy anchors + language + branch match; `finishing-a-branch` now requires `.aiadev/review.yaml`).

## Risks and mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| In-flight feature dirs fail pre-flight on day 1 | High | Med | `docs/articles/preflight.md` documents `aiadev preflight --all`; CHANGELOG flags Breaking |
| Anchor list drifts from templates | Med | Med | `test_preflight_requirements_coverage.py::test_every_anchor_exists_in_its_template` |
| `AIADEV_PREFLIGHT=warn` becomes the CI default | Low | High | docs + CHANGELOG call the env var "debugging only"; a CI job asserts the var is unset |
| 500 ms budget regresses as anchor list grows | Low | Low | `test_reference_dir_completes_under_500ms` asserts the bound on every CI run |
| Subprocess call to `git` makes unit tests flaky | Med | Low | `_current_branch()` takes an injected callable; unit tests pass a stub |

## Complexity tracking

| Article waived | Reason | Alternatives considered | Reviewer |
|---|---|---|---|
| | | | |

## Hand-off to `tasks`

The next skill is `tasks`. It consumes this plan and produces `tasks.md`.
Pre-conditions before hand-off:

- [x] Constitution Check is fully populated, no blank rows.
- [x] Complexity tracking is filled or empty-and-justified.
- [x] Project structure delta is accurate.
