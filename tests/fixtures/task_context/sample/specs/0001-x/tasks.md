# Tasks: task-context sample fixture

**Branch:** `feature/x`
**Plan:** [plan.md](./plan.md)
**Generated:** 2026-05-13
**Language:** en

---

## Task list

### T001 — bootstrap repository scaffolding

- **Status:** pending
- **Depends on:** —
- **Files:**
  - test: `tests/test_bootstrap.py`
- **Spec scenarios:** Story 1 sc1
- **Acceptance:**
  - [ ] Failing test written.
- **Notes:**
  Pure scaffolding.

### T002 — extend foo loader to satisfy Story 1

- **Status:** pending
- **Depends on:** T001
- **Files:**
  - modify: `src/foo.py`
  - test: `tests/test_foo.py`
- **Spec scenarios:** Story 1 sc1, sc2
- **Acceptance:**
  - [ ] Failing test in `tests/test_foo.py`.
  - [ ] `src/foo.py` returns the marker strings demanded by Story 1 sc1 and sc2.

### T003 — emit bar from Story 2 trigger

- **Status:** pending
- **Depends on:** T002
- **Files:**
  - create: `src/bar.py`
  - test: `tests/test_bar.py`
- **Spec scenarios:** Story 2 sc1
- **Acceptance:**
  - [ ] Failing test in `tests/test_bar.py`.
  - [ ] `src/bar.py` created.
