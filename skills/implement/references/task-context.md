# Task-context integration (opt-in)

Read this only when the integration is on: the active preset's `preset.yaml`
declares `task_context: true`, or the orchestrator was invoked with
`aiadev preflight implement --task-context`.

Story 1 of `specs/0014-bmad-inspired-evolutions/spec.md` adds the
`task-context` skill (`skills/task-context/SKILL.md`), which composes a
per-task file at `specs/<branch>/task-context/<TID>-<slug>.md` ahead of the
implementer dispatch. When neither flag is set, the inline implementer prompt
in `SKILL.md` runs byte-for-byte unchanged; this wiring is purely additive.

## Extra steps (between "treat `in_progress` as `pending`" and "dispatch")

3.5. **Compose the file.** Invoke the `task-context` skill for `<TID>`:

```bash
python -c "from pathlib import Path; from aiadev.task_context import compose; print(compose(Path.cwd(), '<TID>'))"
```

If a file already exists for this `<TID>`, check `is_stale` first and skip the
recompose when it returns `False` (reused across retries in a session):

```bash
python -c "from pathlib import Path; from aiadev.task_context import is_stale; print(is_stale(Path('specs/<branch>/task-context/<TID>-<slug>.md')))"
```

3.6. **Replace the implementer prompt** with this shorter one (it loads the
context by path instead of the inline Spec / Plan / Files blocks):

```markdown
You are implementing Task <TID> of an approved plan.

Your full per-task context file lives at:
specs/<branch>/task-context/<TID>-<slug>.md

Read it first. It contains the spec slice, plan slice, files-to-modify with
excerpts, the TDD checklist, and a pointer to the previous task-context.

Workflow: test-first. Write a failing test, confirm it fails for the right
reason, implement the minimum code to pass, confirm it passes. Run only the
tests that exercise the changed code.

Return exactly one status as the first line of your response:
DONE | DONE_WITH_CONCERNS | NEEDS_CONTEXT | BLOCKED
```

Status handling, reviewer and `aiadev tasks done` are unchanged.
