# Reviewer re-dispatch gate

Canonical gate for reviewer subagents (`code-reviewer`, `spec-document-reviewer`,
`plan-document-reviewer`). The reviewer's output rule lives in `agents/<reviewer>.md`;
detecting violations and re-dispatching lives HERE, once. Run it after every reviewer
response: per task in `implement`, once per pass in `requesting-code-review`.

1. **Detect.** If the first line is `APPROVED`, look for the `### Why no issues`
   block: an H3 with ≥ 3 bullets shaped `<file:line> — <verification>`, or (terse-mode,
   `.claude/rules/terse-mode.md`) ≥ 3 lines `🟢 file:line — verification`.
   Anything else is a missing block.
2. **Log.** Append to `specs/<branch>/.review-log.jsonl` regardless of verdict, via
   `aiadev.review_log.append_review_entry`:
   `{"timestamp": <ISO-8601 UTC>, "reviewer": "code-reviewer", "verdict":
   "APPROVED"|"CHANGES_REQUESTED", "has_why_no_issues_block": <bool>, "task_id": <TID>}`.
   Branch-scoped reviews use `"task_id": "branch-review"`.
3. **Non-trivial?** cl-5 definition: `git diff --shortstat --ignore-blank-lines` (a task:
   the task diff; a branch review: `<base>...HEAD`, base = `git merge-base HEAD main`,
   never the empty working-tree diff) > 10 LOC
   after dropping `.md`, `.json`, `.lock`, `.toml` and `docs/`. Creating
   `specs/<branch>/{spec,plan}.md` is ALWAYS non-trivial.
   `aiadev.review_log.is_non_trivial_change` implements it; `aiadev preflight
   requesting-code-review` exposes it.
4. **Trivial exception.** A trivial change does not need the block: accept `APPROVED`
   silently and do not re-dispatch.
5. **Re-dispatch.** `APPROVED` + non-trivial + block missing: dispatch the SAME reviewer
   again with reinforced adversarial framing: "You approved without justifying.
   Assume there is at least one bug and either show it OR justify the absence by
   category (security, performance, spec compliance, tests, complexity)."
6. **Hard limit: 2 re-dispatches per reviewer** (per task, or per review pass for the
   branch). On the third attempt accept the verdict, append
   `WARNING: reviewer exhausted re-dispatch budget without justification` to
   `.review-log.jsonl` and proceed.
