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

## Reviewer re-dispatch gate

Story 3 of `specs/0014-bmad-inspired-evolutions/spec.md` adds the
zero-findings-halt rule for the `code-reviewer` agent. The agent-side
contract (the `### Why no issues` block on `APPROVED`) lives in
`agents/code-reviewer.md` under "Output rule for APPROVED on non-trivial
change". The orchestrator-side counterpart — detecting violations and
re-dispatching — lives HERE.

This skill dispatches the reviewer for the full branch (not per task),
so the gate runs once per review pass:

1. **Read the verdict line.** If the first line is `APPROVED`, parse
   the rest of the response.
2. **Detect the `### Why no issues` block.** A valid response has
   either a `### Why no issues` H3 with ≥ 3 bullet items each in the
   shape `<file:line> — <verification>`, OR (in terse-mode, see
   `.claude/rules/terse-mode.md`) ≥ 3 lines starting with the green
   glyph `🟢 file:line — verification`. Anything else is a missing
   block.
3. **Decide whether the branch diff is non-trivial.** Use the canonical
   cl-5 definition against the full branch diff vs `main`:
   `git diff --shortstat --ignore-blank-lines main...HEAD` > 10 LOC
   after dropping `.md`, `.json`, `.lock`, `.toml`, and any path under
   `docs/`. Spec/plan creation under `specs/<branch>/{spec,plan}.md` is
   ALWAYS non-trivial. The helper
   `aiadev.review_log.is_non_trivial_change` implements this exactly;
   `aiadev preflight requesting-code-review` exposes the same check
   from the CLI and is the recommended way to surface it before this
   skill dispatches anything.
4. **Append a review-log entry** to `specs/<branch>/.review-log.jsonl`
   regardless of verdict. Shape:
   `{"timestamp": <ISO-8601 UTC>, "reviewer": "code-reviewer",
   "verdict": "APPROVED"|"CHANGES_REQUESTED",
   "has_why_no_issues_block": <bool>, "task_id": "branch-review"}`.
   Use `aiadev.review_log.append_review_entry`. The `task_id` field is
   set to a stable sentinel (`"branch-review"`) at this layer because
   the dispatch is branch-scoped, not task-scoped.
5. **Re-dispatch when the rule is violated.** If verdict is `APPROVED`,
   the branch is non-trivial, and the `### Why no issues` block is
   missing, dispatch the SAME `code-reviewer` agent again with
   reinforced adversarial framing. The second prompt MUST escalate to
   something like: "You approved without justifying. Assume there is at least one bug
   and either show it OR justify the absence by category (security,
   performance, spec compliance, tests, complexity)." See
   `agents/code-reviewer.md` for the canonical wording.
6. **Hard limit: 2 re-dispatches per reviewer per review pass.** On the
   third dispatch attempt, accept the verdict but append a
   `WARNING: reviewer exhausted re-dispatch budget without justification`
   line to `.review-log.jsonl` and proceed to "Recording the review
   verdict" below. Plan ADR-4 calls this out as the loop-prevention
   guarantee.
7. **Trivial-change exception.** If the branch diff is trivial (≤ 10
   LOC after the cl-5 exclusions), the rule does not apply — accept
   the `APPROVED` verdict silently and do not re-dispatch. Story 3 sc3
   exists to keep noise out of pure-docs branches and similar no-ops.

## Self-Review Before Dispatching

Before sending to reviewer, ask yourself:
- Would I be comfortable if the team saw this code right now?
- Is there anything I know is wrong but left in anyway?
- Are there any security concerns I'm aware of?

If yes to any — fix first, then request review.
