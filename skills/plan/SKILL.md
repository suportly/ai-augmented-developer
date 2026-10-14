---
name: plan
description: Turn an approved spec.md into a plan.md (plus research, data-model, contracts as needed) that passes the Constitution Check.
metadata:
  aiadev:
    version: 0.2.0
    inputs:
    - type: file
      path: specs/<branch>/spec.md
    - type: dir
      path: specs/_product
      description: Declared stack decisions (tech-stack.md), read when present; plan behaves as today when absent.
      optional: true
    outputs:
    - type: file
      path: specs/<branch>/plan.md
    # Auxiliary artifacts (research.md, data-model.md, contracts/) are
    # follow-up invocations — the plan references them but does not write
    # them in the same call. See the "Next-invocation hints" block below.
    requires:
    - constitution
    - templates/plan-template.md
    handoffs:
    - tasks
    - clarify
---

# Plan

Write the implementation plan from a clean `spec.md`: **how** it will be realized, not task-level code (that is `tasks`).

## Preconditions

- `aiadev preflight plan --feature <slug>` exits 0 (abort otherwise unless `AIADEV_PREFLIGHT=warn`).
- `spec.md` is reviewer-approved with zero `[NEEDS CLARIFICATION]` markers; else run `clarify` or `specify`.

## Loop

1. **Copy the template** `templates/plan-template.md` → `specs/<branch>/plan.md`; fill the header.
2. **Summary and Technical context.** One paragraph, then the table from the active preset plus the spec's non-goals and performance budget. If `specs/_product/tech-stack.md` exists, fill Technical context from its Languages/Frameworks; anything new the plan introduces becomes an **Architecture decisions** entry with justification. Compare its Languages/Frameworks with the `aiadev:auto-stack` block in `AGENTS.md` (when present) and list language/framework divergences citing both sides, without choosing; the human decides which is stale. If `tech-stack.md` is absent, proceed exactly as before.
3. **Constitution Check.** One row per applicable article: `PASS`, `FAIL`, or `N/A` with concrete evidence (file path, test name, or "no provider added"). Any `FAIL` needs a **Complexity tracking** row with the waiver reason.
4. **Architecture decisions.** Short ADR entries: decision, rationale, trade-off.
5. **Project structure changes.** Diff-style list of files to create, modify, remove.
6. **Phase breakdown.** Phases whose order matters; tasks within a phase are independent. Do not enumerate tasks (that is `tasks`).
7. **Write `plan.md` only.** `research.md`, `data-model.md`, `contracts/` belong to follow-up invocations; if a *Single required artifact* directive is present, honour it.
8. **Dispatch `plan-document-reviewer`** if available; iterate until approved.
9. **Report** in 3-5 lines: phases, task forecast, waivers, link.

## Rules

- The Constitution Check is non-optional: blank rows block `tasks`.
- No code in the plan; pseudo-code only to clarify an ADR.
- If `references/stack.md` exists beside this file, read it for stack-specific guidance.

## Graph provider blast-radius (optional)

When a knowledge-graph provider is configured (spec 0017), add an **Affected surfaces / blast-radius** section: query its `impact` operation for the paths the plan changes, list the subsystems touched, citing each edge as `path:symbol` with its confidence label per `rules/graph-facts.md` (an `inferred`/`ambiguous` edge is a signal to verify). **Graceful degradation:** provider absent or unavailable → omit the section with a short note, never an error.

## Hand-off

Constitution Check clean → `tasks`. New ambiguity → `clarify`, with markers added to `spec.md` (not `plan.md`).
