# Constitution: Django + DRF + React preset

> Inherits from the framework-level `constitution.md` at the repo root.
> The articles below **extend** or **tighten** the defaults. They do not
> remove or weaken inherited articles.

**Version:** 1.0.0
**Adopted:** 2026-04-14

---

## Inherited articles (unchanged)

- Article I — Spec-first
- Article II — Test-first
- Article III — Simplicity
- Article IV — Evidence over claims
- Article V — Provider pattern
- Article VI — Privacy by design
- Article VII — Attribution

## Preset-specific articles

### Article DJR-1 — API-First

**Statement.** Every server-rendered resource a client consumes lives under `/api/v1/<app>/`. The frontend reads server state exclusively through TanStack Query hooks wrapping those endpoints.

**Rationale.** An explicit, versioned HTTP surface is the cheapest insurance against silent coupling between backend and frontend. Mobile clients cannot be upgraded atomically; a stable contract is what keeps old installs alive.

**Test.**

- [ ] New endpoints declared under `/api/v1/<app>/`, never ad-hoc paths.
- [ ] Frontend calls go through a TanStack Query hook, not raw `fetch`.
- [ ] Breaking changes either version (`/api/v2/<app>/`) or ship a deprecation window declared in the plan.

**Waivable?** No.

### Article DJR-2 — Async-First

**Statement.** Any operation whose synchronous budget exceeds 2 seconds moves to a Celery task. Request handlers return fast; the client polls or opens an SSE stream for updates.

**Rationale.** A blocked request handler cascades: saturated workers, slow page loads, frustrated users. The two-second ceiling is the observed boundary between "felt fast" and "felt broken" in this stack.

**Test.**

- [ ] New endpoints with external I/O budgeted under 2s, measured with `@override_settings(CELERY_TASK_ALWAYS_EAGER=False)`.
- [ ] Long-running ops produce a task id the client polls.
- [ ] Each new Celery task is `bind=True`, `max_retries=3`, logs start and end, and is idempotent.

**Waivable?** Yes, for synchronous admin commands that never touch the request cycle.

### Article DJR-3 — Docker-native

**Statement.** Every development and deployment workflow runs inside the existing Docker Compose topology or Cloud Run environment. "Works on my machine with local Postgres" is not a delivered feature.

**Rationale.** Divergence between local and production is where most late-stage bugs come from. The rule keeps the gap small.

**Test.**

- [ ] `docker compose up` produces a working local environment on a fresh clone.
- [ ] New services added to `docker-compose.yml` and to the Cloud Run deployment manifest.
- [ ] No new dependency installed globally on the host during `README` setup.

**Waivable?** Yes, for native tooling that cannot run inside containers (mobile EAS builds, hardware debugging). Document in the plan.

### Article DJR-4 — Model → Serializer → Service → View

**Statement.** New functionality follows the layer order: Model (schema + managers) → Serializer (validation + shape) → Service (business logic) → View/ViewSet (HTTP concerns) → URL. Business logic does not live in views.

**Rationale.** Fat-model-thin-view is not dogma; it is reuse. Services can be called from Celery tasks, management commands, and tests without spinning up a request.

**Test.**

- [ ] New business logic sits in `<app>/services/`.
- [ ] Views delegate to services; they do not implement the logic.
- [ ] Tests import the service, not the view, whenever possible.

**Waivable?** No for anything with more than three lines of business logic.

### Article DJR-5 — Encrypted fields for credentials

**Statement.** Any model field that stores credentials, OAuth tokens, API keys, or user-provided secrets uses the project's `EncryptedTextField` (or equivalent). Plain `models.TextField` for secrets is rejected at review.

**Rationale.** Article VI (Privacy by design) at the framework level is satisfied at the application level by making the encrypted field type the default for anything sensitive.

**Test.**

- [ ] `git grep 'models.TextField' new code` returns no sensitive fields.
- [ ] `EncryptedTextField` imports present where new credential storage appears.

**Waivable?** No.

## Tightened framework articles

### Tightening of Article II (Test-first)

In addition to the root rule, this preset requires an **integration test** for:

- Every new HTTP endpoint (`pytest` + DRF `APIClient`).
- Every new Celery task (run in eager mode with a real database).

Unit tests alone are not sufficient for these classes of change.

## Amendment process

Follow the root `constitution.md` amendment process. Preset amendments require at least one reviewer familiar with this stack.
