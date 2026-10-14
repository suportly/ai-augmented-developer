---
name: clarify
description: Surface [NEEDS CLARIFICATION] markers in spec.md (or plan.md) to the user, one at a time, and edit the file with the answers.
metadata:
  aiadev:
    version: 0.3.0
    inputs:
    - type: file
      path: specs/<branch>/spec.md
    outputs:
    - type: file
      path: specs/<branch>/spec.md
    requires:
    - constitution
    handoffs:
    - plan
---

# Clarify

Resolve every `[NEEDS CLARIFICATION: <question>]` marker in a spec or plan before it moves forward. An unanswered marker blocks `plan` and `implement`.

**Announce at start:** "Using the clarify skill. I will walk through each unresolved clarification marker."

## Preconditions

- Run pre-flight first: `aiadev preflight clarify --feature <slug>`. Abort on non-zero exit unless `AIADEV_PREFLIGHT=warn` is set.
- At least one `[NEEDS CLARIFICATION: ...]` marker exists in the target file.

## Loop

1. **Enumerate markers.** Grep the file; list the questions with file:line references.
2. **Triage.** Order by impact × uncertainty (dependencies first: if answering A narrows B, ask A first). Ask at most 5 per session; every unknown beyond the 5th becomes an explicit premise under `## Assumptions` (create it if missing) of the spec, not a question: remove its marker and tag the premise `[impact: low|medium]` as in `specify`.
3. **Ask one at a time** (`[NEEDS CLARIFICATION:cl-N <question>]`; each answer can change the next, so re-triage after it):
   - Restate the question in plain language with the surrounding paragraph as context.
   - Always give a recommendation with a one-line rationale grounded in the spec, codebase or conventions, marked clearly (`★ recommended`). If 2-4 answers are plausible, list them as options. The user must be able to accept it with one word ("yes", "recommended").
   - Wait for the answer. Never decide for the user; if they cannot answer, escalate or park the feature.
   - Edit the file: replace the entire marker with the resolved text, no residual comment, and record the answer in `## Clarifications`.
   - A new ambiguity gets a fresh marker with the next monotonic `cl-N` id.
   - **Legacy markers** (no `cl-N` id): assign the next available id first. Programmatic calls pass `answers=[{id: "cl-1", answer: "..."}, ...]`.
4. **Re-grep** to confirm zero markers remain before reporting done. Never delete a marker without a real answer.

## Hand-off

- Spec clarified → invoke `plan` (or return to the previous skill that called you).
