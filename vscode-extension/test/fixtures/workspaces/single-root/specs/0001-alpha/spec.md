# Feature specification: Alpha fixture

**Branch:** `feature/alpha-fixture`
**Created:** 2026-04-29
**Status:** Approved
**Spec ID:** 0001
**Language:** en

---

## Problem

Integration test fixture.

## Reconnaissance

Reconnaissance: not required (single-surface change: fixture)

## Users and stakeholders

- Test harness.

## Success criteria

- This file is parseable by the spec parser.

## Non-goals

- Nothing.

## User stories

### Story 1 — Fixture (P1)

As a test, I want to parse this fixture so that integration tests pass.

**Acceptance scenarios:**

1. Given this file exists, When parsed, Then the title is "Alpha fixture".
2. Given this file exists, When parsed, Then status is "approved".
3. Given this file exists, When parsed, Then specId is "0001".

## Clarifications

## Data touched

- None.

## Out-of-band effects

None.

## Open risks

- None.

## Traceability

- Originating issue: T029 integration test fixture
- Related specs: none
- Constitution articles invoked: none
