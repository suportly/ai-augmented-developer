# Code Review Context: `aiadev metrics` (spec 0015)

## What Was Built

A new `aiadev metrics` CLI subcommand that aggregates the audit trail
already produced by every pipeline run (`specs/<branch>/.review-log.jsonl`
from spec 0014, `tasks.md` statuses, `spec.md` headers, and `git log`)
and emits structured indicators in either human-readable text or
stable JSON. Read-only, single-repo MVP, no network. The point is to
make the evidence the framework already collects visible to a tech
lead without forcing a file-by-file scan.

## Spec Reference

- Spec: [specs/0015-aiadev-metrics/spec.md](spec.md)
- Plan: [specs/0015-aiadev-metrics/plan.md](plan.md)
- Tasks: [specs/0015-aiadev-metrics/tasks.md](tasks.md)

All six `[NEEDS CLARIFICATION:cl-N]` markers resolved during `clarify`;
their resolution rationale is preserved inline in the spec. Plan's
Constitution Check is 7/7 (no FAIL, no waivers).

## Changed Files

```text
 CHANGELOG.md                                       |  16 +
 README.md                                          |  29 ++
 docs/metrics.md                                    |  84 ++++
 specs/0015-aiadev-metrics/plan.md                  | 160 +++++++
 specs/0015-aiadev-metrics/spec.md                  | 129 ++++++
 specs/0015-aiadev-metrics/tasks.md                 | 247 ++++++++++
 src/aiadev/cli.py                                  |   2 +
 src/aiadev/commands/metrics.py                     | 220 +++++++++
 src/aiadev/metrics.py                              | 509 +++++++++++++++++++
 src/aiadev/metrics_format.py                       | 191 ++++++++
 tests/fixtures/metrics/...                         |  68 +
 tests/test_attribution_and_changelog.py            |  39  ← drift-fix
 tests/test_metrics.py                              | 468 +++++++++++++++++
 tests/test_metrics_command.py                      | 243 ++++++++++
 tests/test_metrics_docs.py                         |  52 +++
 tests/test_metrics_fixtures.py                     | 115 +++++
 tests/test_metrics_format.py                       | 129 ++++++
 29 files changed, 2731 insertions(+), 11 deletions(-)
```

## Key Decisions Made

Tracked in detail in [plan.md](plan.md) as ADRs 1-7. The ones most
worth scrutinising:

1. **ADR-1: split core (`metrics.py`) from CLI (`commands/metrics.py`)**.
   Mirrors the established `review_log.py` ↔ `commands/preflight.py`
   pattern. Lets tests target the core without spawning a Click
   runner.

2. **ADR-3: time window filters on the `spec.md` `Created:` header,
   not git commit timestamps**. Git timestamps drift under
   rebase/cherry-pick; the spec's `Created:` is declared by `specify`
   and stable. This is what gives the determinism property the spec
   asks for (Story 2 sc3).

3. **ADR-6: "first-pass APPROVED" is inferred from chronological
   order, no schema change to the JSONL entry**. JSONL is append-only
   in dispatch order. The trade-off: if the orchestrator ever
   re-dispatches out-of-order (not the case today), the cl-6
   inference becomes wrong and a `attempt_number` field becomes
   necessary.

4. **ADR-7: exit-code policy**. `0` ok (even when `coverage=0%`),
   `1` parse error or feature not found, `2` no data in window OR
   pre-cutoff (spec id ≤ 10) feature without trail. The pre-cutoff
   constant `10` is mirrored from `schemas/spec-recon.schema.json`
   as `_PRE_CUTOFF_LAST_SPEC_ID` in `commands/metrics.py` — small
   duplication chosen over a runtime JSON-schema dependency for a
   single integer.

5. **Privacy default (cl-3): contagens-only**. Reviewer prose (`note`
   field) is omitted from both `text` and `json` output unless the
   user passes `--show-bodies`. Article VI compliance by inversion
   of default.

## Areas Needing Attention

Listing what I think deserves a careful look — not because I have
doubts, but because these are the spots where a reviewer can catch
something I missed:

1. **`first_pass_rate_by_reviewer` in [src/aiadev/metrics.py](../../src/aiadev/metrics.py)**
   — The grouping key for `task_id == "branch-review"` collapses to
   per-reviewer (no task component) so that two consecutive branch-level
   reviews from the same reviewer don't double-count. Worth verifying
   the helper does not accidentally double-count when a reviewer
   re-runs on the same task.

2. **`specify_to_last_commit_days` in [src/aiadev/metrics.py](../../src/aiadev/metrics.py)**
   — Parses `git log -p --name-only` output by walking line-by-line.
   I tested with two synthetic commits; production `git log` output
   includes lines I might be ignoring (merge commit headers,
   `Author:` lines without trailing `Date:`). Reader resilience to
   real-world git log shapes is the question.

3. **`_collect_git_log` exit-code-resilience in
   [src/aiadev/commands/metrics.py](../../src/aiadev/commands/metrics.py)**
   — A failed git subprocess returns `""`, which makes git-derived
   metrics degrade to `None`. Intentional, but verify the CLI never
   crashes on a non-git directory (the smoke run I did is inside the
   real repo).

4. **Determinism guard in
   [tests/test_metrics_format.py::test_json_deterministic_for_same_input](../../tests/test_metrics_format.py)**
   — runs `build_report` twice and byte-compares. Confirms ADR-3
   actually holds. If you can spot any source of non-determinism
   (dict iteration order, default `today()` leaking in), that test
   should have failed but did not — worth a look.

5. **Drift fix in
   [tests/test_attribution_and_changelog.py](../../tests/test_attribution_and_changelog.py)**
   — Not feature work, strictly. The helper
   `_most_recent_changes_block` failed because my CHANGELOG edit
   added `[Unreleased]` content alongside the still-relevant 0.19.0
   release block. New helper concatenates both when both have content;
   the original "freshly cut release" case still works because the
   loop breaks after the first non-empty released block. Mentally
   simulate the test under both scenarios to confirm.

## Test Coverage

- **Backend (Python)**: `pytest --ignore=tests/test_mcp_server.py`
  all green. 68 new tests across 5 files. Existing test count
  unchanged.
- **Test command actually run** (post-amend, on the squashed commit):
  ```bash
  .venv/bin/pytest --ignore=tests/test_mcp_server.py -q
  # → 0 failures, 3 unrelated skips, ~250 tests collected.
  ```
- **markdownlint**: `npx markdownlint-cli2 docs/metrics.md README.md
  CHANGELOG.md specs/0015-aiadev-metrics/*.md` → 0 errors. Note that
  `tests/test_mcp_server.py` failures (7) are pre-existing — they
  require the `[mcp]` extra which is not installed.
- **Smoke run** of the feature against itself (best test of the
  end-to-end wiring):
  ```bash
  .venv/bin/python -m aiadev metrics --feature 0015-aiadev-metrics
  → exit 0, "review trail: vazio (feature ainda no estágio de implement
                                   ou pré-cutoff)"
  ```

## What I Did Differently From the Default `implement` Flow

Two declared departures from the canonical pipeline, both authorised
by the user before they were taken:

1. **No subagent per task during `implement`.** The skill prescribes
   one fresh subagent + two reviewer subagents per task (~42 dispatches
   for 14 tasks). For a feature whose 14 tasks all live in one
   tightly-coupled module set, and where the orchestrator already
   holds the full design context, fresh-subagent isolation gives
   little. I ran the tasks sequentially in the main session, TDD per
   task (test red → impl → green → next), and flipped `tasks.md`
   statuses as the work landed.

2. **One commit for the whole feature.** User directive. The
   `implement` skill normally commits per task (status flip + code +
   tasks.md in one atomic commit per task, so crash recovery works
   between commits). The user signalled the feature is conceptually
   one unit and asked for one commit on the branch. Done — see
   [commit 1694a20](./).

Both departures are noted in the commit body.
