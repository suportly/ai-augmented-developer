---
name: clarify
description: Surface [NEEDS CLARIFICATION] markers in spec.md (or plan.md) to the user, one at a time, and edit the file with the answers.
version: 0.2.0
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

- At least one `[NEEDS CLARIFICATION: ...]` marker exists in the target file.

## Loop

1. **Enumerate markers.** Grep the file; list the questions with file:line references.
2. **Order them.** Dependencies first (if answering A narrows B, ask A first). Then risk (highest-impact first).
3. **For each marker:**
   - Restate the question in plain language, giving the surrounding paragraph as context.
   - If there are 2-4 plausible answers, offer them as a multiple choice.
   - Wait for the user's answer.
   - Edit the file: replace the entire `[NEEDS CLARIFICATION: ...]` expression with the resolved text. Do **not** leave a residual comment.
   - If the answer reveals a new ambiguity, add a fresh marker rather than papering over it.
4. **Re-grep** to confirm zero markers remain before reporting done.

## Rules

- One question at a time. Never batch-ask "here are five questions, answer whichever". That produces half-answered specs.
- Never guess. If the user cannot answer, escalate (tag a stakeholder) or park the feature.
- Never delete a marker without substituting a real answer.

## Hand-off

- Spec clarified → invoke `plan` (or return to the previous skill that called you).
