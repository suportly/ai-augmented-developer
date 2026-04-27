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
| `specify` | the user describes a demand in natural language and no `spec.md` exists yet |
| `clarify` | `spec.md` exists but contains `[NEEDS CLARIFICATION]` markers |
| `plan` | spec is clean; no `plan.md` yet |
| `tasks` | `plan.md` is approved; no `tasks.md` yet |
| `analyze` | checking drift between spec / plan / tasks / code |
| `checklist` | applying a category pass (security, performance, a11y, i18n, privacy, observability) |
| `implement` | `tasks.md` exists and is approved; time to execute |
| `constitution` | amending `constitution.md` (framework, preset, or project) |
| `test-driven-development` | writing any test-backed code inside `implement` |
| `systematic-debugging` | a test is failing or behavior is unexpected |
| `requesting-code-review` | the branch is ready, before opening the PR |
| `finishing-a-branch` | review approved; time to open the PR and clean up |

> **Reconnaissance before `specify`.** When a demand touches an app, service, or surface you have not yet inspected this session, perform a Reconnaissance pass before drafting any user story — read the entry point, read the auth/session module, grep for the integration points, and record the findings in the spec's recon section. See [skills/specify/SKILL.md](../specify/SKILL.md) for the full procedure.

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
