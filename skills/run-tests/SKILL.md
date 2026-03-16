---
name: run-tests
description: Run project tests. Use after modifying code to catch regressions before committing.
disable-model-invocation: true
allowed-tools: Bash, Read, Grep
argument-hint: "[backend|frontend|mobile|all] [--file path] [--app appname]"
---

# Run Tests

Run the test suite for the project. Default runs all layers.

## Usage

- `/run-tests` — Run all layers
- `/run-tests backend` — Django backend tests
- `/run-tests frontend` — React frontend tests
- `/run-tests mobile` — React Native (RNTL) mobile tests
- `/run-tests backend --app accounts` — Specific Django app
- `/run-tests backend --file tests/ai/test_service.py` — Specific test file
- `/run-tests frontend --file src/__tests__/Component.test.tsx` — Specific test file

## Commands by Layer

### Backend (pytest)
```bash
cd backend && pytest --tb=short
# Specific app:
cd backend && pytest tests/<app>/ --tb=short
# Specific file:
cd backend && pytest <path> -v
# With coverage:
cd backend && pytest --cov=. --cov-report=term-missing
```

### Frontend (Jest + RTL)
```bash
cd frontend && npx jest --no-coverage
# Specific file:
cd frontend && npx jest --no-coverage <path>
# Watch mode:
cd frontend && npx jest --watch
```

### Mobile (RNTL)
```bash
cd StriveXMobile && npx jest --no-coverage
# Specific file:
cd StriveXMobile && npx jest --no-coverage <path>
```

### Type Check (no test runner needed)
```bash
cd frontend && npx tsc --noEmit
```

### Linting
```bash
# Backend
cd backend && ruff check .
# Frontend
cd frontend && npm run lint
```

## Steps

1. Identify which layer to test based on `$ARGUMENTS` (default: all)
2. Run the tests
3. Analyze output:
   - All passed → report success with count
   - Failures → list failed tests, analyze if pre-existing or new
4. For new failures → invoke `systematic-debugging`

## Output Format

**Success:**
```
✓ Backend: 87 passed in 4.2s
✓ Frontend: 23 passed in 8.1s
✓ TypeScript: no errors
```

**Failure:**
```
✗ Backend: 2 failed, 85 passed
  FAILED tests/autodev/test_pipeline.py::test_spec_generation - AssertionError
  FAILED tests/ai/test_service.py::test_litellm_fallback - ConnectionError

→ Recommend: run systematic-debugging on these failures
```

## Known Pre-Existing Failures

Document any known flaky tests here when discovered:
```
# Add entries as: test_name — reason — since version
```
