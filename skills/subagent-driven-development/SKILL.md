---
name: subagent-driven-development
description: Use to execute implementation plans with independent subagents and two-stage review per task.
---

# Subagent-Driven Development

Execute plans by dispatching a fresh subagent per task, with two-stage review after each: spec compliance first, then code quality.

**Core principle:** Fresh subagent per task + two-stage review (spec → quality) = high quality, fast iteration.

**Announce at start:** "Using subagent-driven-development. Fresh subagent per task with dual review."

## The Process

### Setup
1. Read the full plan and extract all tasks
2. Create a TodoWrite with all tasks for tracking
3. Verify an approved spec exists before starting

### Per Task

```
Dispatch implementer → spec reviewer → code quality reviewer → mark complete
```

1. **Dispatch implementer** with precise context (see "Implementer Prompt")
2. **Wait for result** — analyze the returned status
3. **Dispatch spec reviewer** (only after DONE)
4. **If spec compliance approved:** dispatch code quality reviewer
5. **If code quality approved:** mark task complete, advance
6. **If any review fails:** fix and re-dispatch — never advance with unresolved issues

### After All Tasks
- Dispatch final code review
- Use `finishing-a-branch` to complete the branch

## Model Selection by Task

| Task Type | Model |
|-----------|-------|
| Mechanical (1-2 files, clear spec) | haiku (cheaper) |
| Integration/judgment calls | sonnet (standard) |
| Architecture/design/review | opus (most capable) |

## Implementer Statuses

### DONE
Implementation complete. Proceed to spec compliance review.

### DONE_WITH_CONCERNS
Read the concerns, assess:
- Blocking for spec? → Fix before proceeding
- Quality improvements? → Let code quality reviewer assess

### NEEDS_CONTEXT
Provide the specific requested context and re-dispatch. Common contexts:
```
"Need the content of file X" → Read and include in prompt
"Don't know how endpoint Y works" → Include API contract
"What pattern to use for Z?" → Include a codebase example
```

### BLOCKED
Assess root cause before retrying:
- Unimplemented dependency → Implement the dependency first
- Design conflict → Escalate to user
- Environment bug → Use `systematic-debugging`

## Implementer Prompt

```markdown
You are an engineer implementing Task N of the plan.

**Task:** <task title>

**Spec context:**
<relevant spec section>

**Plan context:**
<full task with steps and code>

**Files to create/modify:**
<exact file list>

**Project conventions:**
- Backend: Django 5.2 + DRF, pytest + factory_boy, pattern Model→Serializer→Service→View
- Frontend: React 18 + TypeScript strict, TanStack Query, MUI v5
- Celery: bind=True, max_retries=3, transaction.on_commit() to dispatch tasks
- Commits: feat(<app>): description / fix(<app>): description / test(<app>): description

**TDD mandatory:**
1. Write a failing test
2. Confirm it fails for the right reason
3. Implement minimal code
4. Confirm it passes
5. Commit

**Return one of:**
- DONE: implementation complete, all tests passing
- DONE_WITH_CONCERNS: complete but with specific concerns [list them]
- NEEDS_CONTEXT: needs specific context [list what's needed]
- BLOCKED: blocked by [specific cause]
```

## Spec Reviewer Prompt

```markdown
You are a reviewer verifying the implementation matches the spec.

**Spec:** <relevant spec content>
**Task implemented:** <description>
**Implemented code:** <diff or modified files>

Verify:
1. All spec acceptance scenarios are addressed?
2. API interfaces are correct (endpoints, payloads, status codes)?
3. Models/fields match the spec?
4. Error handling behavior is correct?
5. Tests cover the spec scenarios?

Return: APPROVED or ISSUES_FOUND with specific list of violations.
```

## Code Quality Reviewer Prompt

```markdown
You are a code quality reviewer.

**Implemented code:** <diff or files>
**Project context:** Django 5.2 + React 18 + TypeScript strict

Verify:
1. Follows project patterns (Model→Serializer→Service→View)?
2. No security vulnerabilities (SQL injection, XSS, IDOR)?
3. No N+1 queries (use select_related/prefetch_related)?
4. Adequate error handling (no silent exceptions)?
5. No unnecessary TypeScript `any`?
6. No duplicated code (DRY)?
7. Celery tasks are idempotent (if applicable)?

Return: APPROVED or ISSUES with specific list and suggested fix.
```

## Critical Rules

- **Never skip reviews** — quality comes from reviews, not just implementation
- **Never start code quality before spec compliance passes**
- **Never proceed with unresolved issues**
- **Never dispatch implementation subagents in parallel** — serial order mandatory
- **Precise context** — never pass session history to subagents; craft focused prompts
