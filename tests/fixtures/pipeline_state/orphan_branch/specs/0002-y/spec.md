# Feature specification: orphan-branch fixture spec Y

**Branch:** `feature/y`
**Created:** 2026-05-13
**Status:** Approved
**Spec ID:** 2
**Language:** en

---

<!-- section: Problem -->
## Problem

Placeholder problem statement; this spec belongs to `feature/y` and should be skipped when the active branch is `feature/x`.

<!-- section: Reconnaissance -->
## Reconnaissance

Reconnaissance: not required (single-surface change: fixtures)

<!-- section: Users and stakeholders -->
## Users and stakeholders

- Pipeline state detector tests.

<!-- section: Success criteria -->
## Success criteria

- Detector ignores this spec when the active branch is `feature/x`.

<!-- section: Non-goals -->
## Non-goals

- Real product behaviour.

<!-- section: User stories -->
## User stories

### Story 1 — Branch scoping companion (P1)

As a detector, I want to confirm I do not bleed information across branches.

**Acceptance scenarios**:

1. Given the active branch is `feature/x`, When the detector runs, Then this spec is excluded.

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
- Related specs: 0001-x
- Constitution articles invoked: II
