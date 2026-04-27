# Feature specification: {{FEATURE_NAME}}

> This file is produced by the `specify` skill (or by `aiadev init --feature <name>` as a stub). Keep it focused on **what** and **why** — planning and code belong in `plan.md` and `tasks.md`.

**Branch:** `{{BRANCH}}`
**Created:** {{DATE}}
**Status:** Draft <!-- Draft | In review | Approved | Implemented -->
**Spec ID:** {{SPEC_ID}} <!-- auto-incrementing integer -->
**Language:** {{DOC_LANGUAGE}} <!-- BCP-47 tag; every downstream artifact in this feature is written in this language. -->

---

<!-- section: Problem -->
## Problem

<!-- 2-3 sentences. What is broken, missing, or slow today? Who notices?
     Link to supporting evidence (issue, analytics screenshot, user quote).
     You may translate the heading text for non-English specs; the
     `<!-- section: Problem -->` comment above is the schema anchor that
     aiadev validators read, so do not remove or translate it. -->

<!-- section: Reconnaissance -->
## Reconnaissance

<!-- One bullet per surface (app, service, top-level directory) the
     demand touches that you have not already inspected this session.
     The bullet must cite at least one real on-disk file path in
     backticks. The validator (issue #26) checks each cited path for
     existence; prose without a backticked path fails.

     If this is a single-surface change, replace the bullets below
     with a single line of the exact form (and nothing else):

     Reconnaissance: not required (single-surface change: <surface-name>)

     Heading text may be translated for non-English specs; the
     section-anchor comment above must not be translated (anchors are
     the schema contract that aiadev validators read). -->

- **<surface-name>** — entry: `<path>` · auth: `<path|none>` · integration: `<path-or-grep-term>`

<!-- section: Users and stakeholders -->
## Users and stakeholders

<!-- Who benefits from this being done? Who is affected (positive or
     negative)? Who signs off? One bullet per party. -->

-

<!-- section: Success criteria -->
## Success criteria

<!-- Observable outcomes after this ships. Each one should be testable
     or measurable. "It feels faster" is not a success criterion; a
     p95 latency target is. -->

-

<!-- section: Non-goals -->
## Non-goals

<!-- Things explicitly out of scope. List them so the plan does not
     drift into them. -->

-

<!-- section: User stories -->
## User stories

### Story 1 — {{SHORT_TITLE}} (P1)

As a {{ROLE}}, I want {{ACTION}} so that {{OUTCOME}}.

**Acceptance scenarios** (Given / When / Then, ≥ 3 per story):

1. Given ... When ... Then ...
2. Given ... When ... Then ...
3. Given ... When ... Then ...

### Story 2 — {{SHORT_TITLE}} (P2) <!-- optional -->

<!-- section: Clarifications -->
## Clarifications

<!-- Put one [NEEDS CLARIFICATION:cl-N <precise question>] marker here for
     every ambiguity you cannot resolve on your own. The id (cl-1, cl-2, …)
     is a positive integer monotonically assigned within this spec; the
     `clarify` skill will surface these to the user before the spec is
     considered approved. -->

- [NEEDS CLARIFICATION:cl-1 example — is this feature gated behind the Pro plan?]

<!-- section: Data touched -->
## Data touched

<!-- Entities, fields, events created or modified. Not implementation —
     names and shapes only. -->

-

<!-- section: Out-of-band effects -->
## Out-of-band effects

<!-- Anything that reaches beyond this process: notifications sent,
     payments charged, files written to external storage, third-party
     APIs called. If none, say so. -->

-

<!-- section: Open risks -->
## Open risks

<!-- Risks known at spec time. Do not promise mitigations here —
     that is for `plan.md`. -->

-

<!-- section: Traceability -->
## Traceability

- Originating issue: {{ISSUE_URL}}
- Related specs: {{LIST_OR_NONE}}
- Constitution articles invoked: <!-- e.g. I, II, V -->
