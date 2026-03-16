# AI-Augmented Developer

A Claude Code skill package implementing a complete AI-augmented software development workflow, adapted for modern full-stack projects with Django + React + AI.

Inspired by [superpowers](https://github.com/obra/superpowers), expanded with patterns and skills from the [Strivex](https://github.com/alairjt/strivex) and [Activi.dev](https://github.com/alairjt/activi.dev) projects.

## Supported Stack

### Backend
- Python 3.12 + Django 5.2 + DRF
- Celery 5 + Redis (async queues)
- PostgreSQL 16
- LiteLLM (Gemini, Groq, Anthropic)
- Claude Agent SDK

### Frontend
- React 18 + TypeScript
- Material UI v5 / shadcn/ui
- TanStack Query v5
- Framer Motion
- Vite

### Mobile
- React Native + Expo
- EAS Build / EAS Update

### Infrastructure
- Docker + Docker Compose
- Nginx
- GCP Cloud Run

## Development Workflow

```
brainstorming → writing-plans → speckit
     ↓
subagent-driven-development
     ↓
test-driven-development
     ↓
requesting-code-review
     ↓
finishing-a-branch
```

## Available Skills

### Workflow (Process)
| Skill | When to Use |
|-------|-------------|
| `brainstorming` | Before any feature — refines requirements, generates spec |
| `writing-plans` | After spec approved — creates bite-sized implementation plan |
| `speckit` | Full specify→plan→tasks→implement flow (autodev pipeline) |
| `test-driven-development` | When implementing any feature or bugfix |
| `systematic-debugging` | When encountering any bug or failure |
| `subagent-driven-development` | Executing plans with subagents + dual review |
| `requesting-code-review` | Before opening a PR |
| `finishing-a-branch` | After code review approved |

### Project (Stack-Specific)
| Skill | When to Use |
|-------|-------------|
| `run-tests` | After modifying code to catch regressions |
| `frontend-design` | Create high-quality UI components and pages |
| `deploy` | Deploy backend, frontend, or mobile to production |
| `ai-integration` | Integrate LiteLLM, Claude Agent SDK, or other AI providers |
| `autodev-pipeline` | Build or use the proactive auto-development pipeline |
| `django-patterns` | New Django apps, models, serializers, views |
| `celery-async` | Create or debug async Celery tasks |

## Installation

### Claude Code
```
/plugin install https://github.com/suportly/ai-augmented-developer
```

### Cursor
```
/add-plugin https://github.com/suportly/ai-augmented-developer
```

### Gemini CLI
```bash
gemini extensions install https://github.com/suportly/ai-augmented-developer
```

### Codex
```bash
git clone https://github.com/suportly/ai-augmented-developer.git ~/.codex/ai-augmented-developer
mkdir -p ~/.agents/skills
ln -s ~/.codex/ai-augmented-developer/skills ~/.agents/skills/ai-augmented-developer
```
See full instructions in [`.codex/INSTALL.md`](.codex/INSTALL.md).

### OpenCode
```bash
git clone https://github.com/suportly/ai-augmented-developer.git ~/.config/opencode/ai-augmented-developer
mkdir -p ~/.config/opencode/skills
ln -s ~/.config/opencode/ai-augmented-developer/skills ~/.config/opencode/skills/ai-augmented-developer
```
See full instructions in [`.opencode/INSTALL.md`](.opencode/INSTALL.md).

### Manual (any project)
```bash
mkdir -p .claude/skills
cp -r /path/to/ai-augmented-developer/skills/* .claude/skills/
```

## Philosophy

- **TDD mandatory** — tests first, always
- **Design before code** — never skip brainstorming
- **Subagents for quality** — spec + code review on each task
- **Async-first** — Celery for anything that can run in background
- **AI-first** — LiteLLM as abstraction layer, Claude Agent SDK for autonomous execution
- **YAGNI** — minimum necessary complexity
- **DRY** — reuse established patterns from reference projects
