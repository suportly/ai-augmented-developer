# Code Review Context — 0010-pipeline-preflight-checks

## What was built

A read-only `aiadev preflight` checker (Python module + Click subcommand) that verifies upstream artifacts before any pipeline skill runs. Same code path is invoked by the seven pipeline `SKILL.md` Preconditions sections and by CI, so the diagnostics are byte-identical. `finishing-a-branch` now requires `.aiadev/review.yaml` recording `status: approved`.

## Spec / plan / tasks

- Spec — [specs/0010-pipeline-preflight-checks/spec.md](./spec.md)
- Plan — [specs/0010-pipeline-preflight-checks/plan.md](./plan.md) (Constitution Check clean, no waivers)
- Tasks — [specs/0010-pipeline-preflight-checks/tasks.md](./tasks.md) (28 tasks across 4 phases)

## Files added / modified (PR-scope diff)

```text
src/aiadev/preflight.py                       (new, 232 lines)
src/aiadev/commands/preflight.py              (new, 87 lines)
src/aiadev/cli.py                             (modified — registers subcommand)
tests/test_preflight.py                       (new, 477 lines — 22 unit tests)
tests/test_preflight_pipeline.py              (new, 150 lines — E2E + 500ms perf)
tests/test_preflight_requirements_coverage.py (new, 90 lines — drift guard)
tests/fixtures/preflight/reference/{spec,plan,tasks}.md (new fixture)
skills/clarify/SKILL.md                       (preflight call-out)
skills/plan/SKILL.md                          (preflight call-out)
skills/tasks/SKILL.md                         (preflight call-out)
skills/implement/SKILL.md                     (preflight call-out)
skills/analyze/SKILL.md                       (preflight call-out)
skills/requesting-code-review/SKILL.md        (review.yaml emission)
skills/finishing-a-branch/SKILL.md            (preflight + review gate)
docs/articles/preflight.md                    (new — migration article)
CHANGELOG.md                                  ([Unreleased] block: Added / Changed / Breaking)
```

`git diff main...HEAD --stat`: 21 files changed, 1950 insertions, 2 deletions.

## Key decisions (ADRs from plan)

1. **Single entry point** (`aiadev.preflight.check`) shared by CLI and in-skill call-outs — guarantees byte-identical diagnostics.
2. **Static `REQUIREMENTS` table** keyed by skill name, not derived from SKILL.md frontmatter — frontmatter `inputs:` are templates, not machine-checkable rules. Kept in sync by `test_preflight_requirements_coverage.py`.
3. **Pinned anchor lists** (`SPEC_ANCHORS` literal) instead of parsing the live template at runtime — deterministic across framework versions; round-tripped against the template by a coverage test.
4. **`.aiadev/review.yaml` lives at repo root** (not under `specs/<slug>/`) — matches the spec's Breaking-Changes wording verbatim.
5. **`AIADEV_PREFLIGHT=warn`** downgrades the abort but not the message format — CI tailing stderr can switch modes without re-parsing.

## Test coverage

- **22 unit tests** in `tests/test_preflight.py` map 1-1 to spec acceptance scenarios (Story 1 sc1-6, Story 2 sc1-3, Story 3 sc1-3, plus auxiliary CLI cases).
- **8 E2E parametrised cases** in `tests/test_preflight_pipeline.py` cover spec Success criterion #5 (deleting any prior-stage artifact fails the next skill).
- **500 ms performance budget** asserted on the reference fixture (Success criterion #3).
- **Drift guards** in `tests/test_preflight_requirements_coverage.py`: every `PIPELINE_SKILLS` entry has a `skills/<name>/SKILL.md`; every anchor list round-trips against its template; every wired SKILL.md contains the literal `aiadev preflight <skill> --feature` callout.

## Test plan (commands)

```bash
python -m pytest tests/test_preflight.py tests/test_preflight_pipeline.py tests/test_preflight_requirements_coverage.py
# expected: 38 passed
python -m pytest --tb=no -q
# expected: 546 passed; 7 pre-existing MCP failures unrelated to this branch
python -m aiadev preflight --all
# expected: exit 0 on the reference fixture; the in-flight 0010 dir passes
```

## Areas needing reviewer attention

- The `_strip_numeric_prefix` / branch-matching logic accepts both `feature/<slug-without-prefix>` and `feature/<slug-with-prefix>` to match the slug. Confirm this is the intended ergonomic choice; the spec is silent on which form is canonical.
- `src/aiadev/preflight.py` shells out to `git rev-parse --abbrev-ref HEAD` via `subprocess.run` with a fixed argument list (no shell, no user input). The injected `current_branch` callable lets unit tests bypass it.
- `_should_abort` only treats the literal `warn` as a downgrade; any other unrecognised value (including `abort`) keeps the default abort behaviour. This differs slightly from the existing `aiadev.config.resolve_terse_mode` which raises on unknown values — kept lenient here so CI debugging never crashes.

## Pre-existing unrelated failures

`tests/test_mcp_server.py` has 7 failures on this branch. Verified independent of this work by stashing my changes — main pre-merge already produces the same failures. They will be addressed in a separate PR.

## Constitution check

All seven articles either PASS (I, II, III, IV, VI) or N/A (V — no provider, VII — no adapted material). No waivers; Complexity Tracking table empty.
