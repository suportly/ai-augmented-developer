---
name: using-ai-augmented-developer
description: Meta-skill that explains the skill catalog and when to invoke each one. Load it at the start of a conversation to orient the agent before any code-writing action.
---

<SUBAGENT-STOP>
If you were dispatched as a subagent to execute a specific task, skip this skill.
</SUBAGENT-STOP>

## Why this skill exists

The framework only works when the agent picks the right skill for what the user asked. This file is the lookup table and the rules for using it.

## The rule

Before any action that **writes code or state** — creating files, running migrations, committing, opening PRs — check whether a skill applies and invoke it.

Clarifying questions and codebase exploration are **not** write actions. They are allowed and encouraged during `specify` and `clarify` phases, and any time you cannot pick a skill without more information.

If two skills seem to apply, prefer the one further upstream in the pipeline: `specify` beats `plan`, `plan` beats `implement`, `implement` beats stack-specific skills.

## Instruction priority

1. Explicit user instructions and project-level `CLAUDE.md` / `GEMINI.md` / `AGENTS.md`.
2. These skills, when they apply.
3. Default system behavior.

When in conflict, the user wins.

## Available skills

### Pipeline skills (invoke one of these before writing code)

| Skill | Use when |
|---|---|
| `specify` *(phase 3)* | the user describes a demand in natural language and no `spec.md` exists yet |
| `clarify` *(phase 3)* | `spec.md` exists but contains `[NEEDS CLARIFICATION]` markers |
| `plan` *(phase 3)* | spec is clean; no `plan.md` yet |
| `tasks` *(phase 3)* | `plan.md` is approved; no `tasks.md` yet |
| `analyze` *(phase 3)* | checking drift between spec/plan/tasks/code |
| `checklist` *(phase 3)* | applying a security/perf/a11y/i18n review |
| `implement` | `tasks.md` exists and is approved; time to execute |
| `test-driven-development` | writing any test-backed code inside `implement` |
| `systematic-debugging` | a test is failing or behavior is unexpected |
| `requesting-code-review` | the branch is ready, before opening the PR |
| `finishing-a-branch` | review approved; time to open the PR and clean up |

> The entries marked *(phase 3)* land in v0.2. Until then, `brainstorming` and `writing-plans` serve as their predecessors. See `CHANGELOG.md`.

### Preset skills

Skills specific to a stack (Django + React, React Native + Expo, etc.) live under `presets/<preset>/skills/` and load only when that preset is active. Check `CLAUDE.md` to see which preset the current project uses.

## How to invoke

- **Claude Code:** use the `Skill` tool.
- **Gemini CLI:** use `activate_skill`.
- **Cursor / OpenCode / Codex:** skills are picked up from `skills/` automatically.

## Rationalization check

If you catch yourself thinking any of these, stop and pick a skill:

- "This is just a simple question" — the user asked for a change, not a lecture.
- "I'll just do this one small edit first" — one small edit without a skill is how drift starts.
- "Skills are overkill here" — if a skill applies and you skip it, the next conversation has no trail.

Conversely, if none of the skills fit (pure research, reading code the user asked you to read, answering a factual question), proceed without invoking one. Do not force a skill where it adds no value.
