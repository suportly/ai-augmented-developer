---
name: requesting-code-review
description: Use before opening a PR. Dispatches a reviewer subagent.
---

# Requesting Code Review

Review the branch once all tasks are complete and tests pass, before opening any PR.

**Announce at start:** "Using requesting-code-review skill. Dispatching the reviewer."

## Review Preparation Checklist

Before dispatching the reviewer:

- [ ] Tests pass; no type or lint errors; no pending migrations
- [ ] All planned tasks completed (no unchecked `- [ ]`)
- [ ] Commits are clean and atomic

If `references/stack.md` exists beside this file, read it for stack-specific guidance.

## Impacted subsystems (optional — graph provider)

When a knowledge-graph provider is configured (spec 0017), append an **Impacted subsystems** section
to the reviewer prompt: query its `impact` operation for the changed files and list the subsystems
they touch, citing each edge as `path:symbol` with its confidence label per `rules/graph-facts.md`.
**Graceful degradation:** provider absent or unavailable → omit the section, never an error.

## Dispatching the Reviewer

This is the only review of the branch. Use the `code-reviewer` agent, `description` `review: branch <slug>`. No
side document: the prompt carries paths and base ref; the reviewer reads the diff.

**Never pass session history**; send a focused prompt:

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

Write `.aiadev/review.yaml` at the repo root with the verdict, for `finishing-a-branch`. Schema:

```yaml
status: approved          # or: changes_requested
timestamp: 2026-04-21T12:34:56Z   # ISO-8601 UTC
reason: <one line>        # required only when status: changes_requested
```

`aiadev preflight finishing-a-branch` aborts unless `status: approved`.

## Handling Review Feedback

### APPROVED
Write `.aiadev/review.yaml` with `status: approved` and a UTC `timestamp:`, then `finishing-a-branch`.

### CHANGES_REQUESTED
Write `.aiadev/review.yaml` with `status: changes_requested`, a `timestamp:`, and a one-line `reason:`. For each issue:
1. Fix it, add or update tests, re-run the full suite
2. Re-dispatch the reviewer for changed files only (no re-review of unchanged files)

### Escalate to User When
Reviewer and implementer disagree on architecture, the fix needs a significant design change, or the loop exceeds 5 iterations.

## Reviewer re-dispatch gate

Run the gate in `references/review-gate.md` once per review pass (branch-scoped), then go to "Recording the review verdict".


