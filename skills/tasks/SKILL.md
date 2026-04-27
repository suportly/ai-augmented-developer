---
name: tasks
description: Decompose an approved plan.md into an ordered tasks.md ready for `implement`. Each task = one test + one implementation + one commit.
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

**Announce at start:** "Using the tasks skill. One task = one test + one implementation + one commit."

## Preconditions

- Run pre-flight first: `aiadev preflight tasks --feature <slug>`. Abort on non-zero exit unless `AIADEV_PREFLIGHT=warn` is set.
- `plan.md` exists with a fully ticked Constitution Check.
- `templates/tasks-template.md` is available.

## Loop

1. **Copy the template** to `specs/<branch>/tasks.md`.
2. **Read the plan's phase breakdown.** For each phase, produce the tasks that realize it.
3. **For every task, fill the block**:
   - `T<NNN>` id, monotonic within the file.
   - Short title that fits in a commit message.
   - `Status: pending`.
   - `Depends on:` list of task ids or `—`.
   - `Files:` create / modify / test lists. Exact paths.
   - `Spec scenarios:` the spec scenarios this task exercises.
   - `Acceptance:` the checklist every task ends with (test failed, then passed, no regression, commit).
4. **Size rule.** A task should be doable in 2-15 minutes. If bigger, split. If smaller, fold.
5. **Parallelization hints.** Mark groups of tasks that touch disjoint files in the "Parallel group" section. Everything else is serial.
6. **Post-task checklist.** Fill `{{TEST_COMMAND}}` from the active preset.
7. **Dispatch review.** If a task reviewer agent exists, use it; otherwise have the user read the tasks list.

## Rules

- Every spec acceptance scenario must appear in at least one task. Grep to verify.
- No task without a test step.
- Task dependencies form a DAG; `implement` will refuse a cycle.
- Never put time estimates in the task. Estimates drift; the acceptance checklist is what matters.

## Hand-off

- Tasks written and reviewed → invoke `implement`.
- Drift suspected between spec / plan / tasks → invoke `analyze` before implementing.
