# Feature specification: {{FEATURE_NAME}}

> This file is produced by the `specify` skill (or by `aiadev init --feature <name>` as a stub). Keep it focused on **what** and **why** — planning and code belong in `plan.md` and `tasks.md`.

**Branch:** `{{BRANCH}}`
**Created:** {{DATE}}
**Status:** Draft <!-- Draft | In review | Approved | Implemented -->
**Spec ID:** {{SPEC_ID}} <!-- auto-incrementing integer -->
**Language:** {{DOC_LANGUAGE}} <!-- BCP-47 tag; every downstream artifact in this feature is written in this language. -->

---

## Problem

<!-- 2-3 sentences. What is broken, missing, or slow today? Who notices?
     Link to supporting evidence (issue, analytics screenshot, user quote). -->

## Users and stakeholders

<!-- Who benefits from this being done? Who is affected (positive or
     negative)? Who signs off? One bullet per party. -->

-

## Success criteria

<!-- Observable outcomes after this ships. Each one should be testable
     or measurable. "It feels faster" is not a success criterion; a
     p95 latency target is. -->

-

## Non-goals

<!-- Things explicitly out of scope. List them so the plan does not
     drift into them. -->

-

## User stories

### Story 1 — {{SHORT_TITLE}} (P1)

As a {{ROLE}}, I want {{ACTION}} so that {{OUTCOME}}.

**Acceptance scenarios** (Given / When / Then, ≥ 3 per story):

1. Given ... When ... Then ...
2. Given ... When ... Then ...
3. Given ... When ... Then ...

### Story 2 — {{SHORT_TITLE}} (P2) <!-- optional -->

## Clarifications

<!-- Put one [NEEDS CLARIFICATION: <precise question>] marker here for
     every ambiguity you cannot resolve on your own. The `clarify` skill
     will surface these to the user before the spec is considered approved. -->

- [NEEDS CLARIFICATION: example — is this feature gated behind the Pro plan?]

## Data touched

<!-- Entities, fields, events created or modified. Not implementation —
     names and shapes only. -->

-

## Out-of-band effects

<!-- Anything that reaches beyond this process: notifications sent,
     payments charged, files written to external storage, third-party
     APIs called. If none, say so. -->

-

## Open risks

<!-- Risks known at spec time. Do not promise mitigations here —
     that is for `plan.md`. -->

-

## Traceability

- Originating issue: {{ISSUE_URL}}
- Related specs: {{LIST_OR_NONE}}
- Constitution articles invoked: <!-- e.g. I, II, V -->
