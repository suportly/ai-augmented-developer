---
name: requesting-code-review
description: Use before opening a PR. Prepares context for code review and dispatches a reviewer subagent.
---

# Requesting Code Review

Prepare and execute a structured code review before merging any branch.

**Announce at start:** "Using requesting-code-review skill. Preparing review context."

## When to Use

- Before opening any Pull Request
- After all tasks in the implementation plan are complete
- After all tests pass

## Review Preparation Checklist

Before dispatching the reviewer:

- [ ] All tests pass: `pytest` (backend) + `npx jest` (frontend/mobile)
- [ ] No TypeScript errors: `npx tsc --noEmit`
- [ ] No linting errors: `ruff check .` (backend) / `npm run lint` (frontend)
- [ ] No pending migrations: `python manage.py showmigrations | grep "\[ \]"`
- [ ] All planned tasks completed (no unchecked `- [ ]` in plan)
- [ ] Commits are clean and atomic

## Review Context Document

Create `specs/YYYY-MM-DD-<feature>/review-context.md`:

```markdown
# Code Review Context: <Feature Name>

## What Was Built
[2-3 sentences describing the feature]

## Spec Reference
- Spec: `specs/YYYY-MM-DD-<feature>/spec.md`
- Plan: `specs/YYYY-MM-DD-<feature>/plan.md`

## Changed Files
<git diff --stat output>

## Key Decisions Made
- [Decision 1 and why]
- [Decision 2 and why]

## Areas Needing Attention
- [Any complexity, trade-offs, or areas where reviewer should look carefully]

## Test Coverage
- Backend: [pytest output summary]
- Frontend: [jest output summary]
- Manual verification: [what was manually tested]
```

## Dispatching the Reviewer

Use the `code-reviewer` agent with the review context document.

**Never pass session history** — always craft a focused review prompt:

```
You are a code reviewer for a Django 5.2 + React 18 + TypeScript project.

Review the changes described in: <path to review-context.md>

Full diff:
<git diff output>

Check for:
1. Spec compliance — do changes fulfill the spec's acceptance criteria?
2. Security — SQL injection, IDOR, XSS, unencrypted sensitive data?
3. Django patterns — N+1 queries, missing select_related, transaction safety?
4. TypeScript — any types, missing null checks, proper error handling?
5. Celery tasks — idempotency, retry logic, transaction.on_commit usage?
6. Tests — adequate coverage of the spec scenarios? Edge cases?
7. Complexity — unnecessary abstractions, YAGNI violations?

Return: APPROVED or CHANGES_REQUESTED with specific issues and suggested fixes.
```

## Recording the review verdict

Once the reviewer returns a verdict, write `.aiadev/review.yaml` at the repo root so `finishing-a-branch` can verify approval. Schema:

```yaml
status: approved          # or: changes_requested
timestamp: 2026-04-21T12:34:56Z   # ISO-8601 UTC
reason: <one line>        # required only when status: changes_requested
```

`aiadev preflight finishing-a-branch` reads this file and aborts unless `status: approved`.

## Handling Review Feedback

### APPROVED
Write `.aiadev/review.yaml` with `status: approved` and a UTC `timestamp:`. Then proceed to `finishing-a-branch`.

### CHANGES_REQUESTED
Write `.aiadev/review.yaml` with `status: changes_requested`, a `timestamp:`, and a one-line `reason:`. For each issue:
1. Fix the specific issue
2. Add or update tests if needed
3. Re-run the full test suite
4. Re-dispatch the reviewer for changed files only

**Do not re-review unchanged files** — focus the re-review on what changed.

### Escalate to User When
- Reviewer and implementer disagree on architecture
- Fix would require significant design change
- Review loop exceeds 5 iterations

## Self-Review Before Dispatching

Before sending to reviewer, ask yourself:
- Would I be comfortable if the team saw this code right now?
- Is there anything I know is wrong but left in anyway?
- Are there any security concerns I'm aware of?

If yes to any — fix first, then request review.
