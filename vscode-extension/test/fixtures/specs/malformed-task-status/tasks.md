# Tasks: Malformed status fixture

> Regression guard for T009 — only the offending task gets `unknown`,
> the parser does not throw, and the surrounding tasks keep their valid
> statuses.

**Branch:** `feature/malformed-task-status`
**Plan:** [plan.md](./plan.md)
**Generated:** 2026-04-28
**Language:** en

---

## Task list

### T001 — Valid done task

- **Status:** done
- **Depends on:** —
- **Files:**
  - create: `src/a.ts`
- **Spec scenarios:** Story 2 scenario 1
- **Acceptance:**
  - [x] Failing test written.

### T002 — Bogus status task

- **Status:** Bogus
- **Depends on:** T001
- **Files:**
  - modify: `src/b.ts`
- **Spec scenarios:** Story 2 scenario 2
- **Acceptance:**
  - [ ] Failing test written.

### T003 — Valid pending task

- **Status:** pending
- **Depends on:** T002
- **Files:**
  - create: `src/c.ts`
- **Spec scenarios:** Story 2 scenario 3
- **Acceptance:**
  - [ ] Failing test written.
