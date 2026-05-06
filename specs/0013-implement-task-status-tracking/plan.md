# Implementation plan: implement skill must mark tasks done in tasks.md

> Produced by the `plan` skill from an approved `spec.md`. This file describes **how** the spec will be realized. Do not rewrite `spec.md` into `plan.md`.

**Branch:** `feature/implement-task-status-tracking`
**Date:** 2026-05-06
**Spec:** [spec.md](./spec.md)
**Plan version:** 1
**Language:** en

---

## Summary

We add a tasks.md status-tracking contract to the `implement` skill. The orchestrator (the agent following the skill prose) (a) reads `tasks.md` at iteration start, refusing to proceed if any `### TNNN` block has a malformed `**Status:**` line or if the set of `done` ids does not form a contiguous prefix; (b) skips tasks already marked `done`; (c) writes `**Status:** pending` → `**Status:** done` on the active task immediately before staging the per-task commit, so the marker rides inside the same commit as the code change. The change lands in `skills/implement/SKILL.md` (the single tracked source of truth — `.claude/skills/` and `src/aiadev/_assets/skills/` are both gitignored, regenerated downstream by `aiadev sync` and `scripts/sync_assets.py` respectively) plus a small Python helper module under `src/aiadev/` that owns the parse/validate/mutate logic and is exercised exhaustively by unit tests. A pytest content assertion guards the loop section against accidental regression. No new external dependency, no new configuration flag. Note: there is no `aiadev.tools.implement` Python entry point — `implement` is agent-driven prose, not code — so this feature ships no end-to-end pipeline test; agent adherence to the prose is enforced by the contract being explicit in `SKILL.md` (see spec Open risks for the verification gap).

## Technical context

| Field | Value |
|---|---|
| Active preset | `framework-self` (this repo *is* the AI-Augmented Developer framework; no Django/React preset applies) |
| Language / runtime | Python 3.11+ (existing `aiadev` CLI), plus Markdown (skill + template files) |
| Primary dependencies | `click`, `pyyaml`, `jsonschema`, `rich` (already in `pyproject.toml`); no new deps |
| Storage | Local filesystem only — `specs/<branch>/tasks.md` |
| Testing framework | `pytest` 8.x with `pytest-asyncio`; existing fixtures in `tests/fixtures/` and fake LLM in `tests/_fakes/` |
| Target platform(s) | Linux/macOS dev shells; Python ≥ 3.11 |
| Performance budget | N/A — file edits on small markdown files (<10 KB typical); parse + mutate well under 100 ms |
| Security considerations | No secrets, no network. The `tasks.md` writer must reject path traversal in branch names and reject regex meta-characters in task ids before composing the substitution (defensive even though task ids are constrained to `T\d{3,}`). |

## Constitution check

| Article | Applies? | Status | Evidence |
|---|---|---|---|
| I. Spec-first | Yes | PASS | `spec.md` approved 2026-05-06; zero `[NEEDS CLARIFICATION]` markers (3 resolved in clarify pass). |
| II. Test-first | Yes | PASS | Phase 1 lands the parse/validate test fixtures and red unit + drift-import tests before any skill prose or helper code. Each task in `tasks.md` will start with a red test commit per the `tasks` skill contract. |
| III. Simplicity | Yes | PASS | One helper module (`src/aiadev/tasks_status.py`), no new abstraction layer, no provider interface, no config flag. We add only the minimum API the unit tests demand. No e2e harness is built — verification at the agent-adherence layer is documented as an Open risk in the spec rather than papered over with synthetic test infrastructure. |
| IV. Evidence over claims | Yes | PASS | Phase 4 specifies the exact pytest and validator invocations for the PR's test plan; no claims rest on machinery that does not exist. |
| V. Provider pattern | No | N/A | No external network boundary introduced. Filesystem access is in-process. |
| VI. Privacy by design | No | N/A | No PII, no logs, no new model fields. `tasks.md` is project-public by definition. |
| VII. Attribution | No | N/A | No adapted material from another project. `CREDITS.md` unchanged. |

Complexity tracking is empty — no waivers requested.

## Architecture decisions

- **Decision: Orchestrator owns the `Edit`, not the implementer subagent.**
  Rationale: clarify cl-1 — keeps the subagent prompt narrow (code + tests only) and gives the resume guard a single owner. A malformed subagent cannot "forget" the marker because the marker is no longer the subagent's responsibility.
  Trade-offs: orchestrator code has one more responsibility; bug here would mean no marker even with a green commit. Mitigated by the e2e test in Phase 4.

- **Decision: marker `Edit` happens *before* `git add`/`git commit`, inside the same commit as the code change.**
  Rationale: keeps the "1 task = 1 commit" rule (existing skill non-negotiable). A separate marker-only commit would double the commit count and pollute `git log`.
  Trade-offs: if the commit fails (hook rejection), the orchestrator must roll back the marker edit before retrying. Implemented as a `try/except` around the commit step that restores the file from `git checkout -- tasks.md` on failure.

- **Decision: `in_progress` is a transient runtime state, never persisted.**
  Rationale: clarify cl-2 + Story 2 scenario 4 — at iteration start we treat any `in_progress` value as `pending` and re-dispatch. This avoids reasoning about partial-write recovery, which would be a real concurrency layer for no benefit (the orchestrator is single-threaded per feature).
  Trade-offs: a developer who manually annotated `in_progress` before invoking `implement` will have their annotation overwritten. Acceptable — that field belongs to `implement`.

- **Decision: prefix invariant for `done` ids.**
  Rationale: clarify cl-3 — the resume guard's correctness rule is "the set of `done` task ids forms a contiguous prefix of the declared task order." Anything else means human edit + state drift, and silent recovery would re-introduce the issue #33 failure mode.
  Trade-offs: a developer who skipped a task on purpose (`T002 done, T003 skipped, T004 done`) cannot be expressed. That is by design — there is no "skipped" state in the taxonomy and adding one is out of scope.

- **Decision: there is one tracked copy of `implement/SKILL.md`, not two.**
  Rationale: investigation during plan execution confirmed that `.claude/skills/` (per-developer) and `src/aiadev/_assets/skills/` (build artefact regenerated by `scripts/sync_assets.py`) are both gitignored. The notion of "two skill copies must stay aligned" was based on a wrong premise — there is only one tracked source. Story 3 sc2 is therefore reframed as a single-source content assertion (Story 3 sc1 phrased as a CI-run pytest check) rather than a byte-equality drift check between non-existent siblings.
  Trade-offs: a developer who hand-edits the gitignored `.claude/` copy after `aiadev sync` will see their local edit overwritten on the next sync. That is exactly what `aiadev sync` is supposed to do; not a regression.

- **Decision: `tasks.md` is staged inside the same `git add` as the task's code files but the rollback path uses `git restore --staged && git checkout`.**
  Rationale: the simpler "leave unstaged until commit succeeds" alternative would require either a `git commit` with explicit pathspec (fragile against partial-add hooks) or a post-commit amend (forbidden by skill rules). Staging together keeps the commit-formation step a single command. The two-step rollback is a small, well-understood git idiom.
  Trade-offs: the rollback sequence has two commands instead of one. Acceptable. Documented inline in the orchestrator step so a maintainer reading the skill sees the exact recovery commands.

- **Decision: Story 3 contract is enforced by a content assertion in `tests/test_implement_skill_drift.py`, not by a `validate_skills.py` extension.**
  Rationale: the original plan extended `scripts/validate_skills.py` to compare two skill copies. With the single-source reality (above ADR), the natural enforcement layer is pytest — it already runs in CI on every push, and a content assertion ("the loop section must contain these phrases") is the right shape. No new validator, no new CI step; reuse the existing test layer.
  Trade-offs: a content assertion is looser than a hash comparison — a maintainer could rephrase around the required phrases without breaking the test. Mitigated by anchoring on operationally-load-bearing phrases (the literal git rollback commands, the exact `**Status:**` strings) that have no synonyms.

- **Decision: Python helper module location — `src/aiadev/tasks_status.py`.**
  Rationale: parallels the existing `src/aiadev/preflight.py` and `src/aiadev/validate.py`. Keeps the `aiadev` package as the single home for skill-orchestration logic the Python tests can import directly.
  Trade-offs: the orchestrator (which runs as a Claude subagent) does not call this module today — it calls `Edit` directly through Claude tools. The module exists for the Python tests and (future) for `aiadev preflight` to share the same parse/validate logic. We accept the duplication risk and address it by having both code paths consume the same regex constant.

## Project structure changes

```text
specs/0013-implement-task-status-tracking/spec.md         (existing — approved)
specs/0013-implement-task-status-tracking/plan.md         (new — this file)
specs/0013-implement-task-status-tracking/tasks.md        (next skill)

skills/implement/SKILL.md                                 (modified — add explicit status-flip step + idempotency guard; single tracked source)

src/aiadev/tasks_status.py                                (new — parse, validate, mutate)
templates/tasks-template.md                               (modified — add a one-line note that `Status` is mutated by `implement`)

tests/test_tasks_status.py                                (new — unit tests for parse/validate/mutate)
tests/test_implement_skill_drift.py                       (new — content assertion on the implement skill loop section)
tests/fixtures/tasks_md_samples/                          (new — golden-file inputs: clean, malformed, out-of-order, in-progress, all-done)
```

No file removals.

## Phase breakdown

### Phase 1 — Test fixtures and red tests

Lay down the failing tests *before* any implementation prose or helper code, per Article II. Each scenario family lands in the test file that actually exercises it.

- Fixture files under `tests/fixtures/tasks_md_samples/` covering: a clean 3-task list, a malformed (`Status:` missing) list, an out-of-order (`done, pending, done`) list, an `in_progress` mid-list, and an all-`done` list (resume short-circuit case).
- **Story 1 + Story 2 → unit tests.** A red unit test in `tests/test_tasks_status.py` enumerating Story 1 and Story 2 acceptance scenarios as `parametrize` rows. The import of `aiadev.tasks_status` is expected to fail (module not yet present) — that is the right red.
- **Story 3 → content assertion, red in this phase.** A red `tests/test_implement_skill_drift.py` that asserts the `## The loop` section of `skills/implement/SKILL.md` contains the literal status-flip phrases (`**Status:** pending`/`**Status:** done`, the `git restore --staged tasks.md && git checkout -- tasks.md` rollback, the word `orchestrator`). The assertion is red today because the wording lands in Phase 2, and goes green when the skill prose is updated.

### Phase 2 — Helper module + skill prose

Make all red tests green.

- Implement `src/aiadev/tasks_status.py` with: `parse(path) -> list[TaskRow]`, `validate(rows) -> None | raises TasksMdError`, `mark_done(path, task_id) -> None`. Each function has the minimum signature the unit tests demand; nothing speculative. After this lands, `tests/test_tasks_status.py` is green.
- Replace step 5 of `skills/implement/SKILL.md` with the numbered sub-procedure `(a)–(d)` (orchestrator owns `tasks.md` reads/mutates; flip status; `git add` task code + `tasks.md`; rollback on commit failure with `git restore --staged tasks.md && git checkout -- tasks.md`). After this lands, `tests/test_implement_skill_drift.py` is green and Story 3 sc1 + sc2 are satisfied.

### Phase 3 — Template note

Document the contract at the template layer for spec authors who never read the skill source.

- Add a one-liner to `templates/tasks-template.md` near the `Status` taxonomy comment noting that the field is owned by `implement` and not edited by hand. (`src/aiadev/_assets/templates/` is gitignored, regenerated by `scripts/sync_assets.py` before build — no separate edit needed.)

### Phase 4 — Verification

- Run the full `pytest` suite — confirm green, paste the summary into the PR test plan.
- Run `python scripts/validate_skills.py` — exit 0 (drift check passes; the two `implement/SKILL.md` copies are aligned).
- Run the project's markdown lint (`npx markdownlint-cli2 '**/*.md'`) — confirm clean.
- Dogfood verification (manual, written into the PR test plan): on this very feature's `tasks.md`, the agent (running this `/aiadev:implement` session) is itself the first consumer of the new contract — every task in this branch ships with its `**Status:**` line flipped to `done` inside the same commit as the code change, and `git show` on each commit demonstrates Story 1 sc2 directly. Paste one such `git show --stat` output into the PR test plan as Article IV evidence.
- Hand off to `requesting-code-review`.

## Risks and mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Orchestrator marker `Edit` succeeds but `git commit` fails (hook rejection) | Med | Med | Wrap commit step in try/except: on failure, `git restore --staged tasks.md && git checkout -- tasks.md` to restore the pre-edit state, then surface the hook error to the user. |
| Existing in-flight features in consumer projects (where `tasks.md` carries pre-issue-#33 inconsistencies) start failing the new prefix invariant | Med | Med | The error message names the file and the inconsistency; consumers fix manually with the `sed` workaround already documented in issue #33. Changelog will call this out. |
| Implementer subagent prompt confusion if maintainers later try to also list `tasks.md` in "Files to modify" | Low | Low | The skill text explicitly states the orchestrator owns the marker; the implementer prompt does **not** list `tasks.md`. Reviewer subagent will reject any plan that proposes otherwise. |
| Content-assertion in `test_implement_skill_drift.py` becomes a regression magnet (every loop reword needs a test update) | Low | Low | The required phrases are the operationally load-bearing ones (literal git rollback commands, exact `**Status:**` strings); they have no synonyms. Cosmetic prose changes won't trip the test. |

## Complexity tracking

> Required when any Constitution Check row is `FAIL`. Empty table if no waivers.

| Article waived | Reason | Alternatives considered | Reviewer |
|---|---|---|---|
| | | | |

## Hand-off to `tasks`

The next skill is `tasks`. It consumes this plan and produces `tasks.md`.
Pre-conditions before hand-off:

- [x] Constitution Check is fully populated, no blank rows.
- [x] Complexity tracking is filled or empty-and-justified (empty — no waivers).
- [x] Project structure delta is accurate.
