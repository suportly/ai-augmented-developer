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

Turn a plain-language demand into a `spec.md` on **what** and **why**, no implementation details.

**Announce at start:** "Using the specify skill. I will produce a spec.md."

**Language.** Write the spec in the BCP-47 tag in the `Language:` header (`aiadev init --language`, default `en`); downstream skills continue in it.

## Preconditions

- A `constitution.md` exists (root or active preset) and `templates/spec-template.md` exists.
- On `main`, create `feature/<slug>` first.

## Loop

1. **Create the artifact stub.** Compute the next `{{SPEC_ID}}` (4-digit, zero-padded, monotonic across `specs/`). The spec directory is `specs/<NNNN>-<slug>/` where `<NNNN>` is `{{SPEC_ID}}` and `<slug>` is the kebab-case feature slug. If `specs/<NNNN>-<slug>/spec.md` does not exist, copy it from `templates/spec-template.md` and fill `{{FEATURE_NAME}}`, `{{BRANCH}}`, `{{DATE}}`, `{{SPEC_ID}}`. `aiadev init --feature <name>` does this in one shot.
2. **Read the demand.** Identify: primary problem, who feels it, the shape of a good outcome. Do not propose a solution yet. If `specs/_product/mission.md` and/or `specs/_product/roadmap.md` exist, read them and cross-check the demand against them: (a) if the demand conflicts with an entry in the mission's *Out of scope* section, pause and surface the conflict to the user, citing the entry — treated like a premise mismatch (step 3), never a marker; (b) if a `roadmap.md` entry matches the demand, cite its `R<NNN>` id in the spec's *Traceability* section. If neither exists, proceed as before.
3. **Reconnaissance.** For each app, service, or top-level surface mentioned in the demand that you have **not** already inspected this session: read its entry point file, read its auth/session module if it has one, and grep for the integration points the demand claims to use. Record findings in the spec's `<!-- section: Reconnaissance -->` block — one bullet per surface, each citing real on-disk paths in backticks (the validator checks every cited path for existence). For a single-surface change, use the explicit opt-out line documented in the template instead of bullets. **If the recon reveals that the demand's premise is structurally wrong on any surface (a flow that does not exist there), pause and surface the mismatch to the user before drafting any user story** — cite the specific file and line that contradicts the premise. That is a spec-validity problem, not a `[NEEDS CLARIFICATION]` one.
4. **Draft Problem, Users, Success criteria, Non-goals** (each under 5 bullets).
5. **Surface ambiguities inline.** Use at most 3 `[NEEDS CLARIFICATION:cl-N <precise question>]` markers per spec, chosen by priority: scope, then security/privacy, then UX. Ids are **monotonic** within the spec (`cl-1`, `cl-2`, …): the next id is always `max(existing) + 1`, never reused. Every remaining unknown goes to `## Assumptions`: a low-impact, reversible premise, one bullet each, tagged `[impact: low]` or `[impact: medium]`. An unknown that decides scope or security is never an assumption. If more than 3 are scope or security, stop: the demand is too broad; propose splitting into several specs, keeping 3 markers only if the user prefers. Do not invent answers.
6. **Write user stories.** Each story has ≥ 3 acceptance scenarios in Given / When / Then form. If you cannot think of three, fold the story into another or split it.
7. **Dispatch `spec-document-reviewer`** if available. Address feedback until the review returns approved.
8. **Report** in 3-5 lines: file link, outstanding markers.

## What not to do

- Do not write `plan.md` content, or invent acceptance criteria to close markers.
- Do not skip the spec because "the feature is obvious"; Article I is not waivable.
- Do not draft stories by analogy with another surface without a recon entry for it.
- Do not invent a `roadmap.md` entry or `R<NNN>` id for Traceability.

## Hand-off

- If markers remain → invoke `clarify`.
- If the spec is clean and reviewer-approved → invoke `plan`.
