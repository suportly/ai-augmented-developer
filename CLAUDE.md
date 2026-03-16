# AI-Augmented Developer

You are working with the AI-Augmented Developer framework — a structured development workflow for full-stack projects combining Django + React + AI.

## Start Here

**Before writing any code**, invoke the appropriate skill:

| What you're doing | Skill to invoke |
|-------------------|----------------|
| Starting a new feature or task | `brainstorming` |
| Have a spec, need an implementation plan | `writing-plans` |
| Have a plan, ready to implement | `subagent-driven-development` |
| Implementing any feature/fix | `test-driven-development` |
| Hit a bug or test failure | `systematic-debugging` |
| Ready to open a PR | `requesting-code-review` |
| Code review approved | `finishing-a-branch` |
| Adding AI (LiteLLM/Claude SDK) | `ai-integration` |
| New Django app/model/view/URL | `django-patterns` |
| New Celery task or async flow | `celery-async` |
| AutoDev pipeline feature | `autodev-pipeline` |
| UI component or page | `frontend-design` |
| Running tests | `run-tests` |
| Deploying to production | `deploy` |

## Core Principles

1. **Design before code** — Always brainstorm first. No code without an approved spec.
2. **TDD mandatory** — Write failing test → implement → verify passing. No exceptions.
3. **Subagents for quality** — Spec review + code quality review on every task.
4. **Async-first** — Operations > 2 seconds go to Celery. Never block the request cycle.
5. **Provider Pattern** — All external integrations use the Provider Pattern.
6. **API-First** — All endpoints under `/api/v1/<app>/`. Frontend consumes via TanStack Query.
7. **Security by default** — Sensitive data encrypted. All endpoints authenticated. User isolation enforced.
8. **YAGNI** — Build only what's needed. Minimum complexity for current requirements.
9. **Evidence over claims** — Verify before declaring success. "Tests pass" means you ran them.

## Tech Stack

### Backend
- Python 3.12 + Django 5.2 + Django REST Framework
- Celery 5 + Redis (async task queue)
- PostgreSQL 16
- LiteLLM (Gemini 2.5 Pro/Flash, Groq Llama, Anthropic Claude)
- Claude Agent SDK (`claude_agent_sdk`) for autonomous code execution

### Frontend
- React 18 + TypeScript 5 (strict mode)
- Material UI v5
- TanStack Query v5 (server state)
- Framer Motion (animations)
- Vite

### Mobile
- React Native + Expo
- EAS Build (cloud iOS, local Android)
- EAS Update (OTA for JS-only changes)

### Infrastructure
- Docker + Docker Compose
- Nginx (reverse proxy, SSE support)
- GCP Cloud Run

## Project Layout

```
backend/
├── config/          # Django settings, URLs, Celery config
├── accounts/        # User authentication and profiles
├── ai/              # AI service (LiteLLM), prompts, usage tracking
├── gitdata/         # Git provider sync (GitHub, GitLab)
├── integrations/    # External integrations (Jira, Linear, Discord)
├── autodev/         # Proactive auto-development pipeline
├── articles/        # AI-generated tech articles
├── gamification/    # Developer gamification, XP, leaderboard
├── billing/         # Credits, Stripe, subscriptions
├── notifications/   # Real-time notification system
└── shared/          # Shared utilities, managers, base models

frontend/src/
├── pages/           # Route-level page components
├── components/      # Reusable UI components
├── hooks/           # TanStack Query hooks
├── types/           # TypeScript interfaces
├── utils/           # API client, helpers
└── contexts/        # React contexts

specs/               # Feature specs and implementation plans
├── YYYY-MM-DD-<feature>/
│   ├── spec.md
│   ├── plan.md
│   └── tasks.md
```

## Seven Principles (Constitution Check)

Before any implementation, verify:

| # | Principle | Check |
|---|-----------|-------|
| I | Data-Driven Architecture | Data is real and traceable to a source |
| II | Provider Pattern | External integrations use Provider interface |
| III | API-First | All endpoints under `/api/v1/<app>/` |
| IV | Async-First | Long operations use Celery tasks |
| V | Privacy by Design | Sensitive data encrypted, no logging of secrets |
| VI | Docker-Native | Works in existing containers without changes |
| VII | Simplicity | Follows Model→Serializer→Service→View pattern |

## Workflow

```
brainstorming
    ↓ (spec approved)
writing-plans
    ↓ (plan approved)
subagent-driven-development
    → test-driven-development (per task)
    → systematic-debugging (on failures)
    ↓ (all tasks done)
requesting-code-review
    ↓ (review approved)
finishing-a-branch
    ↓ (PR merged)
deploy
```

## Commands Quick Reference

```bash
# Backend tests
cd backend && pytest --tb=short

# Frontend tests
cd frontend && npx jest --no-coverage

# TypeScript check
cd frontend && npx tsc --noEmit

# Linting
cd backend && ruff check .
cd frontend && npm run lint

# Start dev (backend)
cd backend && source venv/bin/activate
watchfiles 'daphne -b 0.0.0.0 -p 8000 config.asgi:application' .

# Start dev (frontend)
cd frontend && npm run dev

# Celery worker
celery -A config worker -l info

# Celery beat (scheduled tasks)
celery -A config beat -l info
```
