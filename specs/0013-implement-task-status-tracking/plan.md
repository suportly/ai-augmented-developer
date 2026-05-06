# Implementation plan: implement skill must mark tasks done in tasks.md

> Produced by the `plan` skill from an approved `spec.md`. This file describes **how** the spec will be realized. Do not rewrite `spec.md` into `plan.md`.

**Branch:** `feature/implement-task-status-tracking`
**Date:** 2026-05-06
**Spec:** [spec.md](./spec.md)
**Plan version:** 1
**Language:** en

---

## Summary

We add a tasks.md status-tracking contract to the `implement` skill. The orchestrator (the agent following the skill prose) (a) reads `tasks.md` at iteration start, refusing to proceed if any `### TNNN` block has a malformed `**Status:**` line or if the set of `done` ids does not form a contiguous prefix; (b) skips tasks already marked `done`; (c) writes `**Status:** pending` → `**Status:** done` on the active task immediately before staging the per-task commit, so the marker rides inside the same commit as the code change. The change lands in two skill markdown files (`skills/implement/SKILL.md` and the `.claude/skills/implement/SKILL.md` mirror) plus a small Python helper module under `src/aiadev/` that owns the parse/validate/mutate logic and is exercised exhaustively by unit tests. A CI drift-check (extension to `scripts/validate_skills.py`) keeps the two skill copies aligned. No new external dependency, no new configuration flag. Note: there is no `aiadev.tools.implement` Python entry point — `implement` is agent-driven prose, not code — so this feature ships no end-to-end pipeline test; agent adherence to the prose is enforced by the contract being explicit in `SKILL.md` (see spec Open risks for the verification gap).

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

- **Decision: Story 3 scenario 3 ("the per-task dispatch contract references the status-mutation step") is satisfied by the `implement` skill edit alone — there is no separate `subagent-driven-development` file.**
  Rationale: spec Reconnaissance records that `skills/subagent-driven-development/SKILL.md` was merged into `implement` and no longer exists on disk. The per-task dispatch contract now lives entirely inside `skills/implement/SKILL.md` (and its `.claude/` mirror), so updating the loop section there *is* the sc3 fulfilment — there is no second file that could disagree.
  Trade-offs: a future maintainer who restores a separate dispatch skill must re-open this question. Acceptable; that would be a constitutional-scale change.

- **Decision: `tasks.md` is staged inside the same `git add` as the task's code files but the rollback path uses `git restore --staged && git checkout`.**
  Rationale: the simpler "leave unstaged until commit succeeds" alternative would require either a `git commit` with explicit pathspec (fragile against partial-add hooks) or a post-commit amend (forbidden by skill rules). Staging together keeps the commit-formation step a single command. The two-step rollback is a small, well-understood git idiom.
  Trade-offs: the rollback sequence has two commands instead of one. Acceptable. Documented inline in the orchestrator step so a maintainer reading the skill sees the exact recovery commands.

- **Decision: drift-check between `skills/implement/SKILL.md` and `.claude/skills/implement/SKILL.md` lives in `scripts/validate_skills.py`.**
  Rationale: the file already validates skill frontmatter and is wired into CI. Extending it to assert the loop section of the two `implement/SKILL.md` files is byte-equal (after a known-trivial frontmatter delta) is the lowest-friction landing point. No new CI step.
  Trade-offs: the validator becomes opinionated about *which sections* must align. We constrain the check to the `## The loop` section by anchor-matching, so unrelated mirror tweaks (e.g. frontmatter `version` bumps) do not trip it.

- **Decision: Python helper module location — `src/aiadev/tasks_status.py`.**
  Rationale: parallels the existing `src/aiadev/preflight.py` and `src/aiadev/validate.py`. Keeps the `aiadev` package as the single home for skill-orchestration logic the Python tests can import directly.
  Trade-offs: the orchestrator (which runs as a Claude subagent) does not call this module today — it calls `Edit` directly through Claude tools. The module exists for the Python tests and (future) for `aiadev preflight` to share the same parse/validate logic. We accept the duplication risk and address it by having both code paths consume the same regex constant.

## Project structure changes

```text
specs/0013-implement-task-status-tracking/spec.md         (existing — approved)
specs/0013-implement-task-status-tracking/plan.md         (new — this file)
specs/0013-implement-task-status-tracking/tasks.md        (next skill)

skills/implement/SKILL.md                                 (modified — add explicit status-flip step + idempotency guard)
.claude/skills/implement/SKILL.md                         (modified — mirror of above)

src/aiadev/tasks_status.py                                (new — parse, validate, mutate)
src/aiadev/_assets/templates/tasks-template.md            (modified — add a one-line note that `Status` is mutated by `implement`)
templates/tasks-template.md                               (modified — same one-liner; root copy)

scripts/validate_skills.py                                (modified — add drift-check between the two implement SKILL.md files)

tests/test_tasks_status.py                                (new — unit tests for parse/validate/mutate)
tests/test_implement_skill_drift.py                       (new — asserts the two implement SKILL.md files agree on the loop section)
tests/fixtures/tasks_md_samples/                          (new — golden-file inputs: clean, malformed, out-of-order, in-progress, all-done)
```

No file removals.

## Phase breakdown

### Phase 1 — Test fixtures and red tests

Lay down the failing tests *before* any implementation prose or helper code, per Article II. Each scenario family lands in the test file that actually exercises it.

- Fixture files under `tests/fixtures/tasks_md_samples/` covering: a clean 3-task list, a malformed (`Status:` missing) list, an out-of-order (`done, pending, done`) list, an `in_progress` mid-list, and an all-`done` list (resume short-circuit case).
- **Story 1 + Story 2 → unit tests.** A red unit test in `tests/test_tasks_status.py` enumerating Story 1 and Story 2 acceptance scenarios as `parametrize` rows. The import of `aiadev.tasks_status` is expected to fail (module not yet present) — that is the right red.
- **Story 3 → markdown / drift tests, also red in this phase.** A red `tests/test_implement_skill_drift.py` that (a) `from scripts.validate_skills import check_implement_mirror` — fails today because the function does not yet exist (the right red for the validator itself), and (b) once the import resolves in Phase 2, contains parameterised assertions that the loop section of both `skills/implement/SKILL.md` and `.claude/skills/implement/SKILL.md` contains the literal status-mutation step wording (failing today because the wording is not yet present — the right red for Story 3 scenario 1, gated until Phase 3). Both red conditions are intentional and documented inline so a reader sees why the file ships before its dependencies.
- *Removed:* an e2e red test was originally planned to run the fake-LLM `implement` flow and assert `tasks.md` ends fully done. Investigation during plan execution confirmed that no `aiadev.tools.implement` exists — `implement` is agent-driven prose with no Python entry point — so there is no harness to extend. The verification gap is documented in spec Open risks; enforcement decomposes into the unit tests (Phase 1/2), drift validator (Phase 1/2), and skill prose (Phase 3).

### Phase 2 — Helper module + drift validator

Make the unit tests and the validator-import test green without touching the skill markdown yet.

- Implement `src/aiadev/tasks_status.py` with: `parse(path) -> list[TaskRow]`, `validate(rows) -> None | raises TasksMdError`, `mark_done(path, task_id) -> None`. Each function has the minimum signature the unit tests demand; nothing speculative. After this lands, `tests/test_tasks_status.py` is green.
- Extend `scripts/validate_skills.py` with `check_implement_mirror()` that diffs the `## The loop` section between `skills/implement/SKILL.md` and `.claude/skills/implement/SKILL.md` and fails on any non-whitespace difference. After this lands, the import in `tests/test_implement_skill_drift.py` resolves and the byte-equality assertion goes green (because the loop sections are identical in tree as of Phase 0). The Story 3 content assertion (looking for the new wording) remains red — that is intentional and unblocks in Phase 3.

### Phase 3 — Skill markdown updates

Now that the contract is enforceable in code, document it in the two skill files. This phase turns the still-red Story 3 markdown assertion green. Each task pairs a markdown edit with a regression run of the drift validator.

- Replace step 5 of `skills/implement/SKILL.md` with a numbered sub-procedure: (a) read row, (b) skip if `done`, (c) abort on malformed/prefix-violation with the exact error string from spec Story 2 scenario 2, (d) treat `in_progress` as `pending`, (e) after spec + code-quality reviewers approve, `Edit` the row to `done`, (f) `git add` the task's code files **and** `tasks.md` together and `git commit`; on commit failure, run `git restore --staged tasks.md && git checkout -- tasks.md` before re-raising.
- Apply the byte-identical change to `.claude/skills/implement/SKILL.md`. Drift validator must pass after this edit lands.
- Add the one-liner to both copies of `tasks-template.md` noting that `Status` is owned by `implement`.
- This phase also satisfies Story 3 scenario 3: the per-task dispatch contract lives entirely inside `implement/SKILL.md` (the prior `subagent-driven-development` skill was merged in — see Reconnaissance and the matching ADR), so the loop-step rewrite *is* the dispatch-contract update; no second file to touch.

### Phase 4 — Verification

- Run the full `pytest` suite — confirm green, paste the summary into the PR test plan.
- Run `python scripts/validate_skills.py` — exit 0 (drift check passes; the two `implement/SKILL.md` copies are aligned).
- Run the project's markdown lint (`npx markdownlint-cli2 '**/*.md'`) — confirm clean.
- Dogfood verification (manual, written into the PR test plan): on this very feature's `tasks.md`, the agent (running this `/aiadev:implement` session) is itself the first consumer of the new contract — every task in this branch ships with its `**Status:**` line flipped to `done` inside the same commit as the code change, and `git show` on each commit demonstrates Story 1 sc2 directly. Paste one such `git show --stat` output into the PR test plan as Article IV evidence.
- Hand off to `requesting-code-review`.

## Risks and mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Orchestrator marker `Edit` succeeds but `git commit` fails (hook rejection) | Med | Med | Wrap commit step in try/except: on failure, `git checkout -- tasks.md` to restore the pre-edit state, then surface the hook error to the user. |
| Drift validator becomes too strict and trips on legitimate frontmatter changes | Med | Low | Scope the validator to the `## The loop` section only, anchor-matched by `## The loop` and the next `## ` heading. Frontmatter and unrelated sections are excluded by design. |
| Existing in-flight features in consumer projects (where `tasks.md` carries pre-issue-#33 inconsistencies) start failing the new prefix invariant | Med | Med | The error message names the file and the inconsistency; consumers fix manually with the `sed` workaround already documented in issue #33. Changelog will call this out. |
| Implementer subagent prompt confusion if maintainers later try to also list `tasks.md` in "Files to modify" | Low | Low | The skill text explicitly states the orchestrator owns the marker; the implementer prompt does **not** list `tasks.md`. Reviewer subagent will reject any plan that proposes otherwise. |
| Test fixtures drift away from the real template format | Low | Low | The fixtures import the canonical `tasks-template.md` and parameterise on it; a template change forces a fixture update via failing tests. |

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
