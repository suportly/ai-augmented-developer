---
name: requesting-code-review
description: Use before opening a PR. Dispatches a reviewer subagent.
---

# Requesting Code Review

Prepare and execute a structured code review before merging any branch.

**Announce at start:** "Using requesting-code-review skill. Dispatching the reviewer."

## When to Use

- Before opening any Pull Request
- After all tasks in the implementation plan are complete
- After all tests pass

## Review Preparation Checklist

Before dispatching the reviewer:

- [ ] All tests pass
- [ ] No type or lint errors
- [ ] No pending migrations (if the change has any)
- [ ] All planned tasks completed (no unchecked `- [ ]` in plan)
- [ ] Commits are clean and atomic

If `references/stack.md` exists beside this file, read it for stack-specific guidance.

## Impacted subsystems (optional — graph provider)

When a knowledge-graph context provider is configured (the optional
`knowledge-graph` preset, spec 0017), append an **Impacted subsystems** section
to the reviewer prompt: query the provider's `impact` operation for the changed
files and list the subsystems they touch, citing each edge as `path:symbol` with
its confidence label per `rules/graph-facts.md`.

**Graceful degradation.** The provider is optional. When none is configured, or
it is unavailable at runtime, omit the section. Never emit an error because a
provider is absent.

## Dispatching the Reviewer

This is the only review of the branch. Use the `code-reviewer` agent, `description` `review: branch <slug>`. No
side document: the prompt carries the paths and the base ref, and the reviewer
reads the diff itself.

**Never pass session history** — craft a focused prompt:

```
You are a code reviewer for <stack from the project's CLAUDE.md>.

Spec: specs/<feature>/spec.md   Plan: specs/<feature>/plan.md
Base ref: <git merge-base HEAD main>
Read the diff yourself: git diff <base ref>...HEAD

[Impacted subsystems section, when a provider is configured]

Check for: spec compliance, security, the stack's own pitfalls, test coverage
of the spec scenarios and edge cases, unnecessary complexity.

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

Run the gate in `references/review-gate.md` once per review pass (branch-scoped), then go to "Recording the review verdict".

## Self-Review Before Dispatching

Before sending to reviewer, ask yourself:
- Would I be comfortable if the team saw this code right now?
- Is there anything I know is wrong but left in anyway?
- Are there any security concerns I'm aware of?

If yes to any — fix first, then request review.
