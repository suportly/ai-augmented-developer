---
name: deploy
description: Deploy backend (Cloud Run), frontend (static/Cloud Run), or mobile (EAS). Use when publishing changes to production.
disable-model-invocation: true
allowed-tools: Bash, Read, Grep
argument-hint: "[backend|frontend|mobile-android|mobile-ios|ota] [--skip-checks]"
---

# Deploy

Deploy the application to production. Runs pre-flight checks unless `--skip-checks` is passed.

## Usage

- `/deploy backend` — Deploy Django backend to GCP Cloud Run
- `/deploy frontend` — Deploy React frontend (build + deploy)
- `/deploy mobile-android` — Build + submit Android AAB to Google Play
- `/deploy mobile-ios` — Build iOS on EAS cloud + submit to TestFlight
- `/deploy ota` — Publish OTA JS update to production channel (mobile, JS-only changes)

---

## Backend — GCP Cloud Run

### Pre-flight Checks
```bash
cd backend && git status  # Must be clean (no uncommitted changes)
python manage.py showmigrations | grep "\[ \]"  # Must be empty
python manage.py migrate --check  # Must pass
```

### Build & Push Docker Image
```bash
IMAGE="<region>-docker.pkg.dev/<project>/<repo>/backend:latest"
docker build -t $IMAGE backend/
docker push $IMAGE
```

### Deploy
```bash
gcloud run deploy backend \
  --image $IMAGE \
  --region <region> \
  --platform managed
```

### Post-Deploy
```bash
# Run migrations on Cloud SQL
gcloud run jobs execute migrate-job --region <region>

# Verify health
curl https://<backend-url>/api/health/
```

**Note:** `gcloud auth` requires interactive browser login. Flag this early if not already authenticated.

---

## Frontend — React (Vite)

### Build
```bash
cd frontend && npm run build
# Verify no TypeScript errors in build output
```

### Deploy (Docker/Cloud Run or static hosting)
```bash
IMAGE="<region>-docker.pkg.dev/<project>/<repo>/frontend:latest"
docker build -t $IMAGE frontend/
docker push $IMAGE
gcloud run deploy frontend --image $IMAGE --region <region>
```

---

## Mobile Android — EAS Build + Google Play

### Pre-flight
```bash
cd <mobile-dir>
# Verify versions are synced
cat app.json | grep -A3 '"android"'
cat android/app/build.gradle | grep versionCode
```

### Bump Version (unless --skip-checks)
```bash
# Uses bump-version skill if available
# Or manually update app.json + android/app/build.gradle
```

### Build AAB
```bash
cd <mobile-dir> && eas build --platform android --profile production --local
# Timeout: ~10 minutes. Run in background.
```

### Submit to Google Play
```bash
eas submit --platform android --latest
```

---

## Mobile iOS — EAS Cloud Build + TestFlight

### Build (cloud, no Mac required)
```bash
cd <mobile-dir> && eas build --platform ios --profile production --non-interactive
# Runs ~15-20 min in EAS cloud. Monitor:
eas build:list --platform ios --limit 1
```

### Submit to TestFlight
```bash
eas submit --platform ios --latest --non-interactive
```

---

## Mobile OTA Update — EAS Update (JS-only)

### When to Use
Only for TypeScript/JavaScript changes. Native changes (new packages, AndroidManifest, Info.plist) require full build.

### Publish
```bash
cd <mobile-dir> && eas update --branch production --message "<description of changes>"
# Verify:
eas update:list --branch production --limit 1
```

---

## Celery Workers (after backend deploy)

Workers must be restarted after deploying new task code:
```bash
docker compose restart celery
# Or in production, trigger worker restart in your orchestration system
```

---

## Rollback

### Backend
```bash
# Revert to previous Cloud Run revision
gcloud run revisions list --service backend --region <region>
gcloud run services update-traffic backend --to-revisions=<previous-revision>=100
```

### Mobile
- OTA: Deploy previous update bundle
- Full build: Submit previous AAB/IPA manually
