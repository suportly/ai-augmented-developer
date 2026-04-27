# Tasks: Pipeline pre-flight checks

> Produced by the `tasks` skill from an approved `plan.md`. Consumed by `implement`.

**Branch:** `feature/pipeline-preflight-checks`
**Plan:** [plan.md](./plan.md)
**Generated:** 2026-04-20
**Language:** en

---

## How to read this file

- Tasks are ordered. `implement` runs them top-to-bottom.
- One task = one commit. The commit message starts with the task id.
- Each task links back to the spec acceptance scenarios it exercises.
- `Status` is one of: `pending`, `in_progress`, `blocked`, `done`. Only `implement` mutates it.

## Task list

### T001 — Bootstrap preflight module with first failing scenario

- **Status:** pending
- **Depends on:** —
- **Files:**
  - create: `src/aiadev/preflight.py`
  - test: `tests/test_preflight.py`
- **Spec scenarios:** Story 1 scenario 1
- **Acceptance:**
  - [ ] `tests/test_preflight.py::test_missing_tasks_md_emits_run_tasks_message` written; `pytest -x tests/test_preflight.py::test_missing_tasks_md_emits_run_tasks_message` fails with `ModuleNotFoundError: aiadev.preflight`.
  - [ ] Implement minimum `PreflightIssue` dataclass + `check(skill, feature_dir)` that returns `[PreflightIssue("pre-flight: tasks.md missing — run /aiadev:tasks first")]` when `skill == "implement"` and `tasks.md` absent.
  - [ ] Existing test suite still passes (`pytest`).
  - [ ] Commit: `feat(preflight): T001 bootstrap module and missing-tasks check`.
- **Notes:** The dataclass shape and helper imports introduced here are reused across T002–T009; do not over-engineer beyond what this single test demands.

### T002 — Missing spec.md aborts every downstream skill

- **Status:** pending
- **Depends on:** T001
- **Files:**
  - modify: `src/aiadev/preflight.py`
  - test: `tests/test_preflight.py`
- **Spec scenarios:** Story 1 scenario 2
- **Acceptance:**
  - [ ] `test_missing_spec_aborts_all_downstream_skills` parametrised over `clarify, plan, tasks, implement, analyze, requesting-code-review, finishing-a-branch`; observed failing because `check()` does not yet handle `spec.md` absence.
  - [ ] Implement: `REQUIREMENTS` table seeded; `check()` emits `pre-flight: spec.md missing — run /aiadev:specify first` for every skill except `specify`.
  - [ ] No regression.
  - [ ] Commit: `feat(preflight): T002 abort downstream skills when spec.md missing`.

### T003 — Block plan when spec.md has`[NEEDS CLARIFICATION]` markers

- **Status:** pending
- **Depends on:** T002
- **Files:**
  - modify: `src/aiadev/preflight.py`
  - test: `tests/test_preflight.py`
- **Spec scenarios:** Story 1 scenario 3
- **Acceptance:**
  - [ ] `test_needs_clarification_markers_block_plan` asserts message `pre-flight: spec.md has 2 unresolved `​`[NEEDS CLARIFICATION]`​` markers — run /aia:clarify first`. Observed RED.
  - [ ] Implement `_count_needs_clarification(text)` and wire into the `plan` rule.
  - [ ] No regression.
  - [ ] Commit: `feat(preflight): T003 block plan on unresolved clarification markers`.

### T004 — Missing review.yaml blocks finishing-a-branch

- **Status:** pending
- **Depends on:** T002
- **Files:**
  - modify: `src/aiadev/preflight.py`
  - test: `tests/test_preflight.py`
- **Spec scenarios:** Story 1 scenario 4
- **Acceptance:**
  - [ ] `test_missing_review_yaml_blocks_finishing_branch` written; covers (a) absent file, (b) `status: changes_requested`, (c) `status: approved`. Observed RED for cases (a) and (b).
  - [ ] Implement repo-root `.aiadev/review.yaml` reader using `yaml.safe_load`; emit `pre-flight: review approval missing — run /aiadev:requesting-code-review first` when missing or non-approved.
  - [ ] No regression.
  - [ ] Commit: `feat(preflight): T004 gate finishing-a-branch on review.yaml approval`.

### T005 — Branch slug mismatch aborts every skill

- **Status:** pending
- **Depends on:** T002
- **Files:**
  - modify: `src/aiadev/preflight.py`
  - test: `tests/test_preflight.py`
- **Spec scenarios:** Story 1 scenario 5
- **Acceptance:**
  - [ ] `test_branch_slug_mismatch_aborts` injects a stub `_current_branch` callable returning `feature/other-thing`; expects message `pre-flight: git branch 'feature/other-thing' does not match feature directory '0010-pipeline-preflight-checks'`. Observed RED.
  - [ ] Implement `_current_branch(runner=subprocess.run)` and inject into `check()`; raise the diagnostic on mismatch.
  - [ ] No regression.
  - [ ] Commit: `feat(preflight): T005 reject branch / feature-dir mismatch`.

### T006 — `AIADEV_PREFLIGHT=warn` downgrades abort to stderr

- **Status:** pending
- **Depends on:** T001
- **Files:**
  - modify: `src/aiadev/preflight.py`
  - test: `tests/test_preflight.py`
- **Spec scenarios:** Story 1 scenario 6
- **Acceptance:**
  - [ ] `test_env_warn_downgrades_to_stderr_diagnostic` deletes tasks.md, sets `AIADEV_PREFLIGHT=warn`, asserts `check()` returns the issue list AND a `would_abort=False` flag (or equivalent) so callers continue. Observed RED.
  - [ ] Implement env-var resolution helper `_should_abort(env)` matching the truthy/falsy table from `aiadev.config`; default = abort, `warn` = continue.
  - [ ] No regression.
  - [ ] Commit: `feat(preflight): T006 honour AIADEV_PREFLIGHT=warn`.

### T007 — Missing section anchor in spec.md aborts plan

- **Status:** pending
- **Depends on:** T002
- **Files:**
  - modify: `src/aiadev/preflight.py`
  - test: `tests/test_preflight.py`
- **Spec scenarios:** Story 2 scenario 1
- **Acceptance:**
  - [ ] `test_missing_section_anchor_in_spec_aborts_plan` strips `<!-- section: Problem -->` from a fixture spec; expects `pre-flight: spec.md missing required section anchor 'Problem'`. Observed RED.
  - [ ] Define `SPEC_ANCHORS` (literal list copied from `templates/spec-template.md`); implement `_missing_anchors(text, anchors)`; wire into `plan` rule.
  - [ ] No regression.
  - [ ] Commit: `feat(preflight): T007 enforce spec.md section anchors`.

### T008 — Language header mismatch (spec vs plan) aborts tasks

- **Status:** pending
- **Depends on:** T007
- **Files:**
  - modify: `src/aiadev/preflight.py`
  - test: `tests/test_preflight.py`
- **Spec scenarios:** Story 2 scenario 2
- **Acceptance:**
  - [ ] `test_language_header_mismatch_spec_vs_plan_aborts_tasks` (spec=`en`, plan=`pt-BR`); expects `pre-flight: language mismatch — spec.md=en, plan.md=pt-BR`. Observed RED.
  - [ ] Implement `_language_of(text)` extracting the `**Language:**` header; wire into `tasks` rule.
  - [ ] No regression.
  - [ ] Commit: `feat(preflight): T008 detect language drift across artifacts`.

### T009 — plan.md branch header mismatch aborts tasks

- **Status:** pending
- **Depends on:** T007
- **Files:**
  - modify: `src/aiadev/preflight.py`
  - test: `tests/test_preflight.py`
- **Spec scenarios:** Story 2 scenario 3
- **Acceptance:**
  - [ ] `test_plan_branch_header_mismatch_aborts_tasks` writes `**Branch:** \`feature/foo\`` in plan.md while feature dir is `0010-pipeline-preflight-checks`; expects `pre-flight: plan.md branch header 'feature/foo' does not match feature directory '0010-pipeline-preflight-checks'`. Observed RED.
  - [ ] Implement `_branch_header_of(text)` and wire into `tasks` rule.
  - [ ] No regression.
  - [ ] Commit: `feat(preflight): T009 reject plan.md branch-header drift`.

### T010 — Register `aiadev preflight` Click subcommand (happy path)

- **Status:** pending
- **Depends on:** T009
- **Files:**
  - create: `src/aiadev/commands/preflight.py`
  - modify: `src/aiadev/cli.py`
  - test: `tests/test_preflight.py`
- **Spec scenarios:** Story 3 scenario 1
- **Acceptance:**
  - [ ] `test_cli_happy_path_exits_zero_silently` uses `CliRunner` against a valid feature dir; expects exit 0 and empty output. Observed RED: subcommand not registered.
  - [ ] Implement `preflight_command` Click group; add to `cli.main`.
  - [ ] No regression.
  - [ ] Commit: `feat(preflight): T010 add CLI subcommand`.

### T011 — CLI emits byte-identical diagnostic to in-skill check

- **Status:** pending
- **Depends on:** T010
- **Files:**
  - modify: `src/aiadev/commands/preflight.py`
  - test: `tests/test_preflight.py`
- **Spec scenarios:** Story 3 scenario 2
- **Acceptance:**
  - [ ] `test_cli_reports_same_message_as_in_skill_check` deletes tasks.md, asserts CLI stderr line equals the `PreflightIssue.message` returned by `check()`. Observed RED.
  - [ ] Implement: CLI prints each issue to stderr verbatim, exits with `len(issues)` clamped to 1.
  - [ ] No regression.
  - [ ] Commit: `feat(preflight): T011 mirror in-skill diagnostic on the CLI`.

### T012 — CLI rejects unknown skills with the known list

- **Status:** pending
- **Depends on:** T010
- **Files:**
  - modify: `src/aiadev/commands/preflight.py`
  - test: `tests/test_preflight.py`
- **Spec scenarios:** Story 3 scenario 3
- **Acceptance:**
  - [ ] `test_cli_unknown_skill_lists_known_skills` invokes `aiadev preflight bogus --feature 0010-…`; expects exit ≠ 0 and `unknown skill 'bogus'; expected one of: clarify, plan, tasks, implement, analyze, requesting-code-review, finishing-a-branch`. Observed RED.
  - [ ] Implement skill-name validation against `REQUIREMENTS.keys()`.
  - [ ] No regression.
  - [ ] Commit: `feat(preflight): T012 reject unknown skill names on the CLI`.

### T013 — `--all` iterates every feature dir

- **Status:** pending
- **Depends on:** T011
- **Files:**
  - modify: `src/aiadev/commands/preflight.py`
  - test: `tests/test_preflight.py`
- **Spec scenarios:** spec Breaking-Changes line 46 ("one-shot `aiadev preflight --all` command")
- **Acceptance:**
  - [ ] `test_cli_all_flag_iterates_every_feature_dir` builds two feature dirs (one valid, one missing tasks.md), runs `aiadev preflight --all`, expects exit ≠ 0 with one diagnostic line scoped to the broken dir. Observed RED: `--all` flag unknown.
  - [ ] Implement `--all` mutually exclusive with `--feature`; iterate `specs/*/` and run the highest-stage check for each (stage = highest artifact present).
  - [ ] No regression.
  - [ ] Commit: `feat(preflight): T013 add --all migration flag`.

### T014 — Coverage test: every pipeline skill has a REQUIREMENTS row

- **Status:** pending
- **Depends on:** T013
- **Files:**
  - create: `tests/test_preflight_requirements_coverage.py`
- **Spec scenarios:** plan ADR #2 sync-drift mitigation
- **Acceptance:**
  - [ ] `test_every_pipeline_skill_has_a_requirements_row` discovers every directory under `skills/` that ships a SKILL.md whose frontmatter declares a `handoffs:` chain in the pipeline; asserts each has a row in `REQUIREMENTS`. Observed RED if any skill is missing.
  - [ ] If RED on this branch, add the missing row in `preflight.py`.
  - [ ] No regression.
  - [ ] Commit: `test(preflight): T014 cover REQUIREMENTS table against skills/`.

### T015 — Coverage test: anchors round-trip against templates

- **Status:** pending
- **Depends on:** T014
- **Files:**
  - modify: `tests/test_preflight_requirements_coverage.py`
- **Spec scenarios:** plan Risks line — anchor drift mitigation
- **Acceptance:**
  - [ ] `test_every_anchor_exists_in_its_template` checks each entry of `SPEC_ANCHORS` is present as `<!-- section: <name> -->` in `templates/spec-template.md`; same for `PLAN_ANCHORS` against `templates/plan-template.md` and `TASKS_ANCHORS` against `templates/tasks-template.md`. Observed RED if any anchor is missing.
  - [ ] Reconcile lists if RED.
  - [ ] No regression.
  - [ ] Commit: `test(preflight): T015 round-trip anchor lists against templates`.

### T016 — `clarify` SKILL.md preflight call-out

- **Status:** pending
- **Depends on:** T015
- **Files:**
  - modify: `skills/clarify/SKILL.md`
  - test: `tests/test_preflight_requirements_coverage.py`
- **Spec scenarios:** Success criterion #1
- **Acceptance:**
  - [ ] `test_clarify_skill_md_has_preflight_callout` greps the file for the literal `aiadev preflight clarify --feature` string. Observed RED.
  - [ ] Add the call-out under the Preconditions section.
  - [ ] No regression.
  - [ ] Commit: `docs(preflight): T016 wire clarify skill to preflight`.

### T017 — `plan` SKILL.md preflight call-out

- **Status:** pending
- **Depends on:** T015
- **Files:**
  - modify: `skills/plan/SKILL.md`
  - test: `tests/test_preflight_requirements_coverage.py`
- **Spec scenarios:** Success criterion #1
- **Acceptance:**
  - [ ] `test_plan_skill_md_has_preflight_callout` asserts `aiadev preflight plan --feature` literal. Observed RED.
  - [ ] Add the call-out.
  - [ ] No regression.
  - [ ] Commit: `docs(preflight): T017 wire plan skill to preflight`.

### T018 — `tasks` SKILL.md preflight call-out

- **Status:** pending
- **Depends on:** T015
- **Files:**
  - modify: `skills/tasks/SKILL.md`
  - test: `tests/test_preflight_requirements_coverage.py`
- **Spec scenarios:** Success criterion #1
- **Acceptance:**
  - [ ] `test_tasks_skill_md_has_preflight_callout` asserts `aiadev preflight tasks --feature` literal. Observed RED.
  - [ ] Add the call-out.
  - [ ] No regression.
  - [ ] Commit: `docs(preflight): T018 wire tasks skill to preflight`.

### T019 — `implement` SKILL.md preflight call-out

- **Status:** pending
- **Depends on:** T015
- **Files:**
  - modify: `skills/implement/SKILL.md`
  - test: `tests/test_preflight_requirements_coverage.py`
- **Spec scenarios:** Success criterion #1
- **Acceptance:**
  - [ ] `test_implement_skill_md_has_preflight_callout` asserts `aiadev preflight implement --feature` literal. Observed RED.
  - [ ] Add the call-out.
  - [ ] No regression.
  - [ ] Commit: `docs(preflight): T019 wire implement skill to preflight`.

### T020 — `analyze` SKILL.md preflight call-out

- **Status:** pending
- **Depends on:** T015
- **Files:**
  - modify: `skills/analyze/SKILL.md`
  - test: `tests/test_preflight_requirements_coverage.py`
- **Spec scenarios:** Success criterion #1
- **Acceptance:**
  - [ ] `test_analyze_skill_md_has_preflight_callout` asserts `aiadev preflight analyze --feature` literal. Observed RED.
  - [ ] Add the call-out.
  - [ ] No regression.
  - [ ] Commit: `docs(preflight): T020 wire analyze skill to preflight`.

### T021 — `requesting-code-review` writes `.aiadev/review.yaml`

- **Status:** pending
- **Depends on:** T015
- **Files:**
  - modify: `skills/requesting-code-review/SKILL.md`
  - test: `tests/test_preflight_requirements_coverage.py`
- **Spec scenarios:** Story 1 scenario 4 (cross-feature dep declared in spec Traceability)
- **Acceptance:**
  - [ ] `test_review_skill_md_documents_review_yaml_emission` asserts the file contains the literal substrings `.aiadev/review.yaml`, `status: approved`, `status: changes_requested`, and `timestamp:`. Observed RED.
  - [ ] Add an explicit step under the skill's hand-off section: "On approval, write `.aiadev/review.yaml` with `status: approved` and `timestamp:` (ISO-8601 UTC). On changes-requested, write `status: changes_requested` plus a one-line `reason:`."
  - [ ] No regression.
  - [ ] Commit: `docs(preflight): T021 require review.yaml emission from review skill`.

### T022 — `finishing-a-branch` preflight + review.yaml gate

- **Status:** pending
- **Depends on:** T021
- **Files:**
  - modify: `skills/finishing-a-branch/SKILL.md`
  - test: `tests/test_preflight_requirements_coverage.py`
- **Spec scenarios:** Story 1 scenario 4, Success criterion #1
- **Acceptance:**
  - [ ] `test_finishing_skill_md_has_preflight_and_review_gate` asserts both `aiadev preflight finishing-a-branch --feature` and `.aiadev/review.yaml` literals are present. Observed RED.
  - [ ] Add both call-outs under Preconditions.
  - [ ] No regression.
  - [ ] Commit: `docs(preflight): T022 gate finishing-a-branch on preflight + review`.

### T023 — E2E: deleting tasks.md fails `implement` preflight

- **Status:** pending
- **Depends on:** T013
- **Files:**
  - create: `tests/test_preflight_pipeline.py`
  - create: `tests/fixtures/preflight/reference/spec.md`
  - create: `tests/fixtures/preflight/reference/plan.md`
  - create: `tests/fixtures/preflight/reference/tasks.md`
- **Spec scenarios:** Success criterion #5, Story 1 scenario 1
- **Acceptance:**
  - [ ] `test_deleting_tasks_md_causes_implement_preflight_failure` copies the reference fixture to a tmp dir, deletes tasks.md, runs `aiadev preflight implement --feature reference` via `CliRunner`, asserts exit ≠ 0 and the actionable message. Observed RED until fixture exists.
  - [ ] Build the reference fixture (canonical artifacts that pass every check when whole).
  - [ ] No regression.
  - [ ] Commit: `test(preflight): T023 add E2E missing-tasks scenario and fixture`.

### T024 — E2E: deleting any prior artifact fails the next skill

- **Status:** pending
- **Depends on:** T023
- **Files:**
  - modify: `tests/test_preflight_pipeline.py`
- **Spec scenarios:** Success criterion #5
- **Acceptance:**
  - [ ] `test_deleting_each_prior_artifact_fails_the_next_skill` parametrised over `[("plan", "spec.md"), ("tasks", "spec.md"), ("tasks", "plan.md"), ("implement", "spec.md"), ("implement", "plan.md"), ("implement", "tasks.md"), ("analyze", "tasks.md"), ("finishing-a-branch", ".aiadev/review.yaml")]`. Each pair: delete file, run CLI, expect exit ≠ 0 + matching message. Observed RED.
  - [ ] Add `.aiadev/review.yaml` (status approved) to the reference fixture so the deletion path is meaningful.
  - [ ] No regression.
  - [ ] Commit: `test(preflight): T024 cover every prior-stage deletion`.

### T025 — Performance: reference dir under 500 ms

- **Status:** pending
- **Depends on:** T023
- **Files:**
  - modify: `tests/test_preflight_pipeline.py`
- **Spec scenarios:** Success criterion #3
- **Acceptance:**
  - [ ] `test_reference_dir_completes_under_500ms` calls `check("analyze", reference_fixture)` inside `time.perf_counter()`; asserts elapsed `< 0.5`. Observed RED if `check()` regresses.
  - [ ] Profile and tighten if necessary; expect this to pass first time given the small reference dir.
  - [ ] No regression.
  - [ ] Commit: `test(preflight): T025 enforce 500 ms reference budget`.

### T026 — E2E: approved review.yaml lets `finishing-a-branch` pass

- **Status:** pending
- **Depends on:** T024
- **Files:**
  - modify: `tests/test_preflight_pipeline.py`
- **Spec scenarios:** Story 1 scenario 4 (positive case)
- **Acceptance:**
  - [ ] `test_review_yaml_approved_lets_finishing_branch_pass` writes `.aiadev/review.yaml` with `status: approved`; runs CLI; asserts exit 0. Observed RED if the gate logic is wrong.
  - [ ] Adjust gate logic if needed.
  - [ ] No regression.
  - [ ] Commit: `test(preflight): T026 close the approved-review happy path`.

### T027 — Migration doc

- **Status:** pending
- **Depends on:** T026
- **Files:**
  - create: `docs/articles/preflight.md`
- **Spec scenarios:** spec Breaking-Changes line 46
- **Acceptance:**
  - [ ] `tests/test_preflight_requirements_coverage.py::test_migration_doc_exists_and_mentions_aiadev_preflight_all` asserts the file exists and contains the literal `aiadev preflight --all` and `AIADEV_PREFLIGHT=warn` strings. Observed RED.
  - [ ] Write the article: pre-flight purpose, diagnostic format, `AIADEV_PREFLIGHT=warn` debug-only switch, one-shot `aiadev preflight --all` migration command, what to do when an in-flight feature dir fails.
  - [ ] No regression.
  - [ ] Commit: `docs(preflight): T027 publish migration article`.

### T028 — CHANGELOG entry

- **Status:** pending
- **Depends on:** T027
- **Files:**
  - modify: `CHANGELOG.md`
- **Spec scenarios:** Constitution Article IV (evidence over claims)
- **Acceptance:**
  - [ ] `tests/test_changelog_entry.py` (existing) passes after appending an `[Unreleased]` block with `Added` (preflight module + CLI), `Changed` (seven SKILL.md files), `Breaking` (in-flight feature dirs must satisfy anchors + language + branch match; `finishing-a-branch` requires `.aiadev/review.yaml`).
  - [ ] If `test_changelog_entry.py` does not enforce this, add a focused assertion in `tests/test_preflight_requirements_coverage.py::test_changelog_mentions_preflight_breaking_change`. Observed RED first.
  - [ ] Full suite green.
  - [ ] Commit: `chore(preflight): T028 changelog entry for preflight + breaking changes`.

## Parallelization hints

- Parallel group A — independent test files / SKILL.md edits, all rooted in T015: T016, T017, T018, T019, T020 (each touches a different `skills/<name>/SKILL.md` and a disjoint test function).
- Parallel group B — disjoint E2E additions atop T023: T024, T025 (both append to `tests/test_preflight_pipeline.py` but use distinct test functions; if `implement` runs them strictly serially, no harm).
- Serial: everything else (T001–T015, T021, T022, T023, T026, T027, T028).

## Post-task checklist

After every task:

- [ ] Commit message references the task id.
- [ ] Status in this file updated.

After all tasks:

- [ ] Full test suite passes (`pytest`).
- [ ] `analyze` skill runs and reports no drift vs spec / plan.
- [ ] Hand off to `requesting-code-review` to open the PR.
