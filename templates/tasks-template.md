# Tasks: {{FEATURE_NAME}}

**Branch:** `{{BRANCH}}`
**Plan:** [plan.md](./plan.md)
**Generated:** {{DATE}}
**Language:** {{DOC_LANGUAGE}} <!-- mirrors spec.md; write task descriptions in this language. -->

---

## How to read this file

- Tasks run top-to-bottom, one commit each, message starting with the task id.
- `Status` (`pending`, `in_progress`, `blocked`, `done`) is owned by `implement`.

## Task list

### T001 — {{SHORT_TITLE}}

- **Status:** pending
- **Depends on:** — <!-- list task ids or dash for none -->
- **Files:**
  - create: `path/to/new.ext`
  - modify: `path/to/existing.ext`
  - test: `path/to/test.ext`
- **Spec scenarios:** Story 1 scenario 1, scenario 2 <!-- `Story N scenario M, scenario K`; `;` splits stories; `Story N` = whole story; infra: `Success criterion #N`; bare dash = error -->
- **Acceptance:**
  - [ ] Failing test written and observed failing for the stated reason.
  - [ ] Minimum implementation makes the test pass.
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat({{AREA}}): T001 {{SHORT_TITLE}}`.
- **Notes:**

### T002 — {{SHORT_TITLE}}

- **Status:** pending
- **Depends on:** T001
- **Files:**
  - modify: `path/to/something.ext`
  - test: `path/to/test_something.ext`
- **Spec scenarios:** Story 1 scenario 3
- **Acceptance:**
  - [ ] ...

## Parallelization hints

- Parallel group A: T00X, T00Y; the rest serial

## Post-task checklist

After every task: commit references the task id; status updated.

After all tasks:

- [ ] Full test suite passes (`{{TEST_COMMAND}}`).
- [ ] `analyze` skill runs and reports no drift vs spec / plan.
- [ ] Hand off to `requesting-code-review` to open the PR.
