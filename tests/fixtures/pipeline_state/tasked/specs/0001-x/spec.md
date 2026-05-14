# Feature specification: tasked fixture

**Branch:** `feature/x`
**Created:** 2026-05-13
**Status:** Approved
**Spec ID:** 1
**Language:** en

---

<!-- section: Problem -->
## Problem

Placeholder problem statement for the tasked fixture.

<!-- section: Reconnaissance -->
## Reconnaissance

Reconnaissance: not required (single-surface change: fixtures)

<!-- section: Users and stakeholders -->
## Users and stakeholders

- Pipeline state detector tests.

<!-- section: Success criteria -->
## Success criteria

- Detector recommends `/aiadev:implement` when this fixture is loaded.

<!-- section: Non-goals -->
## Non-goals

- Real product behaviour.

<!-- section: User stories -->
## User stories

### Story 1 — Tasks ready, none done (P1)

As a detector, I want to recognise pending tasks so that the next step is `implement`.

**Acceptance scenarios**:

1. Given this fixture, When the detector runs, Then it recommends `/aiadev:implement`.

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
- Related specs: none
- Constitution articles invoked: II
