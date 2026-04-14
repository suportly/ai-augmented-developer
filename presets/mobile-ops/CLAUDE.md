# {{PROJECT_NAME}} — mobile-ops preset

> Generated from the `mobile-ops` preset. Adds operational runbooks
> (build, submit, deploy, OTA, release notes) to a stack that combines a
> backend on GCP Cloud Run with an Expo mobile app on EAS.
>
> Regenerate with `aiadev install --preset mobile-ops` after updating
> any variable.

You are working on a project whose operational shape combines:

- **Backend:** HTTP API containerised and deployed to GCP Cloud Run.
- **Mobile:** Expo (React Native) built and distributed via EAS.
- **Admin app:** a second Cloud Run service for the internal admin.
- **OTA:** JS-only updates pushed through EAS Update between full builds.

This preset is additive. It does not redefine how features are specified,
planned, or implemented — pair it with `django-drf-react` (or any other
feature preset) when the backend uses Django + DRF. Only the operational
runbooks change.

## Operational skills loaded

From `presets/mobile-ops/skills/`:

| Skill | Purpose |
|---|---|
| `start-dev` | Bring up backend + frontend + mobile dev servers locally. |
| `run-tests` | Run the project's test suites (backend / frontend / mobile). |
| `bump-version` | Bump `app.json`, `package.json`, and backend version metadata. |
| `build-android` | Trigger an EAS Android build (production profile). |
| `build-ios` | Trigger an EAS iOS build (production profile). |
| `submit-android` | Submit a built Android artifact to Google Play. |
| `submit-ios` | Submit a built iOS artifact to App Store Connect. |
| `deploy-backend` | Push the API image and deploy to Cloud Run. |
| `deploy-admin` | Push the admin image and deploy to Cloud Run. |
| `ota-update` | Publish a JS-only update through EAS Update. |
| `release-notes` | Draft release notes from git log for the next store submission. |

## Project layout

```text
{{BACKEND_DIR}}/        # API backend
{{MOBILE_DIR}}/         # Expo / React Native app
{{ADMIN_DIR}}/          # Admin panel
```

## Backend runtime identifiers

- ASGI module: `{{BACKEND_ASGI_MODULE}}`
- Celery app module: `{{CELERY_APP}}`
- App display name: `{{APP_NAME}}`

## GCP configuration

- Project: `{{GCP_PROJECT}}`
- Region: `{{GCP_REGION}}`
- Artifact Registry repository: `{{ARTIFACT_REPO}}`
- Backend service: `{{BACKEND_SERVICE}}`
- Admin service: `{{ADMIN_SERVICE}}`
- Cloud SQL instance: `{{CLOUD_SQL_INSTANCE}}`
- Production API URL: `{{PROD_API_URL}}`
- Production admin URL: `{{PROD_ADMIN_URL}}`

## Pipeline reminder

`specify → clarify → plan → tasks → implement → (build/submit/deploy/ota skills)`

The skills above are **not** part of the feature pipeline — they are the
release-time runbooks. A feature that spans backend, frontend, and mobile
changes usually invokes several of them from within a single `tasks.md`.

## Upgrade path

When variables change (GCP project rotation, new region, new mobile app
identifier), regenerate this file with `aiadev install --preset
mobile-ops --interactive` instead of editing by hand — the skills under
`skills/` are generated from the same variables and will drift if only
one file is patched.
