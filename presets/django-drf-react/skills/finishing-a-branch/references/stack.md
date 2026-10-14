# Stack commands (django-drf-react)

## Pre-flight checks

- All tests pass
  ```bash
  cd backend && pytest --tb=short
  cd frontend && npx jest --no-coverage
  ```
- No TypeScript errors
  ```bash
  cd frontend && npx tsc --noEmit
  ```
- No linting errors
  ```bash
  cd backend && ruff check .
  cd frontend && npm run lint
  ```
- Migrations are clean (no unapplied, no conflicts)
  ```bash
  cd backend && python manage.py showmigrations | grep "\[ \]"
  python manage.py migrate --check
  ```

## PR test plan

- [ ] `pytest` — all backend tests pass
- [ ] `npx jest` — all frontend tests pass
- [ ] `npx tsc --noEmit` — no TypeScript errors
- [ ] Migrations applied without conflicts

## After merge

Apply any pending migrations in production (coordinate with deploy process).

## Deployment After Merge

| Changed | Action |
|---------|--------|
| Backend Python | `deploy` skill → Cloud Run |
| Database migrations | Run migrations before deploy |
| Frontend React | `deploy` skill → build + deploy |
| Mobile JS-only | `ota-update` skill |
| Mobile native changes | `build-android` / `build-ios` skills |
| Celery tasks | Restart workers after deploy |
