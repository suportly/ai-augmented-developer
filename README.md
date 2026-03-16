# AI-Augmented Developer

AI-Augmented Developer is a complete software development workflow for your coding agents, built on top of a set of composable "skills" and some initial instructions that make sure your agent uses them.

## How it works

It starts from the moment you fire up your coding agent. As soon as it sees that you're building something, it *doesn't* just jump into trying to write code. Instead, it steps back and asks you what you're really trying to do.

Once it's teased a spec out of the conversation, it shows it to you in chunks short enough to actually read and digest.

After you've signed off on the design, your agent puts together an implementation plan that's clear enough for an enthusiastic junior engineer with poor taste, no judgement, no project context, and an aversion to testing to follow. It emphasizes true red/green TDD, YAGNI (You Aren't Gonna Need It), and DRY.

Next up, once you say "go", it launches a *subagent-driven-development* process, having agents work through each engineering task, inspecting and reviewing their work, and continuing forward. It's not uncommon for the agent to be able to work autonomously for a couple of hours at a time without deviating from the plan you put together.

There's a bunch more to it, but that's the core of the system. And because the skills trigger automatically, you don't need to do anything special. Your coding agent just has AI-Augmented Developer superpowers.

## Installation

**Note:** Installation differs by platform. Claude Code and Cursor have built-in plugin marketplaces. Codex and OpenCode require manual setup.

### Claude Code

```bash
/plugin install https://github.com/suportly/ai-augmented-developer
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

### OpenCode

Tell OpenCode:

```
Fetch and follow instructions from https://raw.githubusercontent.com/suportly/ai-augmented-developer/refs/heads/main/.opencode/INSTALL.md
```

### Verify Installation

Start a new session in your chosen platform and ask for something that should trigger a skill (for example, "help me plan this feature" or "let's debug this issue"). The agent should automatically invoke the relevant skill.

## The Basic Workflow

1. **brainstorming** - Activates before writing code. Refines rough ideas through questions, explores alternatives, presents design in sections for validation. Saves design document.

2. **writing-plans** - Activates with approved design. Breaks work into bite-sized tasks (2-5 minutes each). Every task has exact file paths, complete code, and verification steps.

3. **speckit** - Full pipeline from demand to Pull Request: specify → plan → tasks → implement → PR. Designed for proactive, automated development flows.

4. **subagent-driven-development** - Activates with plan. Dispatches fresh subagent per task with two-stage review (spec compliance, then code quality).

5. **test-driven-development** - Activates during implementation. Enforces RED-GREEN-REFACTOR: write failing test, watch it fail, write minimal code, watch it pass, commit.

6. **requesting-code-review** - Activates before opening a PR. Reviews against the plan and spec, reports issues by severity.

7. **finishing-a-branch** - Activates when tasks complete. Verifies tests pass, opens PR with full traceability, cleans up.

**The agent checks for relevant skills before any task.** These are mandatory workflows, not suggestions.

## What's Inside

### Skills Library

**Testing**
- **test-driven-development** - RED-GREEN-REFACTOR cycle, strictly enforced

**Debugging**
- **systematic-debugging** - 4-phase root cause process before any fix

**Planning & Collaboration**
- **brainstorming** - Socratic design refinement with hard gate before code
- **writing-plans** - Detailed, bite-sized implementation plans
- **speckit** - Full autodev pipeline: specify → plan → tasks → implement → PR
- **subagent-driven-development** - Fast iteration with two-stage review per task
- **requesting-code-review** - Pre-PR checklist and review dispatch
- **finishing-a-branch** - PR creation, merge decision, and cleanup

**Project Skills**
- **run-tests** - Run the full test suite across all project layers
- **frontend-design** - Production-grade UI with distinctive aesthetics
- **deploy** - Deploy to cloud infrastructure or mobile stores
- **ai-integration** - Integrate AI providers, streaming responses, and autonomous agents
- **autodev-pipeline** - Build and use the proactive auto-development pipeline
- **django-patterns** - Conventions for apps, models, serializers, views, and URLs
- **celery-async** - Background task patterns, scheduling, retry, and debugging

**Meta**
- **using-ai-augmented-developer** - Introduction to the skills system

### Agents

- **spec-document-reviewer** - Validates specs for completeness and testability
- **plan-document-reviewer** - Validates plans for TDD compliance and exactness
- **code-reviewer** - Reviews code for security, correctness, and spec alignment

## Philosophy

- **Test-Driven Development** - Write tests first, always
- **Design before code** - No implementation without an approved spec
- **Systematic over ad-hoc** - Process over guessing
- **Complexity reduction** - Simplicity as primary goal
- **Evidence over claims** - Verify before declaring success

## Updating

```bash
/plugin update ai-augmented-developer
```

## Contributing

Skills live directly in this repository. To contribute:

1. Fork the repository
2. Create a branch for your skill
3. Submit a PR

## License

MIT License - see LICENSE file for details

## Support

- **Issues**: https://github.com/suportly/ai-augmented-developer/issues
