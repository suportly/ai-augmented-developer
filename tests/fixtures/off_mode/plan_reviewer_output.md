ISSUES_FOUND

Blocking:

1. Task T010 declares a test that reads `benchmark/recorded/*.json` before those
   files exist. The failing-test precondition is structurally impossible.

2. The Constitution Check row for Article V says PASS but cites an "existing
   provider interface" that does not exist in this repository. Either introduce
   the interface in a task and mark it as a new create, or waive Article V with
   a Complexity Tracking row.

Non-blocking:

1. Phase 3 mentions `docs/pipeline-reference.md` as both generated and checked in
   without naming a regeneration trigger. A pre-commit hook or CI step would
   close the gap.
