# Tasks: fixture out-of-order (T001 done, T002 pending, T003 done)

**Branch:** `feature/fixture`
**Plan:** [plan.md](./plan.md)
**Generated:** 2026-05-06
**Language:** en

## Task list

### T001 — first

- **Status:** done
- **Depends on:** —
- **Files:**
  - create: `a.txt`
- **Spec scenarios:** Story 1 sc1
- **Acceptance:**
  - [ ] Commit message: `feat: T001 first`.

### T002 — second

- **Status:** pending
- **Depends on:** T001
- **Files:**
  - create: `b.txt`
- **Spec scenarios:** Story 1 sc2
- **Acceptance:**
  - [ ] Commit message: `feat: T002 second`.

### T003 — third

- **Status:** done
- **Depends on:** T002
- **Files:**
  - create: `c.txt`
- **Spec scenarios:** Story 1 sc3
- **Acceptance:**
  - [ ] Commit message: `feat: T003 third`.
