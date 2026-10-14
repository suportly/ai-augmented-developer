---
name: specify
description: Turn a natural-language demand into a numbered spec.md under specs/<NNNN-slug>/. Use when the user describes what they want but no spec exists yet.
metadata:
  aiadev:
    version: 0.2.0
    inputs:
    - type: text
      description: Feature request in free-form natural language (issue, user quote, product brief).
    - type: dir
      path: specs/_product
      description: Product context (mission.md, roadmap.md) read when present; specify behaves as today when absent.
      optional: true
    outputs:
    - type: file
      path: specs/<NNNN-slug>/spec.md
    requires:
    - constitution
    - templates/spec-template.md
    handoffs:
    - clarify
    - plan
---

# Specify

Take a demand in plain language and produce a `spec.md` focused on **what** and **why** — no implementation details.

**Announce at start:** "Using the specify skill. I will produce a spec.md."

**Language.** Write the spec in the BCP-47 tag recorded in the `Language:` header (stamped by `aiadev init --language`, default `en`). Every downstream skill reads that header and continues in the same language; to switch language, update the header first, then regenerate affected artifacts.

## Preconditions

- The repository has a `constitution.md` at the root (or in the active preset).
- `templates/spec-template.md` exists.
- The current branch is either `main` or an already-open feature branch. If on `main`, create `feature/<slug>` first.

## Loop

1. **Create the artifact stub.** Compute the next `{{SPEC_ID}}` (4-digit, zero-padded, monotonic across `specs/`). The spec directory is `specs/<NNNN>-<slug>/` where `<NNNN>` is `{{SPEC_ID}}` and `<slug>` is the kebab-case feature slug. If `specs/<NNNN>-<slug>/spec.md` does not exist, copy it from `templates/spec-template.md` and fill `{{FEATURE_NAME}}`, `{{BRANCH}}`, `{{DATE}}`, `{{SPEC_ID}}`. `aiadev init --feature <name>` does all of this in one shot.
2. **Read the demand.** Identify: primary problem, who feels it, the shape of a good outcome. Do not propose a solution yet. If `specs/_product/mission.md` and/or `specs/_product/roadmap.md` exist, read them and cross-check the demand against them: (a) if the demand conflicts with an entry in the mission's *Out of scope* section, pause and surface the conflict to the user, citing the entry — same treatment as the premise-mismatch rule in step 3; do not paper over it with a `[NEEDS CLARIFICATION]` marker; (b) if a `roadmap.md` entry matches the demand, cite its `R<NNN>` id in the spec's *Traceability* section. If neither file exists, skip this and proceed exactly as before.
3. **Reconnaissance.** For each app, service, or top-level surface mentioned in the demand that you have **not** already inspected this session: read its entry point file, read its auth/session module if it has one, and grep for the integration points the demand claims to use. Record findings in the spec's `<!-- section: Reconnaissance -->` block — one bullet per surface, each citing real on-disk paths in backticks (the validator checks every cited path for existence). For a single-surface change, use the explicit opt-out line documented in the template instead of bullets. **If the recon reveals that the demand's premise is structurally wrong on any surface (a flow that does not exist there), pause and surface the mismatch to the user before drafting any user story** — cite the specific file and line that contradicts the premise. Do not paper over a premise mismatch with `[NEEDS CLARIFICATION]` markers; that is a spec-validity problem, not a clarification problem.
4. **Draft the Problem, Users, Success criteria, and Non-goals sections.** Keep each under 5 bullets.
5. **Surface ambiguities inline.** Use at most 3 `[NEEDS CLARIFICATION:cl-N <precise question>]` markers per spec, chosen by priority: scope, then security/privacy, then UX. Ids are **monotonic** within the spec (`cl-1`, `cl-2`, …): the next id is always `max(existing) + 1`, never reused. Every remaining unknown goes to `## Assumptions`: a low-impact, reversible premise, one bullet each, tagged `[impact: low]` or `[impact: medium]`. An unknown that decides scope or security is never an assumption. If more than 3 are scope or security, stop: the demand is too broad; propose splitting into several specs, keeping 3 markers only if the user prefers. Do not invent answers.
6. **Write user stories.** Each story has ≥ 3 acceptance scenarios in Given / When / Then form. If you cannot think of three, the story is either too small (fold it into another) or too big (split it).
7. **Dispatch `spec-document-reviewer`** if available. Address feedback until the review returns approved.
8. **Report to the user.** Summarize in 3-5 lines, link the file, list outstanding markers.

## What not to do

- Do not write `plan.md` content.
- Do not invent acceptance criteria to close clarification markers.
- Do not skip the spec because "the feature is obvious"; Article I is not waivable.
- Do not draft user stories by analogy with another surface without recording a recon entry for the surface in question. Analogy-driven drafts are how premise errors leak past `clarify` into `implement`.
- Do not invent a `roadmap.md` entry or `R<NNN>` id for Traceability.

## Hand-off

- If markers remain → invoke `clarify`.
- If the spec is clean and reviewer-approved → invoke `plan`.
