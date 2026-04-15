# {{PROJECT_NAME}} — lean preset

> Generated from the `lean` preset. This preset ships only the
> framework-level pipeline — no stack-specific skills, no project layout
> opinion.

You are working inside a project that uses the AI-Augmented Developer
framework's `specify → clarify → plan → tasks → implement` pipeline. The
framework-level `constitution.md` applies; no preset articles are added.

Use this preset when:

- The stack is exotic (not Django + React, not Expo, not a common web app).
- You want the framework's process discipline but will add stack skills
  manually or through an extension.
- You are evaluating the framework before committing to a full preset.

## Pipeline

`specify → clarify → plan → tasks → implement`

Quality skills available: `test-driven-development`, `systematic-debugging`,
`requesting-code-review`, `finishing-a-branch`, `analyze`, `checklist`,
`frontend-design` (when applicable).

## Project layout

This preset makes no assumptions. Define your own layout in the project's
own amended `constitution.md` if any.

## Quick commands

None shipped by this preset. Add the commands your stack actually uses to
this file before the first `implement` run — agents rely on them.

## What got installed

The installer dropped the complete framework pipeline into this project:

- `.claude/commands/` — 15 slash commands (pipeline + `/sync`).
- `.claude/agents/` — 3 reviewer agents (spec, plan, code).
- `.claude/skills/` — 14 framework-generic skills.
- `.claude/rules/` — 5 coding rules (code-style, testing, api-conventions,
  security, git-workflow).

Run `aiadev sync` whenever you pull a new `aiadev` version or edit the
project's stack so this file's Detected-stack block stays current.

<!-- aiadev:auto-stack:start -->
## Detected stack

_Run `aiadev sync` to populate this block from your project's
package.json / pyproject.toml / Makefile / docker-compose / workflows._
<!-- aiadev:auto-stack:end -->

