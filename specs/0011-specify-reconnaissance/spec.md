# Feature specification: Specify reconnaissance step

> This file is produced by the `specify` skill. Keep it focused on **what** and **why** — planning and code belong in `plan.md` and `tasks.md`.

**Branch:** `feature/specify-reconnaissance`
**Created:** 2026-04-27
**Status:** Draft
**Spec ID:** 0011
**Language:** en

---

<!-- section: Problem -->
## Problem

When `specify` is invoked for a feature whose demand touches an app, service, or surface the agent has not inspected during the current session, the agent often drafts user stories **by analogy** with a sibling surface it knows better. If the analogy is wrong (different entry point, different auth model, different data flow) the spec ships with structurally invalid user stories. Neither `clarify` (which probes behavior of the proposed flow) nor `plan`'s Constitution Check (which does not verify that the user stories have a real touchpoint in the code) detects the mismatch. The cost is paid downstream when `implement` reads the actual code: spec, plan, and tasks all need to be rewritten — multiple hours of churn per occurrence (real example: nzr-kdp spec 025, where 3 of 5 user stories were invalidated by the first 30 lines of `mobile/app/index.tsx`).

<!-- section: Reconnaissance -->
## Reconnaissance

Backfilled per T013 — this spec was authored before the recon rule shipped (cutover_spec_id = 10; this spec is id 11). Each bullet cites paths actually inspected during spec authoring.

- **skills/specify** — entry: `skills/specify/SKILL.md` · auth: `none` · integration: `templates/spec-template.md`
- **templates** — entry: `templates/spec-template.md` · auth: `none` · integration: `schemas/spec-recon.schema.json`
- **schemas** — entry: `schemas/spec-recon.schema.json` · auth: `none` · integration: `src/aiadev/validate.py`
- **src/aiadev** — entry: `src/aiadev/validate.py` · auth: `none` · integration: `src/aiadev/commands/validate.py`
- **skills/using-ai-augmented-developer** — entry: `skills/using-ai-augmented-developer/SKILL.md` · auth: `none` · integration: `skills/specify/SKILL.md`
- **tests** — entry: `tests/test_validate.py` · auth: `none` · integration: `tests/conftest.py`

<!-- section: Users and stakeholders -->
## Users and stakeholders

- Framework users running `aiadev:specify` against demands that span more than one surface they haven't yet inspected.
- Skill authors maintaining `specify`, `clarify`, and `plan` who currently absorb the cost of premise errors as downstream defensive code.
- Reviewers of generated specs who today have no signal that the structural premise was checked against real code.

<!-- section: Success criteria -->
## Success criteria

- For any demand that mentions more than one surface (or a surface not inspected earlier in the session), `specify` produces a `spec.md` whose `Reconnaissance` section names each surface, the entry-point and auth/session files actually read, and the integration points grepped for — drafted before any user story.
- When the reconnaissance reveals a structural mismatch with the demand's premise (a flow that does not exist on the named surface), `specify` pauses and surfaces the mismatch to the user before any user story is written.
- The schema validator must exit non-zero for any spec that lacks a `Reconnaissance` section without an explicit opt-out declaration, regardless of whether user stories are present.
- The `using-ai-augmented-developer` orientation skill mentions the recon step so a fresh agent learns the contract before its first `specify` call.
- A regression test fails if `templates/spec-template.md` loses the `<!-- section: Reconnaissance -->` anchor or the `specify` skill loses the recon step from its Loop.

<!-- section: Non-goals -->
## Non-goals

- Automating the audit itself (an MCP tool that runs the four greps). Worthwhile but separate.
- Retrofitting old specs that pre-date this change.
- Validating semantic correctness of recon findings (the validator checks structure and presence of paths, not that the paths are the *right* ones).
- Extending the recon step to `plan`, `tasks`, or `clarify` — those skills consume an already-recon'd spec.
- Replacing the `Constitution Check` in `plan.md` with anything recon-related.

<!-- section: Breaking changes -->
## Breaking changes

- In-flight specs created before this change ship without a `Reconnaissance` section. The schema validator treats the section as required only for specs whose `Spec ID` is strictly greater than the cutover id pinned in the validator at ship time (the cutover id is the next free id at merge time, recorded in the schema). Specs at or below the cutover are grandfathered.
- The `spec-document-reviewer` subagent gains a check for the recon section, gated by the same cutover id — running it against a grandfathered spec is a no-op for this rule. No new `--legacy` flag is added.

<!-- section: User stories -->
## User stories

### Story 1 — Multi-surface demand triggers recon before any user story (P1)

As a framework user, I want `specify` to inspect each named surface before drafting user stories, so the spec cannot be drafted by analogy with the wrong sibling surface.

**Acceptance scenarios:**

1. Given a fresh session and a demand naming two surfaces (e.g. "web admin" and "mobile app") that the agent has not inspected this session, when I invoke `specify`, then before any user story is drafted the agent reads each surface's entry point and auth/session module and records the file paths in the spec's `Reconnaissance` section.
2. Given a recon pass that reveals the demand's premise is structurally wrong on one of the named surfaces (e.g. demand asks for "mobile signup" but the mobile app is kids-only/paired), when the agent reaches step 2 of the Loop, then it pauses, reports the mismatch to the user citing the file path that contradicts the premise, and does not draft user stories for that surface until the user resolves the mismatch.
3. Given a demand whose surface(s) the agent has already inspected earlier in the same session, when I invoke `specify`, then the recon section still cites the file paths read for each surface (the validator does not enforce session-freshness; it is a structural check) and the Loop continues without pausing.

### Story 2 — Schema rejects empty recon on multi-surface specs (P1)

As a skill author, I want the schema validator to refuse a spec whose `Reconnaissance` section is empty when the demand mentions more than one surface, so analogy-driven drafts cannot ship past CI.

**Acceptance scenarios:**

1. Given a `spec.md` whose `Reconnaissance` section is empty and which carries no explicit single-surface opt-out line, when `aiadev validate` runs, then it exits non-zero with `Reconnaissance section required; add at least one surface entry or opt-out line`. (Surface detection is structural: the validator counts top-level repository directories named in `Problem` or `Users and stakeholders`; multi-surface inference is a hint surfaced in the error message but is not the gate.)
2. Given a single-surface `spec.md` that opts out via the explicit line `Reconnaissance: not required (single-surface change: <surface-name>)`, when `aiadev validate` runs, then it exits 0.
3. Given a `spec.md` whose `Reconnaissance` section is non-empty but contains only prose ("I audited the mobile app") with no file paths, when `aiadev validate` runs, then it exits non-zero with `Reconnaissance entries must cite at least one file path per surface`.

### Story 3 — Orientation surfaces the recon contract to fresh agents (P2)

As an agent invoking the framework for the first time in a conversation, I want `using-ai-augmented-developer` to mention the recon step, so I learn the contract before my first `specify` call rather than failing validation after writing a draft.

**Acceptance scenarios:**

1. Given a fresh conversation, when an agent invokes `using-ai-augmented-developer`, then the rendered guidance contains the literal string `Reconnaissance` at least once and a link to `skills/specify/SKILL.md`.
2. Given `skills/using-ai-augmented-developer/SKILL.md` and `skills/specify/SKILL.md`, when a regression test asserts that the literal string `Reconnaissance` appears in both files, then the assertion passes; if either file drops the string, the test fails.

<!-- section: Clarifications -->
## Clarifications

All clarifications resolved during spec authoring. Decisions:

- **Surface definition (was cl-1):** A "surface" is any top-level app/service directory under the repo root (e.g. `mobile/`, `backend/`, `web/`). For repos that do not match this convention, the agent self-declares the surface list in the recon block; the validator treats the declared list as authoritative. Heuristic name-matching is a hint in error messages, not the gate.
- **Session freshness (was cl-2):** The validator does not enforce whether a surface was "already inspected this session" — that is a behavioural concern the `specify` skill enforces in prose. The validator is structural: every surface entry must cite at least one file path, and every cited path must exist on disk.
- **Legacy spec migration (was cl-3):** Cutover by `Spec ID`. Specs whose id is strictly greater than the cutover id (pinned in the validator schema at ship time) must carry a non-empty `Reconnaissance` section. Specs at or below the cutover id are grandfathered. No date-based cutover, no free opt-out flag.
- **Non-English templates (was cl-4):** All locale-specific spec templates ship the recon section. Heading text may be translated; the `<!-- section: Reconnaissance -->` anchor must not be (consistent with the existing anchor-stability rule).

<!-- section: Data touched -->
## Data touched

- Reads: `templates/spec-template.md`, `skills/specify/SKILL.md`, `skills/using-ai-augmented-developer/SKILL.md`, files named in any draft `Reconnaissance` block (entry points, auth modules, integration grep targets).
- Writes: a new `<!-- section: Reconnaissance -->` block in every newly created `spec.md`. No existing files are mutated by the runtime; the change is to the templates and skill prose.
- Schema additions: a new validator rule keyed off the `<!-- section: Reconnaissance -->` anchor and the surface-mention heuristic.

<!-- section: Out-of-band effects -->
## Out-of-band effects

- None. Reconnaissance is read-only inspection of files already inside the working directory. No network calls, no external APIs, no git mutation.

<!-- section: Open risks -->
## Open risks

- **Shallow padding.** Agents may satisfy the schema by listing paths without actually reading them. Mitigation belongs to the skill prose ("cite paths you have read in this session"), but the validator cannot prove a read happened.
- **Surface heuristic drift.** Repos that do not put apps under top-level directories (monorepos with non-conventional layouts) may bypass the multi-surface trigger. Validator must fall back to the agent's self-declared surface list.
- **Legacy spec churn.** Without a clean migration policy, in-flight specs become un-validatable the moment the change ships.
- **Translation rot.** Non-English presets that translate the recon heading may drift from the anchor; the rule "anchors are not translated" must be re-stated in the template comment.

<!-- section: Traceability -->
## Traceability

- Originating issue: GitHub #26 — "specify: require a brief 'architecture reconnaissance' before drafting user stories on a surface not touched this session"
- Related specs: 0010-pipeline-preflight-checks (validator infrastructure this spec extends), 0009-token-economy-terse-mode (reviewer subagent contract this spec extends with a recon check)
- Cross-feature dependencies: `templates/spec-template.md` change must ship together with `skills/specify/SKILL.md` and the schema rule; otherwise running specs partially upgraded fails validation.
- Constitution articles invoked: I (Spec-first — recon is a precondition for a valid spec), II (Test-first — schema and skill regression tests must precede the implementation), III (Simplicity — read-only audit, no auto-repair), IV (Evidence over claims — file paths replace prose).
