# Tasks: tasked fixture

**Branch:** `feature/x`
**Plan:** [plan.md](./plan.md)
**Generated:** 2026-05-13
**Language:** en

---

## How to read this file

- Tasks are ordered. `implement` runs them top-to-bottom.
- One task = one commit. The commit message starts with the task id.
- `Status` is one of: `pending`, `in_progress`, `blocked`, `done`.

## Task list

### T001 — first fixture task

- **Status:** pending
- **Depends on:** —
- **Files:**
  - create: `placeholder.txt`
- **Spec scenarios:** Story 1 scenario 1
- **Acceptance:**
  - [ ] Failing test written.
  - [ ] Implementation makes it pass.
- **Notes:**
  Fixture only.

### T002 — second fixture task

- **Status:** pending
- **Depends on:** T001
- **Files:**
  - modify: `placeholder.txt`
- **Spec scenarios:** Story 1 scenario 1
- **Acceptance:**
  - [ ] Failing test written.

## Parallelization hints

- Serial: T001, T002

## Post-task checklist

After every task:

- [ ] Commit message references the task id.
- [ ] Status in this file updated.
