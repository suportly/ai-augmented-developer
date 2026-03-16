---
name: writing-plans
description: Use when you have a spec or requirements for a multi-step task, before touching any code
---

# Writing Plans

## Overview

Write detailed implementation plans assuming the developer has zero codebase context and questionable taste. Document everything: which files to touch for each task, code, tests, how to verify. DRY. YAGNI. TDD. Frequent commits.

**Announce at start:** "Using the writing-plans skill to create the implementation plan."

**Save plans to:** `specs/YYYY-MM-DD-<feature-name>/plan.md`

## Required Plan Header

Every plan MUST start with:

```markdown
# [Feature Name] — Implementation Plan

> **For agentic workers:** REQUIRED: Use `subagent-driven-development` (if subagents available) or execute in current session.

**Branch**: `XXX-<name>` | **Date**: YYYY-MM-DD | **Spec**: [spec.md](spec.md)

## Summary
[One sentence describing what this builds]

## Technical Context
- **Stack**: Python 3.12 / TypeScript 5.x / Django 5.2+ / React 18
- **Primary Dependencies**: [list]
- **Storage**: PostgreSQL 16 ([new tables? which apps affected])
- **Testing**: pytest + factory_boy (backend), Jest/RNTL (frontend/mobile)

## Constitution Check
| Principle | Status | Notes |
|-----------|--------|-------|
| Data-Driven Architecture | PASS/FAIL | ... |
| Provider Pattern | PASS/FAIL | ... |
| API-First | PASS/FAIL | ... |
| Async-First | PASS/FAIL | ... |
| Simplicity | PASS/FAIL | ... |

---
```

## File Structure Mapping

Before defining tasks, map files to be created/modified:

```markdown
## Project Structure

backend/
├── <app>/
│   ├── models.py          # New models
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   ├── tasks.py           # If Celery
│   ├── services/
│   │   └── <service>.py
│   └── migrations/

frontend/src/
├── pages/<Module>/
│   └── <Page>.tsx
├── components/<Module>/
│   └── <Component>.tsx
├── hooks/
│   └── use<Feature>.ts
└── types/
    └── <feature>.ts
```

## Task Granularity (2-5 minutes each)

Each step is one action:
- "Write the failing test" — step
- "Run to confirm it fails" — step
- "Implement minimal code" — step
- "Run to confirm it passes" — step
- "Commit" — step

## Task Structure

````markdown
### Task N: [Component Name]

**Files:**
- Create: `exact/path/to/file.py`
- Modify: `exact/path/to/existing.py`
- Test: `tests/exact/path/to/test_file.py`

- [ ] **Step 1: Write the failing test**

```python
# pytest
def test_specific_behavior(db, user_factory):
    user = user_factory()
    result = my_function(user, input_data)
    assert result.status == 'expected'
    assert result.field == 'expected_value'
```

- [ ] **Step 2: Run to confirm it FAILS**

```bash
cd backend && pytest tests/path/test_file.py::test_specific_behavior -v
```
Expected: FAIL — "function not defined" or ImportError

- [ ] **Step 3: Implement minimal code**

```python
# backend/<app>/services/my_service.py
def my_function(user, data):
    return ExpectedResult(status='expected', field=data['field'])
```

- [ ] **Step 4: Run to confirm it PASSES**

```bash
cd backend && pytest tests/path/test_file.py::test_specific_behavior -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/<app>/services/my_service.py tests/path/test_file.py
git commit -m "feat(<app>): add my_function with test"
```
````

## Patterns by Layer

### Django Backend — Implementation Order
1. Models + migrations
2. Serializers
3. Services (business logic)
4. Views/ViewSets
5. URLs
6. Celery tasks (if async)
7. Admin registration
8. Integration tests

### React Frontend — Implementation Order
1. TypeScript types (`types/<feature>.ts`)
2. TanStack Query hooks (`hooks/use<Feature>.ts`)
3. Base components
4. Main page
5. Route integration (`routes.tsx`)
6. Tests

### Celery Tasks
- Always `bind=True, max_retries=3`
- Log start and end with `logger.info`
- `countdown` for exponential retry
- Idempotent task when possible

## Plan Review Loop

After completing each chunk of the plan (≤1000 lines):

1. Dispatch `plan-document-reviewer` subagent
2. If Issues Found: fix, re-dispatch, repeat
3. If Approved: proceed to next chunk (or execution handoff)

## Execution Handoff

After saving the plan:
> "Plan complete and saved to `specs/<path>/plan.md`. Ready to execute?"

- **With subagents (Claude Code):** Use `subagent-driven-development` — mandatory standard
- **Without subagents:** Execute in current session step by step
