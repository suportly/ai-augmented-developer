# Task context: {{TASK_ID}} — {{TASK_TITLE}}

> Produced by the `task-context` skill before each task in `implement`'s
> loop. Carries everything the implementer subagent needs for this one
> task. Generated; do not hand-edit (changes are overwritten on next
> compose).

**Branch:** `{{BRANCH}}`
**Generated:** {{DATE}}
**Spec:** [{{SPEC_PATH}}]({{SPEC_PATH}})
**Plan:** [{{PLAN_PATH}}]({{PLAN_PATH}})

---

<!-- section: spec-slice -->
## Spec slice — acceptance scenarios for this task

<!-- The skill copies the exact Given/When/Then scenarios from spec.md
     that this task exercises (per the task's "Spec scenarios:" line).
     Heading text may be translated for non-English specs; the
     section-anchor comment above is the schema contract that aiadev
     readers parse and must not be translated or removed. -->

{{SPEC_SLICE}}

<!-- section: plan-slice -->
## Plan slice — task block

<!-- Full T<NNN> block copied verbatim from plan.md / tasks.md so the
     implementer can read Files / Status / Acceptance / Notes without
     opening multiple files. -->

{{PLAN_SLICE}}

<!-- section: files -->
## Files to modify, with excerpts

<!-- Each file in the task's "Files:" list. For files marked `modify:`,
     paste an excerpt of the relevant region (max 40 lines per file).
     For files marked `create:` or `test:`, just list the path so the
     implementer knows it does not exist yet. -->

{{FILES_TO_MODIFY_WITH_EXCERPTS}}

<!-- section: tdd-checklist -->
## TDD checklist

<!-- Copied from skills/test-driven-development/SKILL.md so the
     implementer does not need to re-read that skill — the rules live
     here, in the task context, at dispatch time. -->

{{TDD_CHECKLIST}}

<!-- section: previous-task-context -->
## Previous task context

<!-- If task-context/T<NNN-1>-*.md exists, point to it so the
     implementer has continuity (e.g. "Last task added the helper X
     used here"). Set to the literal string `none` for the first task
     in the branch. -->

{{PREVIOUS_TASK_CONTEXT_POINTER}}

<!-- section: cross-references -->
## Cross-references

- Spec: [`{{SPEC_PATH}}`]({{SPEC_PATH}})
- Plan: [`{{PLAN_PATH}}`]({{PLAN_PATH}})
- TDD rules: [`skills/test-driven-development/SKILL.md`](../../skills/test-driven-development/SKILL.md)
