# Tasks: implement skill must mark tasks done in tasks.md

> Produced by the `tasks` skill from an approved `plan.md`. Consumed by `implement`.

**Branch:** `feature/implement-task-status-tracking`
**Plan:** [plan.md](./plan.md)
**Generated:** 2026-05-06
**Language:** en

---

## How to read this file

- Tasks are ordered. `implement` runs them top-to-bottom.
- One task = one commit. The commit message starts with the task id.
- Each task links back to the spec acceptance scenarios it exercises.
- `Status` is one of: `pending`, `in_progress`, `blocked`, `done`. Only `implement` mutates it.

## Task list

### T001 — Add tasks.md fixtures (clean, malformed, out-of-order, in_progress, all-done)

- **Status:** done
- **Depends on:** —
- **Files:**
  - create: `tests/fixtures/tasks_md_samples/clean_3_tasks.md`
  - create: `tests/fixtures/tasks_md_samples/malformed_missing_status.md`
  - create: `tests/fixtures/tasks_md_samples/out_of_order_done_pending_done.md`
  - create: `tests/fixtures/tasks_md_samples/in_progress_mid_list.md`
  - create: `tests/fixtures/tasks_md_samples/all_done.md`
  - test: — (fixtures only; consumed by T002)
- **Spec scenarios:** Story 1 sc1, Story 2 sc1–sc4 (provides the inputs each scenario reads).
- **Acceptance:**
  - [ ] Each fixture is a valid `tasks.md` per the canonical structure in `templates/tasks-template.md` except for the deliberate defect named in the filename.
  - [ ] Fixtures use `T001`, `T002`, `T003` ids and minimal `Files:` blocks (no real paths needed — fixtures are parser fodder).
  - [ ] No test introduced yet; this task ships only data.
  - [ ] Commit message: `test(tasks-status): T001 add tasks.md golden fixtures`.

### T002 — Red unit tests for tasks_status parse/validate/mark_done

- **Status:** pending
- **Depends on:** T001
- **Files:**
  - create: `tests/test_tasks_status.py`
  - test: `tests/test_tasks_status.py`
- **Spec scenarios:** Story 1 sc2 (mark_done writes only one row), Story 2 sc1 (resume skip), sc2 (out-of-order halt with exact error string), sc3 (all-done short-circuit), sc4 (in_progress treated as pending).
- **Acceptance:**
  - [ ] Failing test written; `pytest tests/test_tasks_status.py` fails with `ModuleNotFoundError: aiadev.tasks_status` (the right red — module does not yet exist).
  - [ ] Tests are parametrised over the T001 fixtures plus a copy-on-write mutation test for `mark_done`.
  - [ ] Story 2 sc2 assertion includes the verbatim error string `ERROR: tasks.md inconsistency — T003 is done but T002 is pending. Fix tasks.md manually before resuming.`.
  - [ ] Story 2 sc4 assertion checks that an `in_progress` row is reported as a re-dispatch target (treated-as-pending), not skipped.
  - [ ] No other existing test regresses.
  - [ ] Commit message: `test(tasks-status): T002 add red unit tests for parse/validate/mark_done`.

### T003 — Red drift-validator import test

- **Status:** pending
- **Depends on:** —
- **Files:**
  - create: `tests/test_implement_skill_drift.py`
  - test: `tests/test_implement_skill_drift.py`
- **Spec scenarios:** Story 3 sc1 (loop section names the file edit + transform + commit timing), sc2 (CI-enforced drift check), sc3 (per-task dispatch contract references status-mutation step).
- **Acceptance:**
  - [ ] Failing test written; `pytest tests/test_implement_skill_drift.py` fails with `ImportError: cannot import name 'check_implement_mirror' from scripts.validate_skills` (the right red — function not added yet).
  - [ ] File contains a parametrised content assertion (gated behind the import) that the loop section of `skills/implement/SKILL.md` and `.claude/skills/implement/SKILL.md` contains the literal sub-procedure wording introduced in T006. The content assertion is also expected red until T006.
  - [ ] An inline comment at the top of the file states which tests are intentionally red and which become green after T005 vs T006.
  - [ ] Commit message: `test(skill-drift): T003 add red drift-validator import + content tests`.

### T004 — Implement aiadev.tasks_status (parse, validate, mark_done)

- **Status:** pending
- **Depends on:** T002
- **Files:**
  - create: `src/aiadev/tasks_status.py`
  - test: `tests/test_tasks_status.py` (existing red from T002)
- **Spec scenarios:** Story 1 sc2, Story 2 sc1, sc2, sc3, sc4.
- **Acceptance:**
  - [ ] `pytest tests/test_tasks_status.py` is green.
  - [ ] Module exports exactly `parse`, `validate`, `mark_done`, `TasksMdError`. No speculative helpers.
  - [ ] `validate` enforces (a) every `### TNNN` block has a parseable `**Status:**` line in `{pending, in_progress, blocked, done}`, (b) `done` ids form a contiguous prefix of declared task order, raising `TasksMdError` otherwise.
  - [ ] `mark_done` rewrites only the targeted `### TNNN` block's `**Status:**` line; surrounding bytes unchanged (golden-file diff in test).
  - [ ] No other existing test regresses (`pytest`).
  - [ ] Commit message: `feat(tasks-status): T004 implement parse/validate/mark_done helper`.
- **Notes:**
  Use a single regex constant for the `**Status:**` line shape and re-use it for both `parse` and `mark_done` so the two cannot drift.

### T005 — Add check_implement_mirror to scripts/validate_skills.py

- **Status:** pending
- **Depends on:** T003
- **Files:**
  - modify: `scripts/validate_skills.py`
  - test: `tests/test_implement_skill_drift.py`
- **Spec scenarios:** Story 3 sc2 (CI-enforced drift check).
- **Acceptance:**
  - [ ] `from scripts.validate_skills import check_implement_mirror` resolves; the import-level red in T003 turns green.
  - [ ] `check_implement_mirror()` extracts the `## The loop` section (anchor-matched from `## The loop` to the next `## ` heading) of both `skills/implement/SKILL.md` and `.claude/skills/implement/SKILL.md`, and returns success only when the two are non-whitespace-equal. On mismatch it raises with both file paths and a unified diff snippet.
  - [ ] The function is wired into the script's main entry point so CI invocation surfaces the new check.
  - [ ] No other existing validator regresses (`python scripts/validate_skills.py` exits 0 on the unchanged tree).
  - [ ] The Story 3 *content* assertion in `tests/test_implement_skill_drift.py` is still red (expected — content lands in T006).
  - [ ] Commit message: `feat(validate-skills): T005 add implement-mirror drift check`.

### T006 — Update skills/implement/SKILL.md loop step 5

- **Status:** pending
- **Depends on:** T004, T005
- **Files:**
  - modify: `skills/implement/SKILL.md`
  - test: `tests/test_implement_skill_drift.py` (loop content for the bare-form file)
- **Spec scenarios:** Story 1 sc1, sc2, sc3, sc4; Story 2 sc1, sc2, sc3, sc4; Story 3 sc1, sc3.
- **Acceptance:**
  - [ ] Step 5 of the loop is replaced with a numbered sub-procedure `(a)–(f)` covering: read row, skip-if-`done`, abort on malformed/prefix-violation with the exact spec error string, treat `in_progress` as `pending`, post-review `Edit` `pending → done`, `git add` task code files **and** `tasks.md`, `git commit`; on commit failure run `git restore --staged tasks.md && git checkout -- tasks.md` before re-raising.
  - [ ] The sub-procedure cites the orchestrator (not the subagent) as the actor performing the `Edit`.
  - [ ] Story 3 content assertion in `tests/test_implement_skill_drift.py` against `skills/implement/SKILL.md` goes green; the mirror assertion remains red until T007.
  - [ ] No regression in any other existing test.
  - [ ] Commit message: `docs(implement-skill): T006 add explicit status-flip sub-procedure to step 5`.

### T007 — Mirror the loop change into .claude/skills/implement/SKILL.md

- **Status:** pending
- **Depends on:** T006
- **Files:**
  - modify: `.claude/skills/implement/SKILL.md`
  - test: `tests/test_implement_skill_drift.py` (full green)
- **Spec scenarios:** Story 3 sc1, sc2, sc3.
- **Acceptance:**
  - [ ] The `## The loop` section is byte-equal (modulo whitespace) to the bare-form file from T006.
  - [ ] `python scripts/validate_skills.py` exits 0 (drift check passes).
  - [ ] All three Story 3 assertions in `tests/test_implement_skill_drift.py` are green (import, drift, content).
  - [ ] No regression elsewhere (`pytest`).
  - [ ] Commit message: `docs(implement-skill): T007 mirror status-flip sub-procedure to .claude/ copy`.

### T008 — Annotate tasks-template.md (root + bundled assets) with Status ownership note

- **Status:** pending
- **Depends on:** T007
- **Files:**
  - modify: `templates/tasks-template.md`
  - modify: `src/aiadev/_assets/templates/tasks-template.md`
  - test: extend `tests/test_framework_artifacts.py` (or whichever existing test asserts the two template copies stay in sync) to require the new note in both files
- **Spec scenarios:** Story 3 sc1 (rule visible to maintainers), reinforces Story 1 sc1 by documenting the contract at the template layer.
- **Acceptance:**
  - [ ] A failing assertion is added first (red), then the template note (green) — both ride in this single commit per the project's existing pattern for template-sync tasks.
  - [ ] Both template copies carry an identical one-liner near the `Status` taxonomy comment, e.g. `<!-- 'Status' is owned by the implement skill: it flips pending → done as each task ships. Do not edit by hand. -->`.
  - [ ] The framework-artifacts test now passes; no other test regresses.
  - [ ] Commit message: `docs(tasks-template): T008 mark Status as implement-owned in both template copies`.

## Parallelization hints

- **Parallel group A (independent, no shared files):** T001, T003.
- **Serial:** everything else. T002 needs T001. T004 needs T002. T005 needs T003. T006 needs T004 + T005. T007 needs T006. T008 needs T007.

## Post-task checklist

After every task:

- [ ] Commit message references the task id.
- [ ] Status in this file flipped from `pending` to `done` (this is exactly the contract under construction; the agent running this session dogfoods it manually for T001–T008 since the contract lands in `SKILL.md` only at T006/T007).

After all tasks:

- [ ] Full test suite passes: `pytest`.
- [ ] Skill validators pass: `python scripts/validate_skills.py`.
- [ ] Markdown lint passes: `npx markdownlint-cli2 '**/*.md'`.
- [ ] `analyze` skill runs and reports no drift vs spec / plan.
- [ ] Hand off to `requesting-code-review`.
