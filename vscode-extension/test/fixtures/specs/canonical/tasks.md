# Tasks: Canonical fixture

> Produced by the `tasks` skill from an approved `plan.md`. Consumed by `implement`.

**Branch:** `feature/canonical`
**Plan:** [plan.md](./plan.md)
**Generated:** 2026-04-28
**Language:** en

---

## How to read this file

- Tasks are ordered. `implement` runs them top-to-bottom.
- One task = one commit. The commit message starts with the task id.
- `Status` is one of: `pending`, `in_progress`, `blocked`, `done`.

## Task list

### T001 — Scaffold parser module

- **Status:** done
- **Depends on:** —
- **Files:**
  - create: `src/parser/tasks.ts`
- **Spec scenarios:** Story 2 scenario 1
- **Acceptance:**
  - [x] Failing test written.
  - [x] Implementation makes the test pass.

### T002 — Add status bullet recognition

- **Status:** in_progress
- **Depends on:** T001
- **Files:**
  - modify: `src/parser/tasks.ts`
- **Spec scenarios:** Story 2 scenario 2
- **Acceptance:**
  - [ ] Failing test written.
  - [ ] Implementation makes the test pass.

### T003 — Wire parser into provider

- **Status:** blocked
- **Depends on:** T002
- **Files:**
  - modify: `src/provider.ts`
- **Spec scenarios:** Story 2 scenario 3
- **Acceptance:**
  - [ ] Failing test written.

### T004 — Document parser API

- **Status:** pending
- **Depends on:** T003
- **Files:**
  - create: `docs/parser.md`
- **Spec scenarios:** Story 2 scenario 3
- **Acceptance:**
  - [ ] Documentation drafted.

## Parallelization hints

- Serial: everything.

## Post-task checklist

After every task:

- [ ] Commit message references the task id.
- [ ] Status in this file updated.
