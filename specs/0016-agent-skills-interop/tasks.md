# Tasks: agent-skills-interop

> Produced by the `tasks` skill from an approved `plan.md`. Consumed by `implement`.

**Branch:** `feature/agent-skills-interop`
**Plan:** [plan.md](./plan.md)
**Generated:** 2026-07-08
**Language:** en <!-- mirrors spec.md; write task descriptions in this language. -->

---

## How to read this file

- Tasks are ordered. `implement` runs them top-to-bottom.
- One task = one commit. The commit message starts with the task id.
- Each task links back to the spec acceptance scenarios it exercises.
- `Status` is one of: `pending`, `in_progress`, `blocked`, `done`. Owned by the `implement` skill — it flips `pending` → `done` inside each task's commit. Do not edit by hand; manual edits are overwritten on the next `implement` run.

## Task list

### T001 — agent-skills-interop

- **Status:** pending
- **Depends on:** — <!-- list task ids or dash for none -->
- **Files:**
  - create: `path/to/new.ext`
  - modify: `path/to/existing.ext`
  - test: `path/to/test.ext`
- **Spec scenarios:** Story 1 scenario 1, scenario 2
- **Acceptance:**
  - [ ] Failing test written and observed failing for the stated reason.
  - [ ] Minimum implementation makes the test pass.
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat(): T001 agent-skills-interop`.
- **Notes:**
  <!-- anything the implementer should know but isn't obvious from the files -->

### T002 — agent-skills-interop

- **Status:** pending
- **Depends on:** T001
- **Files:**
  - modify: `path/to/something.ext`
  - test: `path/to/test_something.ext`
- **Spec scenarios:** Story 1 scenario 3
- **Acceptance:**
  - [ ] ...

<!-- Add more tasks as needed. Keep the block structure consistent so
     `aiadev validate` can parse them. -->

## Parallelization hints

<!-- Tasks that do not share files can be attempted in parallel if the
     platform supports it. List the safe parallel groups here. Leave empty
     if the whole list is serial. -->

- Parallel group A: T00X, T00Y
- Serial: everything else

## Post-task checklist

After every task:

- [ ] Commit message references the task id.
- [ ] Status in this file updated.

After all tasks:

- [ ] Full test suite passes (``).
- [ ] `analyze` skill runs and reports no drift vs spec / plan.
- [ ] Hand off to `requesting-code-review` to open the PR.
