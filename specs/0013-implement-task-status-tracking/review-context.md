# Code Review Context: implement skill must mark tasks done in tasks.md (issue #33)

## What Was Built

Adds a tasks.md status-tracking contract to the `implement` skill so each per-task commit flips `**Status:** pending` → `**Status:** done` atomically. Lands a Python helper (`aiadev.tasks_status`) with parse/validate/mark_done plus 12 unit tests, rewrites step 5 of `skills/implement/SKILL.md` into a 9-step loop with explicit orchestrator ownership and rollback semantics, and pins the loop section against regression via a content-assertion test.

Also bundles a small unrelated fix (`vscode-extension/media/aiadev.svg` redrawn from the existing `icon.png` design — the previous SVG was a generic 18×18 rectangle).

## Spec Reference

- Spec: [specs/0013-implement-task-status-tracking/spec.md](./spec.md)
- Plan: [specs/0013-implement-task-status-tracking/plan.md](./plan.md)
- Tasks: [specs/0013-implement-task-status-tracking/tasks.md](./tasks.md) (T001–T006 all `Status: done`)
- Originating issue: https://github.com/suportly/ai-augmented-developer/issues/33

## Changed Files

```
 skills/implement/SKILL.md                          |  24 +++-
 specs/0013-implement-task-status-tracking/plan.md  | 152 +++
 specs/0013-implement-task-status-tracking/spec.md  | 122 +++
 specs/0013-implement-task-status-tracking/tasks.md |  97 +++
 src/aiadev/tasks_status.py                         | 137 +++
 templates/tasks-template.md                        |   2 +-
 tests/fixtures/tasks_md_samples/*.md  (5 files)    | 189 +++
 tests/test_implement_skill_drift.py                |  48 +++
 tests/test_tasks_status.py                         | 149 +++
 vscode-extension/media/aiadev.svg                  |  19 ++-
 14 files changed, 929 insertions(+), 10 deletions(-)
```

## Key Decisions Made

1. **Orchestrator owns the marker, not the implementer subagent** (clarify cl-1; plan ADR). Subagent prompt remains code-only; only the orchestrator reads/mutates `tasks.md`. Eliminates the failure mode where a subagent forgets the marker.

2. **Marker rides inside the per-task commit, not a separate commit** (plan ADR). `git add` task code + `tasks.md` together; rollback on commit failure via `git restore --staged tasks.md && git checkout -- tasks.md`. Preserves the "1 task = 1 commit" rule.

3. **`in_progress` is transient runtime state, never persisted** (clarify cl-2). On iteration start, an `in_progress` row is treated as `pending` and re-dispatched; partial-write recovery is out of scope.

4. **Strict prefix invariant for `done` ids** (clarify cl-3). The set of `done` task ids must form a contiguous prefix of declared task order; out-of-order halts with the verbatim error string from spec Story 2 sc2. No silent recovery — that is exactly the failure mode this feature exists to eliminate.

5. **Single-source-of-truth, not two-mirror drift** (mid-implementation course correction; plan ADR). `.claude/skills/` and `src/aiadev/_assets/skills/` are both gitignored — `aiadev sync` and `scripts/sync_assets.py` regenerate them. Story 3 sc2 was therefore reframed from byte-equality-between-mirrors to a single-source content assertion in `tests/test_implement_skill_drift.py` against `skills/implement/SKILL.md`. The course correction is documented in commit `48747da` and in the plan ADR.

6. **No e2e harness** (course correction). `aiadev.tools.implement` does not exist — `implement` is agent-driven prose, not Python code. The verification gap is documented under spec Open risks; enforcement decomposes into unit tests + content assertion + skill prose. Article IV evidence is the live `git show` output on this very branch (commits show the marker flip riding inside the task commit — Story 1 sc2 demonstrated dogfood-style).

## Areas Needing Attention

- **`src/aiadev/tasks_status.py` regex robustness.** `_TASK_HEADER_RE = r"^### (T\d{3,}) — (.+)$"` and `_STATUS_LINE_RE = r"^- \*\*Status:\*\* (\S+)\s*$"`. The header regex is anchored on the em-dash (—); a hand-edited `tasks.md` with an ASCII hyphen would not parse. Acceptable trade-off (the template enforces em-dash) but worth confirming the reviewer agrees.

- **`mark_done` rewrite preserves whitespace per-line but consumes any trailing whitespace on the status line.** Test golden-file diff confirms surrounding bytes are unchanged; trailing spaces on the original status line would be dropped. No real-world content has them.

- **Validation of out-of-order semantics.** `validate()` raises with the literal spec error string (`"ERROR: tasks.md inconsistency — T003 is done but T002 is pending. Fix tasks.md manually before resuming."`). The exact message is asserted verbatim by the unit test. Future spec edits to the message must update the test in lockstep.

- **Two T006 commits in history.** Renumbering happened mid-implementation when T004/T010 were dropped. The earlier `1ccb754` is what is now T005 in the corrected `tasks.md`; the later `9c3cd2e` is the current T006. Commit messages reflect the old numbers; the canonical record going forward is `tasks.md`. Acceptable, but if the reviewer wants a clean linear renumber I can squash + reword.

- **Pre-existing failures in `tests/test_mcp_server.py`.** 7 failures present on `main` before this branch, untouched by my changes. Verified by `git stash`-checking on the parent commit. They are pre-existing and out of scope.

## Test Coverage

- **Backend:** `pytest --ignore=tests/test_mcp_server.py` — **569 passed, 1 skipped** (skipped is pre-existing, gates on a future T013). The 12 unit tests in `tests/test_tasks_status.py` cover Story 1 sc2 + Story 2 sc1–sc4. The single test in `tests/test_implement_skill_drift.py` covers Story 3 sc1 + sc2.
- **Skill validators:** `python scripts/validate_skills.py` — exit 0; every SKILL.md OK.
- **Manual verification (Article IV evidence):** `git show 9c3cd2e -- specs/0013-implement-task-status-tracking/tasks.md` shows the diff `-**Status:** pending` / `+**Status:** done` riding inside the same commit as the `templates/tasks-template.md` edit — Story 1 sc2 demonstrated by the very branch under review.
- **Pre-existing failures:** `tests/test_mcp_server.py` (7 failures on `main`, unrelated, untouched by this branch).

## Self-review

- Comfortable showing this to the team? Yes. The course-correction commits (`48747da`) are conspicuous but honest — they document a real planning error caught mid-implementation rather than papered over.
- Anything I know is wrong? No.
- Security concerns? None — local file IO, no network, no PII, no secrets.
