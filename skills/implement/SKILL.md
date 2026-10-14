---
name: implement
description: Execute an approved plan and tasks list with one fresh subagent and one reviewer per task (conformance first, then quality).
metadata:
  aiadev:
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
    - analyze
    - requesting-code-review
    - finishing-a-branch
    - systematic-debugging
---

# Implement

Turn an approved `plan.md` + `tasks.md` into code: one fresh subagent and one reviewer per task. Specs and plans come from the upstream skills.

## When to use

Needs a clean `spec.md`, a `plan.md` with a ticked Constitution Check and a `tasks.md` with a ready task; else invoke the upstream skill. Pre-flight non-zero exit aborts unless `AIADEV_PREFLIGHT=warn`.

## The loop

For each task in declared order: read row → skip-if-done → dispatch implementer → single reviewer → `aiadev tasks done`.

The **orchestrator** (you), not the implementer, owns every step that reads or mutates `tasks.md`; the subagent's file list never includes it. No parallel implementers on tasks touching the same files.

0. **First call**, in parallel: `aiadev preflight implement --feature <slug> --format json` and `Read` of `tasks.md`, `plan.md`, `spec.md`. Paths come from JSON `docs`, test command from `test_command`. `ok: false` aborts.
1. **Read the row** with the rules of `aiadev.tasks_status` (owner of the `**Status:**` grammar). Malformed status, a value outside `pending|in_progress|blocked|done`, or a `done`-prefix violation: halt non-zero, surface the error verbatim, no auto-repair.
2. **Skip if `done`** (resume guard). `in_progress` counts as `pending` (crashed run): re-dispatch.
3. **Task context.** When `task_context: true` in `preset.yaml` or `--task-context`, read `references/task-context.md` and follow it; otherwise skip this step.
4. **Dispatch implementer** with the prompt below, `description` `implement: <TID> <title>` (reviewer: `review: <TID> <title>`). Hand-craft the context; no conversation history.
5. **Act on the return status** (below).
6. **Prose tier: no reviewer.** If every file of the task is prose markdown under `docs/` or root docs (README, CHANGELOG, CONTRIBUTING), run `npx markdownlint-cli2 <files>` (plus `python3 scripts/validate_skills.py` if it exists), record the result in the commit message and do not dispatch a reviewer. Not prose: `docs/instruction-budget.json`, `docs/pipeline-path.yaml`, anything under `skills/`, `agents/`, `rules/`, `templates/`, `commands/`, `src/`, `tests/`.
   Otherwise dispatch the single reviewer only after `DONE` (prompt below).
7. **Close the task, atomically**, one commit with code, tests and the status flip:
   `aiadev tasks done <TID> --feature <slug> --commit "<TID> <subject>" FILES...`
   It flips `pending` → `done`, stages FILES plus `tasks.md`, commits, and on failure (hook rejection, signing error) rolls the marker back and unstages; refuses if those paths are already staged. Never `--no-verify`.
   Fallback: `aiadev.tasks_status.mark_done`, `git add` files and `tasks.md` together, commit; on commit failure `git restore --staged tasks.md && git checkout -- tasks.md`.
8. `ISSUES` or `BLOCKED`: fix and re-dispatch; the row stays `pending` until step 7 lands a green commit.

After the last task, hand off to `analyze` and then `requesting-code-review` (owns the branch review).

## Implementer prompt

```markdown
You are implementing Task N of an approved plan.

Task: <task title from tasks.md>

Spec context (relevant excerpt only):
<minimum spec slice this task depends on>

Plan context:
<the full task entry from plan.md, including acceptance criteria>

Files to create or modify:
<exact file list, no wildcards>

Workflow: test-first. Write a failing test, confirm it fails for the
right reason, implement the minimum code to pass, confirm it passes.
Run only the tests that exercise the changed code.

Return exactly one status as the first line of your response:
- DONE — complete, task-scoped tests passing
- DONE_WITH_CONCERNS — complete, with concerns [list]
- NEEDS_CONTEXT — cannot proceed without [list]
- BLOCKED — cannot proceed because [specific cause]
```

## Status handling

- **DONE** — advance to review.
- **DONE_WITH_CONCERNS** — blocks the spec? fix before review; else pass to the reviewer.
- **NEEDS_CONTEXT** — provide exactly what was asked; never guess.
- **BLOCKED** — find the root cause first (task order, design conflict: escalate, environment: `systematic-debugging`).

## Reviewer prompt

Dispatch `code-reviewer`:

```markdown
You are the single reviewer for one task. Two passes, in order.

Inputs, embedded (excerpts only, no whole files): acceptance scenarios,
the diff, the test output, preset `CLAUDE.md` rules.

Pass 1 — conformance. Each acceptance scenario is exercised by a test;
API shape, data model and error paths match the spec; nothing beyond the
task's scope was added.
If pass 1 has findings: STOP. Return CHANGES_REQUESTED with only those
findings and skip quality.

Pass 2 — quality. Preset patterns; security; performance traps; error
handling; no gratuitous abstraction; tests cover happy path and a failure.

First line: APPROVED or CHANGES_REQUESTED, then file:line fixes.
```

Correction loop: after 5 fix → re-review iterations on one task, stop and escalate to the user. One task per commit, message carries the task id.

## Reviewer re-dispatch gate

After the reviewer of step 6 answers, run the gate in `skills/requesting-code-review/references/review-gate.md` (APPROVED without the `### Why no issues` block, trivial exception, re-dispatch limit, review-log entry with the task id).

If the loop itself fails: pause, note the incident in `tasks.md` under the task, tell the user what failed and what you need.
