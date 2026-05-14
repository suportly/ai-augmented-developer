# Feature specification: orphan-branch fixture spec X

**Branch:** `feature/x`
**Created:** 2026-05-13
**Status:** Approved
**Spec ID:** 1
**Language:** en

---

<!-- section: Problem -->
## Problem

Placeholder problem statement; this spec belongs to `feature/x`.

<!-- section: Reconnaissance -->
## Reconnaissance

Reconnaissance: not required (single-surface change: fixtures)

<!-- section: Users and stakeholders -->
## Users and stakeholders

- Pipeline state detector tests.

<!-- section: Success criteria -->
## Success criteria

- Detector only inspects the spec matching the current git branch.

<!-- section: Non-goals -->
## Non-goals

- Real product behaviour.

<!-- section: User stories -->
## User stories

### Story 1 — Branch scoping (P1)

As a detector, I want to ignore specs belonging to other branches when reporting state.

**Acceptance scenarios**:

1. Given multiple specs and the current branch is `feature/x`, When the detector runs, Then it only reports `0001-x`.

<!-- section: Clarifications -->
## Clarifications

- None outstanding.

<!-- section: Data touched -->
## Data touched

- None.

<!-- section: Out-of-band effects -->
## Out-of-band effects

- None.

<!-- section: Open risks -->
## Open risks

- None.

<!-- section: Traceability -->
## Traceability

- Originating issue: n/a (fixture)
- Related specs: 0002-y
- Constitution articles invoked: II
