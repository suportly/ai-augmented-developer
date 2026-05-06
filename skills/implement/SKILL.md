---
name: implement
description: Execute an approved plan + tasks list by dispatching one fresh subagent per task and applying two-stage review (spec compliance, then code quality) before moving on.
version: 0.2.0
inputs:
  - type: file
    path: specs/<branch>/plan.md
  - type: file
    path: specs/<branch>/tasks.md
outputs:
  - type: commit
    description: One commit per task, in order, with the task id in the commit message.
requires:
  - constitution
  - test-driven-development
handoffs:
  - requesting-code-review
  - finishing-a-branch
  - systematic-debugging
---

# Implement

Take a `plan.md` + `tasks.md` that have already been specified, clarified and approved, and turn them into code through disciplined subagent execution.

**Announce at start:** "Using the implement skill. One subagent per task with two-stage review."

This skill replaces the previous `speckit` and `subagent-driven-development` skills. It does not generate specs or plans — use `specify` → `clarify` → `plan` → `tasks` first.

## When to use

Run pre-flight first: `aiadev preflight implement --feature <slug>`. Abort on non-zero exit unless `AIADEV_PREFLIGHT=warn` is set.

Invoke when the repository already contains:

- `specs/<branch>/spec.md` with no `[NEEDS CLARIFICATION]` markers,
- `specs/<branch>/plan.md` whose Constitution Check section is fully ticked,
- `specs/<branch>/tasks.md` with at least one task marked ready.

If any of those are missing, stop and invoke the appropriate upstream skill instead.

## The loop

For each task in `tasks.md`, in declared order:

```
read row  →  skip-if-done  →  dispatch implementer  →  spec reviewer  →
code quality reviewer  →  flip status & commit
```

The **orchestrator** (the agent following this skill) — not the implementer subagent — owns every step that reads or mutates `tasks.md`. The subagent's "Files to create or modify" list never includes `tasks.md`.

1. **Read the row.** Apply the parse/validate rules implemented in `aiadev.tasks_status` (the helper module that owns the `**Status:**` line grammar) to `specs/<branch>/tasks.md` at iteration start — the orchestrator may invoke it via `python -c` or replicate the rules inline using `Read`/`Bash` tools. On any malformed status line, value outside `pending|in_progress|blocked|done`, or `done`-prefix violation, halt the loop with a non-zero exit and surface the error verbatim — do not auto-repair. Examples: `ERROR: tasks.md malformed at T003 (line 47): missing or unparseable **Status:** line. Fix manually before resuming.` or `ERROR: tasks.md inconsistency — T003 is done but T002 is pending. Fix tasks.md manually before resuming.`
2. **Skip if already done.** If the current row's `**Status:**` is `done`, advance to the next task with no subagent dispatch — this is the resume guard.
3. **Treat `in_progress` as `pending`.** A row found in `**Status:** in_progress` at iteration start means a previous run crashed mid-iteration before its commit landed; there is nothing on disk worth preserving. Re-dispatch from scratch.
4. **Dispatch implementer** with the prompt below. Hand-craft the context — do not forward full conversation history.
5. **Wait for the return status** (see the taxonomy below) and act on it.
6. **Dispatch spec reviewer** only after the implementer reports `DONE`.
7. **Dispatch code quality reviewer** only after the spec reviewer returns `APPROVED`.
8. **Flip status and commit, atomically.** This is one git commit per task — the marker rides inside it:
   - (a) Rewrite the active row's `**Status:** pending` line to `**Status:** done` — invoke `aiadev.tasks_status.mark_done(tasks_md_path, task_id)` (e.g. via `python -c`) or apply the equivalent `Edit` directly. Only the targeted `### TNNN` block changes; surrounding bytes stay untouched.
   - (b) `git add` the task's code/test files **and** `tasks.md` together.
   - (c) `git commit -m "<task id> <subject>"`.
   - (d) On commit failure (hook rejection, signing error, etc.): roll back the marker before re-raising — `git restore --staged tasks.md && git checkout -- tasks.md` — then surface the underlying hook output to the user. Never use `--no-verify` to bypass.
9. If any step returns `ISSUES` or `BLOCKED`, fix and re-dispatch. The row stays `**Status:** pending` until step 8 lands a green commit; never premature-mark on retry.

After the last task:

- Dispatch a final full-branch review.
- Hand off to `finishing-a-branch` to open the PR.

## Model selection

| Task type | Model |
|---|---|
| Mechanical edits to 1-2 files with an unambiguous spec | Haiku |
| Integration work, judgment calls, new modules | Sonnet |
| Architectural decisions, cross-cutting refactors, final review | Opus |

## Implementer prompt

```markdown
You are implementing Task N of an approved plan.

Task: <task title from tasks.md>

Spec context (relevant excerpt only):
<copy the minimum spec slice that this task depends on>

Plan context:
<the full task entry from plan.md, including acceptance criteria>

Files to create or modify:
<exact file list — no wildcards>

Workflow: test-first. Write a failing test, confirm it fails for the
right reason, implement the minimum code to pass, confirm it passes.

Return exactly one status as the first line of your response:
- DONE — implementation complete, all tests passing
- DONE_WITH_CONCERNS — complete, but with issues worth raising [list]
- NEEDS_CONTEXT — cannot proceed without [list]
- BLOCKED — cannot proceed because [specific cause]
```

Project-specific conventions (stack, patterns, commit style) belong in the active preset's `CLAUDE.md`, not in this prompt — the subagent will read them from the project root.

## Status handling

- **DONE** — advance to spec review.
- **DONE_WITH_CONCERNS** — decide: does the concern block the spec? If yes, fix before review. If no (quality only), pass to the code quality reviewer to judge.
- **NEEDS_CONTEXT** — provide exactly what was asked for and re-dispatch. Never guess.
- **BLOCKED** — find the root cause before retrying. Common causes: an unimplemented upstream task (fix ordering in `tasks.md`), a design conflict (escalate to the user), or an environment issue (invoke `systematic-debugging`).

## Spec reviewer prompt

```markdown
You are reviewing whether an implementation matches its spec.

Spec excerpt: <the relevant acceptance scenarios>
Task: <description>
Diff or files changed: <produce from git>

Verify:
1. Every acceptance scenario in the spec is exercised by at least one test.
2. API shape (endpoints, payloads, status codes) matches the spec.
3. Data model (fields, types, constraints) matches the spec.
4. Error paths described in the spec are handled.

Return exactly one status as the first line:
- APPROVED
- ISSUES_FOUND — followed by a list of specific violations with file:line
```

## Code quality reviewer prompt

```markdown
You are reviewing code quality after spec compliance was already approved.

Diff or files changed: <from git>
Active preset context: <read CLAUDE.md>

Verify:
1. Follows the patterns declared in the active preset.
2. No security issues (injection, IDOR, XSS, secret leakage).
3. No performance traps (N+1, missing indexes, unbounded loops).
4. Error handling is explicit; no silent catches.
5. No gratuitous abstraction; YAGNI respected.
6. Tests cover the happy path and at least one failure mode.

Return exactly one status as the first line:
- APPROVED
- ISSUES — followed by a list with specific fixes suggested
```

## Rules that do not bend

- Never skip either review. Quality comes from the reviews, not from the implementer.
- Never start the code quality review before spec compliance is `APPROVED`.
- Never dispatch implementation subagents in parallel for tasks that touch the same files. Serial is safer and the cost is negligible compared to a botched merge.
- Never forward the full session transcript to a subagent. Craft a focused prompt each time — the subagent should be able to succeed with no other context.
- One task per commit; the commit message references the task id.

## Error handling for the pipeline itself

If the loop fails (a subagent returns garbage, or two review attempts produce contradictory verdicts):

1. Pause the pipeline. Do not try to paper over it by advancing.
2. Write a short incident note in `specs/<branch>/tasks.md` under the affected task.
3. Notify the user with: what failed, what you tried, what you need to proceed.
