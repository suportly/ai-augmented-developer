---
description: Test-first workflow, naming, and structure baseline for every stack.
alwaysApply: true
---

# Testing

The AI-Augmented Developer constitution (Article II) mandates test-first
development. This rule is the concrete version of that mandate.

## Process

1. Write the test **before** the implementation. Run it; it must fail
   for the right reason.
2. Write the minimum code to make the test pass.
3. Refactor with tests green.
4. Commit. One red → green → refactor cycle per commit.

Skipping step 1 is a constitutional violation. If you catch yourself
writing implementation first, stop and revert.

## What to test

- **Pure logic**: exhaustively. Include edge cases (empty, one element,
  max size, unicode, timezone boundaries).
- **I/O boundaries**: integration tests with a real database/filesystem
  for the happy path, plus the one failure that users actually hit.
- **Contracts**: every public API endpoint has at least one test that
  documents the response shape.

Do NOT write tests that:

- Assert implementation details (private method calls, internal state).
  The test breaks on refactor — that's a smell, not a safety net.
- Re-test the framework (Django auth, React rendering).
- Snapshot entire pages unless the snapshot is actively reviewed.

## Structure

- One test file per module under test, mirroring the source tree.
- Test names describe the scenario and the expected outcome:
  `test_returns_empty_list_when_user_has_no_orders`, not `test_orders`.
- Arrange / Act / Assert blocks separated by a blank line.
- No shared mutable state between tests. Use fixtures/factories, not
  module-level constants.

## Forbidden

- Mocking what you own. If you wrote the class, test it for real.
  Mock boundaries you don't control (third-party APIs, time, random).
- `time.sleep` in tests. Use freezegun / fake clock / poll-until.
- Tests that pass when disabled. Every assertion matters.
