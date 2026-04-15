# {{PROJECT_NAME}} — Django + DRF + React preset

> Generated from the `django-drf-react` preset of the AI-Augmented Developer
> framework. Regenerate with `aiadev install --preset django-drf-react` if
> the preset changes.

You are working inside a full-stack project using the Django + DRF + React
stack. Follow the pipeline described below. The framework-level
constitution at `constitution.md` applies unchanged; the preset adds the
articles in `presets/django-drf-react/constitution.md`.

## Pipeline (from framework)

`specify → clarify → plan → tasks → implement`

See the root [CLAUDE.md](../../CLAUDE.md) for the canonical skill table.
This file only carries the stack additions.

## Tech stack

**Backend**

- Python 3.12 + Django 5.2 + Django REST Framework
- Celery 5 + Redis (async task queue)
- PostgreSQL 16
- LiteLLM (Gemini 2.5 Pro/Flash, Groq Llama, Anthropic Claude)
- Claude Agent SDK (`claude_agent_sdk`) for autonomous code execution

**Frontend**

- React 18 + TypeScript 5 (strict mode)
- Material UI v5
- TanStack Query v5 (server state)
- Framer Motion (animations)
- Vite

**Mobile**

- React Native + Expo
- EAS Build (cloud iOS, local Android)
- EAS Update (OTA for JS-only changes)

**Infrastructure**

- Docker + Docker Compose
- Nginx (reverse proxy, SSE support)
- GCP Cloud Run

## Project layout

```text
{{BACKEND_DIR}}/
├── config/          # Django settings, URLs, Celery config
├── accounts/        # User authentication and profiles
├── ai/              # AI service (LiteLLM), prompts, usage tracking
├── <other apps>/    # Project-specific apps
└── shared/          # Shared utilities, managers, base models

{{FRONTEND_DIR}}/src/
├── pages/           # Route-level page components
├── components/      # Reusable UI components
├── hooks/           # TanStack Query hooks
├── types/           # TypeScript interfaces
├── utils/           # API client, helpers
└── contexts/        # React contexts

specs/               # Feature specs and implementation plans
```

## Preset-specific skills

Loaded from `presets/django-drf-react/skills/`:

- `django-patterns` — App / model / serializer / view / URL conventions.
- `ai-integration` — LiteLLM + Claude Agent SDK providers.
- `celery-async` — Task patterns, scheduling, retries, idempotency.
- `autodev-pipeline` — The proactive auto-development pipeline.
- `deploy` — Cloud Run + EAS deployment runbooks.
- `run-tests` — pytest backend + Jest frontend entry point.

## Quick commands

```bash
# Backend tests
cd {{BACKEND_DIR}} && pytest --tb=short

# Frontend tests
cd {{FRONTEND_DIR}} && npx jest --no-coverage

# TypeScript check
cd {{FRONTEND_DIR}} && npx tsc --noEmit

# Linting
cd {{BACKEND_DIR}} && ruff check .
cd {{FRONTEND_DIR}} && npm run lint

# Start dev (backend)
cd {{BACKEND_DIR}} && source venv/bin/activate
watchfiles 'daphne -b 0.0.0.0 -p 8000 config.asgi:application' .

# Start dev (frontend)
cd {{FRONTEND_DIR}} && npm run dev

# Celery worker
celery -A config worker -l info

# Celery beat (scheduled tasks)
celery -A config beat -l info
```

## Waivers carried by this preset

- **Article III (Simplicity)** — when introducing the provider interface for
  a new AI model vendor, the second caller rule is relaxed: the interface
  is required by Article V and Article III must yield to it. Document the
  waiver in the plan's Complexity Tracking.

<!-- aiadev:auto-stack:start -->
## Detected stack

_Run `aiadev sync` to populate this block from the project's
package.json / pyproject.toml / Makefile / docker-compose / workflows._
<!-- aiadev:auto-stack:end -->
