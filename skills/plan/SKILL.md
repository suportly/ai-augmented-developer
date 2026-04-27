---
name: plan
description: Turn an approved spec.md into a plan.md (plus research, data-model, contracts as needed) that passes the Constitution Check.
version: 0.2.0
inputs:
  - type: file
    path: specs/<branch>/spec.md
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

Write the implementation plan from a clean `spec.md`. The plan says **how** the spec will be realized, without diving into task-level code (that is `tasks`).

**Announce at start:** "Using the plan skill. I will produce plan.md and pass the Constitution Check before handing off."

## Preconditions

- Run pre-flight first: `aiadev preflight plan --feature <slug>`. Abort on non-zero exit unless `AIADEV_PREFLIGHT=warn` is set.
- `spec.md` exists, reviewer-approved, and contains zero `[NEEDS CLARIFICATION]` markers. If not → invoke `clarify` or `specify` first.
- `constitution.md` is readable.

## Loop

1. **Copy the template.** `templates/plan-template.md` → `specs/<branch>/plan.md`. Fill the header placeholders.
2. **Write the Summary** (one paragraph) and **Technical context** table from the active preset plus the spec's non-goals and performance budget.
3. **Fill the Constitution Check table.** One row per applicable article. For each: mark `PASS`, `FAIL`, or `N/A`, and give concrete evidence (file path, test name, or "no provider added"). If any article is `FAIL`, you **must** add a row to **Complexity tracking** with the waiver reason.
4. **Add Architecture decisions.** Short ADR-style entries — decision, rationale, trade-off. One per non-trivial choice.
5. **Project structure changes.** Diff-style listing of files to create, modify, or remove.
6. **Phase breakdown.** Group the work into phases whose order matters. Within a phase, tasks will be independent. Do not enumerate individual tasks here — that is `tasks`'s job.
7. **Next-invocation hints — do NOT write in this call.** The plan may
   reference auxiliary artifacts that, when needed, belong in follow-up
   invocations of this skill (or in a separate spec). This call writes
   `plan.md` **only**. Hints for future invocations:
   - `research.md` for investigations the plan depends on.
   - `data-model.md` for schema diagrams or field lists.
   - `contracts/` for API payloads, event shapes, CLI grammars.

   When `aiadev.tools.plan(...)` is the entry point, the orchestrator
   passes a *Single required artifact* directive that forbids these
   auxiliary paths in the current turn — honour it.
8. **Dispatch `plan-document-reviewer`** if available. Iterate until approved.
9. **Report** in 3-5 lines: phases, #tasks forecast, any waivers requested, link to the file.

## Rules

- The Constitution Check is **non-optional**. A plan with blank rows blocks `tasks` from running.
- Do not write code in the plan. Pseudo-code is allowed only when needed to clarify an ADR.
- Do not enumerate tasks here. `tasks.md` is the only source of truth for the task list.

## Hand-off

- Plan approved, Constitution Check clean → invoke `tasks`.
- Plan revealed new ambiguity → invoke `clarify` with specific markers added to `spec.md` (not `plan.md`).
