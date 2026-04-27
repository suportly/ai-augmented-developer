---
name: analyze
description: Check for drift between spec.md, plan.md, tasks.md, and the actual code. Reports the gaps; does not fix them.
version: 0.2.0
inputs:
  - type: dir
    path: specs/<branch>/
outputs:
  - type: text
    description: A gap report. Optionally written to specs/<branch>/analysis.md.
requires:
  - constitution
handoffs:
  - plan
  - tasks
  - clarify
---

# Analyze

Compare what the spec said, what the plan scheduled, what the tasks listed, and what the code actually did. Return a report of the drift.

**Announce at start:** "Using the analyze skill. I will report gaps; fixes are a separate pass."

## When to use

Run pre-flight first: `aiadev preflight analyze --feature <slug>`. Abort on non-zero exit unless `AIADEV_PREFLIGHT=warn` is set.

- Before opening the PR — sanity check that implementation matches spec.
- Mid-implementation, when something "feels off" — usually a missing task or a spec the plan ignored.
- After a long break — quickly regain context on a branch.

## Loop

1. **Collect.** Read `spec.md`, `plan.md`, `tasks.md`, and the diff of the branch vs its base.
2. **Map acceptance scenarios → tasks → commits.** Build a small table.
3. **Report four gap classes:**
   - **Spec without plan coverage** — an acceptance scenario that no plan phase addresses.
   - **Plan without task coverage** — a plan entry with no corresponding task.
   - **Task without code** — a task marked `done` whose files are missing or unchanged in the diff.
   - **Code without task** — files changed in the branch that no task asked for.
4. **Check the Constitution.** Article by article, does the current state still pass? Flag any that silently slipped to `FAIL`.
5. **Report.** Short, structured. Each gap has a file:line or commit hash and a suggested skill to invoke next.

## Rules

- Do not fix anything. Analysis and remediation are separate passes; mixing them hides the drift.
- Do not open issues or edit skill files — drop your report in `specs/<branch>/analysis.md` (optional) or straight to the user.
- No silent "looks fine". If there is truly no drift, say so explicitly.

## Hand-off

Suggest the skill most likely to close each gap:

- Spec gap → `clarify` or `specify` (for the missing scenario).
- Plan gap → `plan`.
- Task gap → `tasks`.
- Code drift → a new task plus `implement`.
- Constitution drift → open an amendment PR per `constitution.md`'s amendment process.
