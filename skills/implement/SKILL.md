---
name: implement
description: Execute an approved plan + tasks list by dispatching one fresh subagent per task and applying a single reviewer per task (spec compliance first, then code quality) before moving on.
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

Take a `plan.md` + `tasks.md` that have already been specified, clarified and approved, and turn them into code through disciplined subagent execution.

**Announce at start:** "Using the implement skill. One subagent per task, one reviewer per task."

This skill replaces the previous `speckit` and `subagent-driven-development` skills. It does not generate specs or plans — use `specify` → `clarify` → `plan` → `tasks` first.

## When to use

Pre-flight is the first call of the loop (below). Abort on non-zero exit unless `AIADEV_PREFLIGHT=warn` is set.

Invoke when the repository already contains:

- `specs/<branch>/spec.md` with no `[NEEDS CLARIFICATION]` markers,
- `specs/<branch>/plan.md` whose Constitution Check section is fully ticked,
- `specs/<branch>/tasks.md` with at least one task marked ready.

If any of those are missing, stop and invoke the appropriate upstream skill instead.

## The loop

For each task in `tasks.md`, in declared order:

```
read row  →  skip-if-done  →  dispatch implementer  →  single reviewer  →
aiadev tasks done
```

The **orchestrator** (the agent following this skill) — not the implementer subagent — owns every step that reads or mutates `tasks.md`. The subagent's "Files to create or modify" list never includes `tasks.md`.

0. **First call.** Issue in parallel, in one message: `aiadev preflight implement --feature <slug> --format json` and `Read` of `tasks.md`, `plan.md`, `spec.md`. Take the doc paths from the JSON `docs` and the test command from `test_command`; do not rediscover them. `ok: false` aborts (see above).
1. **Read the row.** Apply the parse/validate rules of `aiadev.tasks_status` (owner of the `**Status:**` grammar) to `tasks.md`. On any malformed status line, value outside `pending|in_progress|blocked|done`, or `done`-prefix violation, halt with a non-zero exit and surface the error verbatim — do not auto-repair. Example: `ERROR: tasks.md inconsistency — T003 is done but T002 is pending. Fix tasks.md manually before resuming.`
2. **Skip if already done.** A row with `**Status:** done` advances with no dispatch — the resume guard.
3. **Treat `in_progress` as `pending`.** It means a previous run crashed before its commit landed; re-dispatch from scratch.
4. **Dispatch implementer** with the prompt below. Hand-craft the context — do not forward conversation history.
5. **Wait for the return status** (taxonomy below) and act on it.
6. **Dispatch the single reviewer** only after the implementer reports `DONE`. It receives the diff and the test output and checks spec conformance first, code quality second (prompt below).
7. **Close the task, atomically** — one commit carries code, tests and the status flip:
   `aiadev tasks done <TID> --feature <slug> --commit "<TID> <subject>" FILES...`
   It flips `pending` → `done`, stages FILES plus `tasks.md`, commits, and on failure (hook rejection, signing error) rolls the marker back and unstages. It refuses if those paths are already staged. Surface the hook output; never use `--no-verify`.
   Fallback if the command is unavailable: rewrite the row with `aiadev.tasks_status.mark_done`, `git add` the files and `tasks.md` together, commit, and on commit failure run `git restore --staged tasks.md && git checkout -- tasks.md`.
8. If any step returns `ISSUES` or `BLOCKED`, fix and re-dispatch. The row stays `pending` until step 7 lands a green commit.

After the last task, hand off to `analyze` (drift check) and then `requesting-code-review`, which owns the branch-level review. `implement` does not review the whole branch.

## Task-context integration (opt-in)

Story 1 of `specs/0014-bmad-inspired-evolutions/spec.md` adds the
`task-context` skill (see `skills/task-context/SKILL.md`), which
composes a per-task context file at
`specs/<branch>/task-context/<TID>-<slug>.md` ahead of the implementer
dispatch. This integration is **opt-in**.

### When the integration is active

Either:

1. The active preset's `preset.yaml` declares `task_context: true`, OR
2. The orchestrator was invoked with `aiadev preflight implement
   --task-context`.

When neither flag is set, the implementer prompt below — the inline
"Spec context / Plan context / Files to create or modify" form — runs
**byte-for-byte unchanged**. The task-context wiring is purely additive.

### When active, the loop changes

Insert two extra steps between step 3 (Treat `in_progress` as `pending`)
and step 4 (Dispatch implementer):

3.5. **Compose the task-context file.** Invoke the `task-context` skill
     for the current `<TID>`. Mechanically that runs the helper:

   ```bash
   python -c "from pathlib import Path; from aiadev.task_context import compose; print(compose(Path.cwd(), '<TID>'))"
   ```

   The call returns the path to the rendered file under
   `specs/<branch>/task-context/`. If a previous task-context file
   already exists for this `<TID>`, check `aiadev.task_context.is_stale`
   first and skip the recompose when it returns `False` — the same
   artifact is reused across retries within a session.

   ```bash
   python -c "from pathlib import Path; from aiadev.task_context import is_stale; print(is_stale(Path('specs/<branch>/task-context/<TID>-<slug>.md')))"
   ```

3.6. **Replace the implementer prompt.** Instead of the inline
     `Spec context` / `Plan context` / `Files to create or modify`
     blocks documented in the implementer-prompt section below,
     dispatch the implementer with this shorter prompt that loads the
     per-task context by path:

   ```markdown
   You are implementing Task <TID> of an approved plan.

   Your full per-task context file lives at:
   specs/<branch>/task-context/<TID>-<slug>.md

   Read it first. It contains the spec slice, plan slice,
   files-to-modify with excerpts, the TDD checklist, and a pointer to
   the previous task-context (if any).

   Workflow: test-first. Write a failing test, confirm it fails for
   the right reason, implement the minimum code to pass, confirm it
   passes. Run only the tests that exercise the changed code.

   Return exactly one status as the first line of your response:
   - DONE
   - DONE_WITH_CONCERNS
   - NEEDS_CONTEXT
   - BLOCKED
   ```

The remaining loop steps (5 onwards: status handling, reviewer,
`aiadev tasks done`) are unchanged.

## Model selection

| Task type | Model |
|---|---|
| Mechanical edits to 1-2 files with an unambiguous spec | Haiku |
| Integration work, judgment calls, new modules | Sonnet |
| Architectural decisions, cross-cutting refactors, review | Opus |

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
Run only the tests that exercise the changed code (the new test plus
any module-level or related-file tests). The full suite is the
`finishing-a-branch` gate, not a per-task gate.

Return exactly one status as the first line of your response:
- DONE — implementation complete, task-scoped tests passing
- DONE_WITH_CONCERNS — complete, but with issues worth raising [list]
- NEEDS_CONTEXT — cannot proceed without [list]
- BLOCKED — cannot proceed because [specific cause]
```

Project-specific conventions (stack, patterns, commit style) belong in the active preset's `CLAUDE.md`, not in this prompt — the subagent will read them from the project root.

## Status handling

- **DONE** — advance to review.
- **DONE_WITH_CONCERNS** — decide: does the concern block the spec? If yes, fix before review. If no (quality only), pass to the reviewer to judge.
- **NEEDS_CONTEXT** — provide exactly what was asked for and re-dispatch. Never guess.
- **BLOCKED** — find the root cause before retrying. Common causes: an unimplemented upstream task (fix ordering in `tasks.md`), a design conflict (escalate to the user), or an environment issue (invoke `systematic-debugging`).

## Reviewer prompt

```markdown
You are the single reviewer for one task. Two passes, in order.

Inputs: spec acceptance scenarios, task description, diff (from git),
test output, active preset `CLAUDE.md`.

Pass 1 — conformance. Every acceptance scenario is exercised by a test;
API shape, data model and error paths match the spec.
If pass 1 finds violations, stop: report them and skip pass 2.

Pass 2 — quality. Preset patterns followed; no security issues
(injection, IDOR, XSS, secrets); no performance traps; explicit error
handling; no gratuitous abstraction; tests cover happy path and a failure.

First line: APPROVED, or CHANGES_REQUESTED followed by file:line fixes.
```

## Reviewer re-dispatch gate

Story 3 of `specs/0014-bmad-inspired-evolutions/spec.md` adds the
zero-findings-halt rule for reviewer subagents (`code-reviewer`,
`spec-document-reviewer`, `plan-document-reviewer`). The agent-side
contract lives in `agents/<reviewer>.md` under the
"Output rule for APPROVED on non-trivial change" section. The
orchestrator-side counterpart — detecting violations and re-dispatching
— lives HERE.

For the reviewer dispatched in step 6 of the loop:

1. **Read the verdict line.** If the first line is `APPROVED`, parse
   the rest of the response.
2. **Detect the `### Why no issues` block.** A valid response has
   either a `### Why no issues` H3 with ≥ 3 bullet items each in the
   shape `<file:line> — <verification>`, OR (in terse-mode, see
   `.claude/rules/terse-mode.md`) ≥ 3 lines starting with the green
   glyph `🟢 file:line — verification`. Anything else is a missing
   block.
3. **Decide whether the change is non-trivial.** Use the canonical
   cl-5 definition: `git diff --shortstat --ignore-blank-lines` > 10
   LOC after dropping `.md`, `.json`, `.lock`, `.toml`, and any path
   under `docs/`. Spec/plan creation under `specs/<branch>/{spec,plan}.md`
   is ALWAYS non-trivial. The helper
   `aiadev.review_log.is_non_trivial_change` implements this exactly;
   `aiadev preflight requesting-code-review` exposes the same check
   from the CLI.
4. **Append a review-log entry** to `specs/<branch>/.review-log.jsonl`
   regardless of verdict. Shape:
   `{"timestamp": <ISO-8601 UTC>, "reviewer": <name>, "verdict":
   "APPROVED"|"CHANGES_REQUESTED", "has_why_no_issues_block": <bool>,
   "task_id": <TID>}`. Use `aiadev.review_log.append_review_entry`.
5. **Re-dispatch when the rule is violated.** If verdict is `APPROVED`,
   the change is non-trivial, and the `### Why no issues` block is
   missing, dispatch the SAME reviewer again with reinforced
   adversarial framing. The second prompt MUST escalate to something
   like: "You approved without justifying. Assume there is at least one bug
   and either show it OR justify the absence by category (security,
   performance, spec compliance, tests, complexity)." See
   `agents/<reviewer>.md` for the canonical wording.
6. **Hard limit: 2 re-dispatches per reviewer per task.** On the
   third dispatch attempt, accept the verdict but append a
   `WARNING: reviewer exhausted re-dispatch budget without justification`
   line to `.review-log.jsonl` and proceed. Plan ADR-4 calls this out
   as the loop-prevention guarantee.
7. **Trivial-change exception.** If the change is trivial (≤ 10 LOC
   after the cl-5 exclusions), the rule does not apply — accept the
   `APPROVED` verdict silently and do not re-dispatch. Story 3 sc3
   exists to keep noise out of the loop.

## Rules that do not bend

- Never skip the per-task review. Quality comes from the review, not from the implementer.
- Never run the quality pass while conformance has open violations.
- Never dispatch implementation subagents in parallel for tasks that touch the same files. Serial is safer and the cost is negligible compared to a botched merge.
- Never forward the full session transcript to a subagent. Craft a focused prompt each time — the subagent should be able to succeed with no other context.
- One task per commit; the commit message references the task id.

## Error handling for the pipeline itself

If the loop fails (a subagent returns garbage, or two review attempts produce contradictory verdicts):

1. Pause the pipeline. Do not try to paper over it by advancing.
2. Write a short incident note in `specs/<branch>/tasks.md` under the affected task.
3. Notify the user with: what failed, what you tried, what you need to proceed.
