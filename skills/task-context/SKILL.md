---
name: task-context
description: Compose a rich per-task context file (specs/<branch>/task-context/<TID>-<slug>.md) before each implementer dispatch. Opt-in; default off.
version: 0.1.0
inputs:
  - type: text
    description: Task ID (e.g. T003) the implementer is about to pick up.
outputs:
  - type: file
    path: specs/<branch>/task-context/<TID>-<slug>.md
    description: Self-contained per-task brief consumed by the implementer subagent.
requires:
  - templates/task-context-template.md
  - aiadev.task_context
handoffs:
  - implement
---

# Task context

Produce a per-task context file that gives the implementer subagent
everything it needs in one self-contained artifact: the spec scenarios
this task exercises, the matching plan block, an excerpt of every file
to modify, the TDD checklist, and a pointer back to the previous
task-context for continuity.

**Announce at start:** "Using the task-context skill. I will compose
the per-task context file before the next implementer dispatch."

## When to use

- The active preset has `task_context: true` in its `preset.yaml`, OR
- The orchestrator was invoked with `aiadev preflight implement --task-context`.

When neither flag is set, the `implement` skill uses its inline prompt
(default behavior, byte-for-byte unchanged from before this skill
existed). The task-context skill never runs implicitly.

## Loop

1. Read the task ID from the orchestrator (e.g. `T003`).
2. Render the file via the helper:

   ```bash
   python -c "from pathlib import Path; from aiadev.task_context import compose; print(compose(Path.cwd(), 'T003'))"
   ```

   The helper handles spec/plan/tasks slicing, file excerpts (40-line
   cap on `modify:` paths, no excerpt for `create:` / `test:` paths),
   the static TDD checklist, and the previous-task pointer.
3. Optionally check staleness before reuse:

   ```bash
   python -c "from pathlib import Path; from aiadev.task_context import is_stale; print(is_stale(Path('specs/0001-x/task-context/T003-foo.md')))"
   ```

   Recompose if the call returns `True` — a referenced file changed
   after the brief was generated.
4. Hand the resulting path to the implementer subagent prompt as the
   primary context artifact.

## Rules

- The skill is a leaf in the pipeline graph. It does not invoke any
  other skill — calling `aiadev.task_context` via `python -c` is a
  tooling invocation, not a skill invocation.
- Generated files under `specs/<branch>/task-context/` are
  regenerated each loop. Do not hand-edit them; changes are lost on
  the next compose.
- The default mtime probe is hermetic; production wiring may inject a
  git-log probe via the `newest_modification` callable in
  `is_stale(...)`.

## Hand-off

The `implement` skill consumes the rendered file as the implementer's
primary context. See `skills/implement/SKILL.md` for the wiring
details (opt-in via preset.yaml `task_context: true` or the
`--task-context` preflight flag).
