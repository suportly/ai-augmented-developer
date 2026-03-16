---
name: using-ai-augmented-developer
description: Use when starting any conversation - establishes how to find and use skills, requiring skill invocation before ANY response including clarifying questions
---

<SUBAGENT-STOP>
If you were dispatched as a subagent to execute a specific task, skip this skill.
</SUBAGENT-STOP>

<EXTREMELY-IMPORTANT>
If you think there is even a 1% chance a skill might apply to what you are doing, you ABSOLUTELY MUST invoke the skill.

IF A SKILL APPLIES TO YOUR TASK, YOU DO NOT HAVE A CHOICE. YOU MUST USE IT.

This is not negotiable. This is not optional.
</EXTREMELY-IMPORTANT>

## Instruction Priority

1. **User's explicit instructions** (CLAUDE.md, GEMINI.md, AGENTS.md, direct requests) — highest priority
2. **AI-Augmented Developer skills** — override default system behavior where they conflict
3. **Default system prompt** — lowest priority

## Available Skills

### Workflow Skills (invoke BEFORE any implementation)

| Skill | Trigger |
|-------|---------|
| `brainstorming` | "build X", "add feature", "create component", "implement" |
| `writing-plans` | "plan this", "I have a spec", "need a plan" |
| `speckit` | "autodev", "pipeline", "specify→plan→implement" |
| `test-driven-development` | any feature or bugfix implementation |
| `systematic-debugging` | bug, test failure, unexpected behavior |
| `subagent-driven-development` | "execute the plan", "implement all tasks" |
| `requesting-code-review` | "review code", "before PR", "check my changes" |
| `finishing-a-branch` | "merge", "open PR", "done with branch" |

### Project Skills (stack-specific)

| Skill | Trigger |
|-------|---------|
| `run-tests` | "run tests", "check if tests pass", after modifying code |
| `frontend-design` | "build UI", "create component", "design page" |
| `deploy` | "deploy", "publish", "push to production" |
| `ai-integration` | "add AI", "LiteLLM", "Claude SDK", "streaming" |
| `autodev-pipeline` | "autodev", "issue tracker", "proactive dev" |
| `django-patterns` | "new app", "new model", "new endpoint", "migration" |
| `celery-async` | "async task", "background job", "Celery", "scheduled" |

## The Rule

**Invoke relevant or potentially relevant skills BEFORE any response or action.**

Even a 1% chance a skill might apply means you should invoke it.

## Red Flags (You're Rationalizing)

| Thought | Reality |
|---------|---------|
| "This is just a simple question" | Questions are tasks. Check for skills. |
| "I need more context first" | Skill check comes BEFORE clarifying questions. |
| "Let me explore the codebase first" | Skills tell you HOW to explore. Check first. |
| "This doesn't need a formal skill" | If a skill exists, use it. |
| "I'll just do this one thing first" | Check BEFORE doing anything. |
| "The skill is overkill" | Simple things become complex. Use it. |

## Skill Priority

1. **Process skills first** (brainstorming, debugging) — determine HOW to approach
2. **Implementation skills second** (frontend-design, django-patterns) — guide execution

"Let's build X" → `brainstorming` first, then implementation skills.
"Fix this bug" → `systematic-debugging` first, then domain skills.

## How to Access Skills

**Claude Code:** Use the `Skill` tool.
**Gemini CLI:** Use the `activate_skill` tool.
**Cursor / OpenCode / Codex:** Skills load automatically from the `skills/` directory.
