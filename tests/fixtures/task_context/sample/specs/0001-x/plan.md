# Implementation plan: task-context sample fixture

**Branch:** `feature/x`
**Date:** 2026-05-13
**Spec:** [spec.md](./spec.md)
**Plan version:** 1
**Language:** en

---

## Summary

Plan slice fixture for `task-context` compose tests. Each Phase-1 task
gets its own block here so the helper can extract per-task plan slices.

## Phase breakdown

### Phase 1 — Wire the loaders

#### T001 — bootstrap repository scaffolding

- Notes: T001-plan-marker — sets up the test harness with no production code.
- Touches: tests only.

#### T002 — extend foo loader to satisfy Story 1

- Notes: T002-plan-marker — implementation lives in `src/foo.py`; the
  loader must return the canonical strings demanded by Story 1 sc1 and
  sc2 (sc3 is deferred to a follow-up).
- Risk: foo currently returns hardcoded values; the new behaviour must
  not regress callers in `tests/`.

#### T003 — emit bar from Story 2 trigger

- Notes: T003-plan-marker — creates `src/bar.py` from scratch; no
  existing file to modify.

## Constitution check

| Article | Applies? | Status |
|---|---|---|
| I. Spec-first | Yes | PASS |
| II. Test-first | Yes | PASS |
