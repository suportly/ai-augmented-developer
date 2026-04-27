# Feature specification: Pipeline pre-flight checks

> This file is produced by the `specify` skill. Keep it focused on **what** and **why** — planning and code belong in `plan.md` and `tasks.md`.

**Branch:** `feature/pipeline-preflight-checks`
**Created:** 2026-04-20
**Status:** Draft
**Spec ID:** 0010
**Language:** en

---

<!-- section: Problem -->
## Problem

Today, every pipeline skill (`clarify`, `plan`, `tasks`, `implement`, `analyze`, `requesting-code-review`, `finishing-a-branch`) assumes prior artifacts exist and are well-formed, but none verifies it. When an agent skips a stage — or the previous stage produced a malformed artifact (missing section anchors, drifted `Language:` header, mismatched feature slug) — the failure surfaces several steps later with an opaque error (e.g. `tasks` cannot read `plan.md`, or `implement` parses partial scaffolding). The user pays for the wasted run and the skipped stage is hard to identify post-hoc.

<!-- section: Users and stakeholders -->
## Users and stakeholders

- Framework users running the aiadev pipeline who want fast, actionable failure messages.
- Skill authors who currently must defensively code around upstream malformed input.
- CI / E2E pipeline that today cannot assert "stage X refused stage Y output" because there is no shared validator.

<!-- section: Success criteria -->
## Success criteria

- Every downstream pipeline skill aborts within its first action when its required upstream artifacts are missing, malformed, or incoherent — with a single-line message naming the missing/invalid artifact and the skill to run to produce it.
- A shared `aiadev preflight <skill> --feature <slug>` command exits non-zero on the same failures that the in-skill check would catch, so CI and humans see identical errors.
- Pre-flight completes in under 500 ms for a reference feature directory containing `spec.md`, `plan.md`, `tasks.md`, and the schemas currently in `schemas/`.
- When `AIADEV_PREFLIGHT=warn` is set, the skill emits the diagnostic to stderr and continues instead of aborting; default (unset or `abort`) aborts.
- After the change ships, the existing E2E pipeline test demonstrates: deleting any prior-stage artifact causes the immediately following pipeline skill to fail with the actionable message (and not with an unrelated parse error).

<!-- section: Non-goals -->
## Non-goals

- Auto-repair of malformed artifacts. Pre-flight reports, it does not fix.
- Schema design for artifacts that do not yet have one (`tasks.md`, `analyze.md`); pre-flight uses the schemas that already exist and treats missing schemas as "presence + anchor check only".
- Re-validation of artifacts the current skill itself produces (that is the reviewer subagent's job).
- Replacing `validate_skills.py` or the existing JSON-schema set; pre-flight composes them.
- Cross-skill semantic consistency (e.g. constitution articles invoked in `spec.md` are addressed in `plan.md`). That belongs to `analyze`.

<!-- section: Breaking changes -->
## Breaking changes

- In-flight feature directories that drift from the new contract (missing section anchors, mismatched `Language:` headers, branch mismatch) will fail pre-flight on the next pipeline invocation. The plan must include a one-shot `aiadev preflight --all` command and a documented migration note.
- The `requesting-code-review` skill must be updated to write `.aiadev/review.yaml` (status + timestamp). Existing branches that completed review before this change will need a manual `review.yaml` stub before `finishing-a-branch` will run.

<!-- section: User stories -->
## User stories

### Story 1 — Skipping a stage fails fast with a pointer to the missing skill (P1)

As a framework user, I want any pipeline skill I invoke out of order to refuse to run and tell me which skill to run first, so I do not waste a run discovering it indirectly.

**Acceptance scenarios:**

1. Given a feature directory with `spec.md` and `plan.md` but no `tasks.md`, when I invoke `implement`, then the skill aborts with `pre-flight: tasks.md missing — run /aiadev:tasks first`.
2. Given a feature directory missing `spec.md` entirely, when I invoke any pipeline skill except `specify`, then it aborts with `pre-flight: spec.md missing — run /aiadev:specify first`.
3. Given a feature directory whose `spec.md` still contains unresolved `[NEEDS CLARIFICATION]` markers, when I invoke `plan`, then the skill aborts with `pre-flight: spec.md has N unresolved [NEEDS CLARIFICATION] markers — run /aiadev:clarify first`.
4. Given a feature directory with an approved `plan.md` and `tasks.md` but no `.aiadev/review.yaml` recording an approved review, when I invoke `finishing-a-branch`, then it aborts with `pre-flight: review approval missing — run /aiadev:requesting-code-review first`.
5. Given the feature directory is `0010-pipeline-preflight-checks` but the current git branch is `feature/other-thing`, when I invoke any pipeline skill, then pre-flight aborts with `pre-flight: git branch 'feature/other-thing' does not match feature directory '0010-pipeline-preflight-checks'`.
6. Given `AIADEV_PREFLIGHT=warn` is set and `tasks.md` is missing, when I invoke `implement`, then pre-flight emits the diagnostic to stderr, exits with status 0, and the skill continues executing.

### Story 2 — Malformed upstream artifact is caught before downstream work (P1)

As a skill author, I want pre-flight to reject artifacts that lack required section anchors or have a drifted `Language:` header, so downstream skills do not silently proceed against bad input.

**Acceptance scenarios:**

1. Given a `spec.md` whose `<!-- section: Problem -->` anchor was removed, when I invoke `plan`, then pre-flight reports `pre-flight: spec.md missing required section anchor 'Problem'` and aborts.
2. Given a `spec.md` with `Language: en` and a `plan.md` with `Language: pt-BR`, when I invoke `tasks`, then pre-flight reports `pre-flight: language mismatch — spec.md=en, plan.md=pt-BR` and aborts.
3. Given a `plan.md` whose `Branch:` header does not match the feature slug of the directory, when I invoke `tasks`, then pre-flight reports `pre-flight: plan.md branch header 'feature/foo' does not match feature directory '0010-pipeline-preflight-checks'` and aborts.

### Story 3 — CI can run pre-flight independently (P2)

As a CI maintainer, I want a CLI entry point that runs the same check the skill does, so the contract is enforced even when the skills are not invoked through Claude Code.

**Acceptance scenarios:**

1. Given a feature directory in a valid state, when I run `aiadev preflight plan --feature 0010-pipeline-preflight-checks`, then it exits 0 with no output.
2. Given the same directory with `tasks.md` deleted, when I run `aiadev preflight implement --feature 0010-pipeline-preflight-checks`, then it exits non-zero and prints the same single-line message the skill would emit.
3. Given an unknown skill name, when I run `aiadev preflight bogus --feature 0010-...`, then it exits non-zero with `unknown skill 'bogus'; expected one of: clarify, plan, tasks, implement, analyze, requesting-code-review, finishing-a-branch`.

<!-- section: Clarifications -->
## Clarifications

All clarifications resolved during spec authoring. Decisions:

- **Failure mode (was cl-1):** Hard abort by default. The env var `AIADEV_PREFLIGHT=warn` downgrades to a stderr diagnostic + continue, intended for debugging only. No `--force` flag (env var keeps the bypass out of muscle memory).
- **Scope for schema-less artifacts (was cl-2):** MVP performs presence + section-anchor checks only for `tasks.md` and `analyze.md`. Full JSON schemas for them are a follow-up feature.
- **Review-approval signal (was cl-3):** `requesting-code-review` writes `.aiadev/review.yaml` with `status: approved|changes_requested` and a timestamp; `finishing-a-branch` pre-flight requires `status: approved`.
- **Feature-slug source of truth (was cl-4):** The directory name `specs/<NNNN>-<slug>/` is authoritative. The `Branch:` header in `spec.md` and the current git branch must match `feature/<slug>`; mismatch is a pre-flight failure.
- **Cross-skill semantic checks (was cl-5):** Out of scope (see Non-goals).

<!-- section: Data touched -->
## Data touched

- Reads: `specs/<NNNN-slug>/spec.md`, `plan.md`, `tasks.md`, plus optional `research.md`, `data-model.md`, `contracts/`, and `.aiadev/review.yaml`.
- Reads: existing JSON schemas under `schemas/` for any artifact that has one.
- Writes: nothing. Pre-flight is read-only.
- Emits: a single-line diagnostic to stderr on failure; non-zero exit when invoked as CLI.

<!-- section: Out-of-band effects -->
## Out-of-band effects

- None. Pre-flight does not call external APIs, does not write files, does not mutate git state.

<!-- section: Open risks -->
## Open risks

- Existing in-flight feature directories may not satisfy stricter checks (e.g. drifted `Language:` headers); shipping this without a migration path could block users mid-pipeline.
- Section-anchor validation depends on the templates being stable; if a template adds a new anchor, every in-flight feature instantly fails pre-flight unless we version anchors.
- The `--force` / env bypass (pending cl-1) risks becoming the default in CI, defeating the purpose.

<!-- section: Traceability -->
## Traceability

- Originating issue: critical analysis conversation 2026-04-20 (problem #2 in "Onda 1")
- Related specs: none
- Cross-feature dependencies: `requesting-code-review` skill must be updated to emit `.aiadev/review.yaml` for Story 1 scenario 4 to be testable.
- Constitution articles invoked: I (Spec-first), II (Test-first — pre-flight needs E2E coverage), III (Simplicity — read-only checker, no auto-repair), IV (Evidence over claims — failure messages must be precise and actionable)
