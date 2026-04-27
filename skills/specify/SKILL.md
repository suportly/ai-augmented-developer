---
name: specify
description: Turn a natural-language demand into a numbered spec.md under specs/<NNNN-slug>/. Use when the user describes what they want but no spec exists yet.
version: 0.2.0
inputs:
  - type: text
    description: Feature request in free-form natural language (issue, user quote, product brief).
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

**Announce at start:** "Using the specify skill. I will produce a spec.md; implementation details come later."

**Language.** Write the spec in the BCP-47 tag recorded in the `Language:` header (stamped by `aiadev init --language`, default `en`). Every downstream skill (`clarify`, `plan`, `tasks`, `implement`, `analyze`, `checklist`) must read that header and continue in the same language. If the user asks for a different language mid-flow, update the header in `spec.md` first, then regenerate affected artifacts.

## Preconditions

- The repository has a `constitution.md` at the root (or in the active preset).
- `templates/spec-template.md` exists.
- The current branch is either `main` or an already-open feature branch. If on `main`, create `feature/<slug>` first.

## Loop

1. **Create the artifact stub.** Compute the next `{{SPEC_ID}}` (4-digit, zero-padded, monotonic across `specs/`). The spec directory is `specs/<NNNN>-<slug>/` where `<NNNN>` is `{{SPEC_ID}}` and `<slug>` is the kebab-case feature slug. If `specs/<NNNN>-<slug>/spec.md` does not exist, copy it from `templates/spec-template.md` and fill `{{FEATURE_NAME}}`, `{{BRANCH}}`, `{{DATE}}`, `{{SPEC_ID}}`. `aiadev init --feature <name>` does all of this in one shot.
2. **Read the demand.** Identify: primary problem, who feels it, the shape of a good outcome. Do not propose a solution yet.
3. **Reconnaissance.** For each app, service, or top-level surface mentioned in the demand that you have **not** already inspected this session: read its entry point file, read its auth/session module if it has one, and grep for the integration points the demand claims to use. Record findings in the spec's `<!-- section: Reconnaissance -->` block — one bullet per surface, each citing real on-disk paths in backticks (the validator checks every cited path for existence). For a single-surface change, use the explicit opt-out line documented in the template instead of bullets. **If the recon reveals that the demand's premise is structurally wrong on any surface (a flow that does not exist there), pause and surface the mismatch to the user before drafting any user story** — cite the specific file and line that contradicts the premise. Do not paper over a premise mismatch with `[NEEDS CLARIFICATION]` markers; that is a spec-validity problem, not a clarification problem.
4. **Draft the Problem, Users, Success criteria, and Non-goals sections.** Keep each under 5 bullets.
5. **Surface ambiguities inline.** Every unknown becomes a `[NEEDS CLARIFICATION:cl-N <precise question>]` marker with a **monotonically assigned** id within the spec (`cl-1`, `cl-2`, …). To compute the next id, count existing `cl-N` markers in the file and add 1. Do not reuse ids of removed markers; the next id is always `max(existing) + 1`. Do not invent answers.
6. **Write user stories.** Each story has ≥ 3 acceptance scenarios in Given / When / Then form. If you cannot think of three, the story is either too small (fold it into another) or too big (split it).
7. **Dispatch `spec-document-reviewer`** if available. Address feedback until the review returns approved.
8. **Report to the user.** Summarize the spec in 3-5 lines, link to the file, and list the outstanding `[NEEDS CLARIFICATION]` markers.

## What not to do

- Do not write `plan.md` content. Cross that bridge with `plan`.
- Do not invent acceptance criteria to close clarification markers. Ambiguity is a signal, not a defect.
- Do not skip the spec because "the feature is obvious". Article I is not waivable on feature work.
- Do not draft user stories by analogy with another surface without recording a recon entry for the surface in question. Analogy-driven drafts are how premise errors leak past `clarify` into `implement`.

## Hand-off

- If markers remain → invoke `clarify`.
- If the spec is clean and reviewer-approved → invoke `plan`.
