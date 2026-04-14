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

1. **brainstorming** — Activates before writing code. Refines rough ideas through questions, explores alternatives, presents design in sections for validation. Saves spec document.

2. **writing-plans** — Activates with approved design. Breaks work into bite-sized tasks (2-5 minutes each). Every task has exact file paths, complete code, and verification steps.

3. **implement** — Activates with an approved plan and tasks list. Dispatches a fresh subagent per task with two-stage review (spec compliance, then code quality) before advancing.

4. **test-driven-development** — Activates during implementation. Enforces RED-GREEN-REFACTOR: write failing test, watch it fail, write minimal code, watch it pass, commit.

5. **requesting-code-review** — Activates before opening a PR. Reviews against plan and spec, reports issues by severity. Critical issues block progress.

6. **finishing-a-branch** — Activates when tasks complete. Verifies tests pass, opens PR with full traceability (issue → spec → plan → code), cleans up.

**The agent checks for relevant skills before any task.** These are mandatory workflows, not suggestions.

## What's Inside

### Skills (15 total)

**Workflow**
- **using-ai-augmented-developer** — Entry point. Ensures skills are invoked before any response.
- **brainstorming** — Socratic design refinement with hard gate before any code
- **writing-plans** — Detailed, bite-sized implementation plans with TDD steps
- **implement** — Fresh subagent per task with two-stage review (spec compliance, then code quality)
- **test-driven-development** — RED-GREEN-REFACTOR cycle, strictly enforced
- **systematic-debugging** — 4-phase root cause investigation before any fix
- **requesting-code-review** — Pre-PR checklist and reviewer agent dispatch
- **finishing-a-branch** — PR creation, merge decision, cleanup

**Project Skills**
- **run-tests** — Run the full test suite across all project layers
- **frontend-design** — Production-grade UI with distinctive, non-generic aesthetics
- **deploy** — Deploy to cloud infrastructure or mobile app stores
- **ai-integration** — Integrate AI providers, streaming responses, and autonomous agents
- **autodev-pipeline** — Build and use the proactive auto-development pipeline
- **django-patterns** — Conventions for apps, models, serializers, views, and URLs
- **celery-async** — Background task patterns, scheduling, retry logic, and debugging

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

This framework builds on prior work from `obra/superpowers`, `github/spec-kit`, `contains-studio/agents`, and internal StriveX playbooks. See [CREDITS.md](./CREDITS.md) for the full attribution list.

## License

MIT License — see LICENSE file for details

## Support

- **Issues**: https://github.com/suportly/ai-augmented-developer/issues
