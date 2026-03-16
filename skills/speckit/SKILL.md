---
name: speckit
description: Full automatic development flow: specify → plan → tasks → implement → PR. Use for features with the SpecKit pipeline or autodev integration.
---

# SpecKit — Automatic Development Flow

Transforms a demand (issue, spec, user story) into code + Pull Request following the Activi.dev structured pipeline.

## Pipeline Overview

```
Demand (issue/spec)
    ↓
[specify] Generate complete spec.md
    ↓
[plan]    Generate plan.md with bite-sized tasks
    ↓
[tasks]   Execute tasks with subagents (TDD)
    ↓
[review]  Automated code review
    ↓
[pr]      Create Pull Request linked to demand
```

**Announce at start:** "Using the speckit skill. Pipeline: specify → plan → tasks → implement → PR."

## Phase 1: Specify

From the demand (free text, issue, or draft spec):

1. **Read the demand** and identify:
   - Type: feature, bugfix, refactor, performance
   - Complexity: S (< 1h), M (1-4h), L (> 4h, consider decomposition)
   - Affected Django app / React component / both

2. **Generate spec.md** at `specs/YYYY-MM-DD-<slug>/spec.md`:
   ```markdown
   # Feature Specification: <Name>
   **Branch**: `NNN-<slug>`
   **Created**: YYYY-MM-DD
   **Status**: Draft

   ## Summary
   [2-3 sentences]

   ## User Stories & Tests
   ### Story 1 - <Title> (P1)
   As a <role>, I want <action> so that <benefit>.
   **Acceptance Scenarios**: Given/When/Then (minimum 3 scenarios)

   ## Technical Decisions
   - Stack: [affected layers]
   - New models: [yes/no, which]
   - Celery tasks: [yes/no, why]
   - Breaking changes: [yes/no]

   ## Traceability
   - Issue: #<number> / <URL>
   - Branch: `NNN-<slug>`
   ```

3. **Run spec-document-reviewer** subagent — fix until approved
4. **Wait for user approval** before proceeding

## Phase 2: Plan

Invoke `writing-plans` with the generated spec. The plan must include:
- Constitution Check of the 7 principles
- Exact file mapping
- Bite-sized tasks with TDD (RED → GREEN → REFACTOR → COMMIT)
- Token usage estimate per AI step (if applicable)

## Phase 3: Tasks (Implementation)

Invoke `subagent-driven-development` to execute the plan:
- Fresh subagent per task
- Spec compliance review after each task
- Code quality review after spec compliance
- Never skip reviews

### SpecKit Implementation Rules

**Django Backend:**
```python
# Follow pattern: Model → Serializer → Service → View → URL → Task → Admin
# Use EncryptedTextField for sensitive data (credentials, tokens)
# Always UserManager on models with user FK
# Provider Pattern for external integrations
```

**Celery Tasks:**
```python
@app.task(bind=True, max_retries=3, default_retry_delay=60)
def my_task(self, demand_id: str) -> None:
    logger.info(f"[speckit] starting task demand_id={demand_id}")
    try:
        # logic here
        logger.info(f"[speckit] task completed demand_id={demand_id}")
    except Exception as exc:
        logger.error(f"[speckit] task failed demand_id={demand_id}: {exc}")
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
```

**React Frontend:**
```typescript
// Follow pattern: types → hooks (TanStack Query) → components → page → route
// Always TypeScript strict
// MUI v5 for UI components
// TanStack Query for server state (no useState for server data)
```

## Phase 4: PR

After implementation and code review approved:

1. **Create branch** named `NNN-<slug>`
2. **Push** the branch
3. **Open PR** with:
   ```markdown
   ## Summary
   - [bullet points of main changes]

   ## Traceability
   - Closes #<issue_number>
   - Spec: `specs/YYYY-MM-DD-<slug>/spec.md`
   - Plan: `specs/YYYY-MM-DD-<slug>/plan.md`

   ## Test Plan
   - [ ] pytest backend (all passing)
   - [ ] Frontend compiles without TypeScript errors
   - [ ] Migrations applied without conflicts
   - [ ] Celery tasks manually tested (if applicable)
   ```
4. **Link to original issue** in PR description

## Constitution Check (7 Principles)

Before any implementation, verify:

| Principle | Check |
|-----------|-------|
| I. Data-Driven Architecture | Data is real and traceable? |
| II. Provider Pattern | External integrations use Provider Pattern? |
| III. API-First | All endpoints under `/api/v1/<app>/`? |
| IV. Async-First | Slow operations go to Celery? |
| V. Privacy by Design | Sensitive data in EncryptedTextField? |
| VI. Docker-Native | Works in existing containers? |
| VII. Simplicity | Follows Model→Serializer→View→Task pattern? |

## Pipeline Error Handling

If any phase fails:
1. **Log** the error with full context
2. **Notify** the user with specific questions to unblock
3. **Pause** the pipeline — never continue with unresolved errors
4. **Never retry** the same approach more than 3 times without changing strategy
