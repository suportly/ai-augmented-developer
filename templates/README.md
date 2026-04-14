# Templates

This directory holds the canonical templates used by the framework's
pipeline skills. They are copied into a project's `specs/<branch>/`
directory by `aiadev init --feature <name>` and then filled in by the
`specify`, `clarify`, `plan`, `tasks`, and `checklist` skills.

| File | Produced by | Consumed by |
|---|---|---|
| [`spec-template.md`](./spec-template.md) | `specify` | `clarify`, `plan` |
| [`plan-template.md`](./plan-template.md) | `plan` | `tasks`, `implement` |
| [`tasks-template.md`](./tasks-template.md) | `tasks` | `implement` |
| [`checklist-template.md`](./checklist-template.md) | `checklist` | reviewers |
| [`constitution-template.md`](./constitution-template.md) | `aiadev init` | project maintainers |
| [`agent-file-template.md`](./agent-file-template.md) | `aiadev install` | the coding agent at session start |
| [`commands/command-template.md`](./commands/command-template.md) | contributors adding plugin commands | agent runtime |

## Conventions

- Placeholders use `{{UPPER_SNAKE}}` (e.g. `{{FEATURE_NAME}}`). `aiadev`
  substitutes them on `init`/`install`.
- `[NEEDS CLARIFICATION: <question>]` is a live marker read by the
  `clarify` skill. Any spec or plan containing this marker is considered
  unapproved.
- Section headings are stable — validators grep for them. If you rename
  a section, update `schemas/` and the skill that produces or consumes
  the file.
- Keep each template terse. The agent fills them in; long preamble
  competes with the actual content.

## When to edit a template

- New articles in `constitution.md` should be mirrored as new rows in
  `plan-template.md`'s Constitution Check table.
- New skills that produce a new artifact get a new template here.
- Stack-specific templates live in the preset (`presets/<preset>/templates/`),
  not here.
