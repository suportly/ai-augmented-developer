---
name: tasks
description: Decompose an approved plan.md into an ordered tasks.md ready for `implement`. Each task = one test + one implementation + one commit.
metadata:
  aiadev:
    version: 0.2.0
    inputs:
    - type: file
      path: specs/<branch>/plan.md
    outputs:
    - type: file
      path: specs/<branch>/tasks.md
    requires:
    - constitution
    - templates/tasks-template.md
    handoffs:
    - implement
    - analyze
---

# Tasks

Convert a plan into the ordered list of atomic units that `implement` will execute.

## Preconditions

- Run `aiadev preflight tasks --feature <slug>`; abort on non-zero exit unless `AIADEV_PREFLIGHT=warn`.
- `plan.md` exists with a fully ticked Constitution Check.
- `templates/tasks-template.md` is available.

## Loop

1. **Copy the template** to `specs/<branch>/tasks.md`.
2. **Read the plan's phase breakdown.** For each phase, produce the tasks that realize it.
3. **For every task, fill the block**:
   - `T<NNN>` id, monotonic within the file.
   - Short title that fits in a commit message.
   - `Status: pending`; `Depends on:` task ids or `—`.
   - `Files:` create / modify / test lists. Exact paths.
   - `Spec scenarios:` canonical notation from the template.
   - `Acceptance:` the checklist every task ends with (test failed, then passed, no regression, commit).
4. **Size rule.** A task should be doable in 2-15 minutes. If bigger, split. If smaller, fold.
5. **Parallelization hints.** Mark groups of tasks that touch disjoint files in the "Parallel group" section. Everything else is serial.
6. **Post-task checklist.** Fill `{{TEST_COMMAND}}` from the active preset.
7. **Dispatch review.** If a task reviewer agent exists, use it; otherwise have the user read the tasks list.

## Rules

- Every spec scenario appears in at least one task: run `aiadev preflight implement --feature <slug>` and fix the scenario/task coverage errors it reports.
- Quote data-model constraints (size, enum values, nullability) verbatim in the task that touches them.
- Task dependencies form a DAG; `implement` will refuse a cycle.
- No task without a test step; no time estimates.
- **Heading shape is part of the contract.** Tasks are `### T<NNN> — Title` (H3). If you want to group tasks visually by phase, use a bold paragraph or a bullet list — never a heading that demotes the task to `####`. H3 stays canonical.
- **Status vocabulary is fixed.** Use exactly one of `pending`, `in_progress`, `blocked`, `done`. Don't invent synonyms.

## Hand-off

- Tasks written and reviewed → invoke `implement`.
- Drift suspected between spec / plan / tasks → invoke `analyze` before implementing.
