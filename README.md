# AI-Augmented Developer

AI-Augmented Developer is a complete software development workflow for your coding agents, built on top of a set of composable "skills" and some initial instructions that make sure your agent uses them.

## How it works

It starts from the moment you fire up your coding agent. As soon as it sees that you're building something, it *doesn't* just jump into trying to write code. Instead, it steps back and asks you what you're really trying to do.

Once it's teased a spec out of the conversation, it shows it to you in chunks short enough to actually read and digest.

After you've signed off on the design, your agent puts together an implementation plan that's clear enough for an enthusiastic junior engineer with poor taste, no judgement, no project context, and an aversion to testing to follow. It emphasizes true red/green TDD, YAGNI (You Aren't Gonna Need It), and DRY.

Next up, once you say "go", the `implement` skill takes over: it dispatches one fresh subagent per task, runs a spec compliance review and a code quality review after each, and moves forward only when both pass. The agent can run through several tasks unattended as long as the plan stays accurate — your job is to check in, not to babysit every step.

There's a bunch more to it, but that's the core of the system. And because the skills trigger automatically, you don't need to do anything special. Your coding agent just has AI-Augmented Developer superpowers.

## Installation

**Note:** Installation differs by platform. Claude Code and Cursor have built-in plugin support. Codex and OpenCode require manual setup.

### Claude Code

```bash
/plugin marketplace add suportly/ai-augmented-developer
/plugin install ai-augmented-developer@ai-augmented-developer-marketplace
```

### Cursor

```text
/add-plugin https://github.com/suportly/ai-augmented-developer
```

### Gemini CLI

```bash
gemini extensions install https://github.com/suportly/ai-augmented-developer
```

To update:

```bash
gemini extensions update ai-augmented-developer
```

### Codex

Tell Codex:

```
Fetch and follow instructions from https://raw.githubusercontent.com/suportly/ai-augmented-developer/refs/heads/main/.codex/INSTALL.md
```

**Detailed docs:** [docs/README.codex.md](docs/README.codex.md)

### OpenCode

Tell OpenCode:

```
Fetch and follow instructions from https://raw.githubusercontent.com/suportly/ai-augmented-developer/refs/heads/main/.opencode/INSTALL.md
```

**Detailed docs:** [docs/README.opencode.md](docs/README.opencode.md)

### Verify Installation

Start a new session in your chosen platform and ask for something that should trigger a skill (for example, "help me plan this feature" or "let's debug this issue"). The agent should automatically invoke the relevant skill.

## The Basic Workflow

1. **specify** — Activates first. Turns a natural-language demand into a `spec.md` under `specs/<branch>/`, surfacing any ambiguity as `[NEEDS CLARIFICATION: …]` markers instead of guessing.

2. **clarify** — Walks the user through the clarification markers one at a time and rewrites the spec with the answers. The spec stays unapproved while any marker is unresolved.

3. **plan** — Turns the clean spec into a `plan.md` that fills the Constitution Check table, maps project structure changes, and splits the work into phases.

4. **tasks** — Decomposes the plan into an ordered `tasks.md` where each task = one failing test + one implementation + one commit, with dependencies declared.

5. **implement** — Dispatches one fresh subagent per task with a two-stage review (spec compliance, then code quality) before advancing. One task per commit; never skip either review.

6. **analyze**, **checklist** — Cross-checks. `analyze` reports drift between spec, plan, tasks, and actual code. `checklist` runs a category pass (security, performance, accessibility, i18n, privacy, observability).

7. **test-driven-development**, **systematic-debugging** — Invoked inside `implement`. RED-GREEN-REFACTOR for new work; four-phase root-cause investigation for failures.

8. **requesting-code-review**, **finishing-a-branch** — Pre-PR review and merge hygiene. Close the loop back to the spec.

**The agent checks for relevant skills before any task.** These are mandatory workflows, not suggestions.

## What's Inside

### Skills (14 generic + preset)

**Pipeline**
- **specify** — Natural-language demand → numbered `spec.md` with `[NEEDS CLARIFICATION]` markers for ambiguity.
- **clarify** — Surfaces those markers one at a time and rewrites the spec with the answers.
- **plan** — Turns an approved spec into `plan.md` with a mandatory Constitution Check.
- **tasks** — Ordered `tasks.md`; one task = one test + one implementation + one commit.
- **implement** — Fresh subagent per task with two-stage review (spec compliance, then code quality).
- **analyze** — Gap report between spec, plan, tasks, and code.
- **checklist** — Category pass: security, performance, accessibility, i18n, privacy, observability.
- **constitution** — Amend the framework/preset/project constitution through the documented process.

**Quality**
- **using-ai-augmented-developer** — Meta-skill that orients the agent to the catalog and skill rule.
- **test-driven-development** — RED-GREEN-REFACTOR cycle, strictly enforced.
- **systematic-debugging** — 4-phase root-cause investigation before any fix.
- **requesting-code-review** — Pre-PR checklist and reviewer agent dispatch.
- **finishing-a-branch** — PR creation, merge decision, cleanup.
- **frontend-design** — Production-grade UI with distinctive, non-generic aesthetics.

**Stack skills (via presets)**

Stack-specific skills live under `presets/<preset>/skills/` and load only when that preset is active. The bundled `django-drf-react` preset ships:

- **django-patterns** — App / model / serializer / view / URL conventions.
- **ai-integration** — LiteLLM + Claude Agent SDK providers.
- **celery-async** — Background task patterns, scheduling, retries.
- **autodev-pipeline** — Proactive auto-development pipeline.
- **deploy** — Cloud Run + EAS deployment runbooks.
- **run-tests** — pytest backend + Jest frontend entry point.

A minimal `lean` preset is also available for projects with an exotic stack. See `presets/catalog.json` for the full list.

### Commands

Skills are invoked directly by name — there are no thin command wrappers in v0.2. Earlier versions shipped `/brainstorm`, `/write-plan`, `/execute-plan`, `/speckit`, `/debug`; these redirected to skills with no added behavior and were removed. Call the skills themselves instead.

### Agents (3 total)

- **spec-document-reviewer** — Validates specs for completeness, clarity, and testability
- **plan-document-reviewer** — Validates plans for TDD compliance, exact file paths, and step granularity
- **code-reviewer** — Reviews code for security, spec alignment, and quality

## Philosophy

- **Test-Driven Development** — Write tests first, always
- **Design before code** — No implementation without an approved spec
- **Systematic over ad-hoc** — Process over guessing
- **Complexity reduction** — Simplicity as primary goal
- **Evidence over claims** — Verify before declaring success

## Updating

```bash
/plugin update ai-augmented-developer
```

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for the full workflow (issue-first, one concern per PR, skill frontmatter rules). Bug reports and security issues follow [SECURITY.md](./SECURITY.md). Changes are logged in [CHANGELOG.md](./CHANGELOG.md).

## Credits

This framework builds on prior work from `obra/superpowers` and `github/spec-kit`. See [CREDITS.md](./CREDITS.md) for the full attribution list.

## License

MIT License — see LICENSE file for details

## Support

- **Issues**: https://github.com/suportly/ai-augmented-developer/issues
