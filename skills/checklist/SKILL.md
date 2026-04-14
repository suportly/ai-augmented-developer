---
name: checklist
description: Run a category-specific quality pass (security / performance / accessibility / i18n / privacy / observability) against the current plan and code.
version: 0.2.0
inputs:
  - type: text
    description: Category name (security, performance, accessibility, internationalization, privacy, observability, or a preset-defined category).
  - type: dir
    path: specs/<branch>/
outputs:
  - type: file
    path: specs/<branch>/checklists/<category>.md
requires:
  - constitution
  - templates/checklist-template.md
---

# Checklist

Apply a focused quality pass in one category. Default categories ship with the template; presets can add more.

**Announce at start:** "Using the checklist skill in <category> mode."

## Preconditions

- `plan.md` exists. Running a checklist before `plan` is premature.
- `templates/checklist-template.md` is available.
- The category is either a default or registered by the active preset.

## Loop

1. **Copy the template** to `specs/<branch>/checklists/<category>.md`.
2. **Set the Scope section.** Which parts of the plan does this pass cover; which are out of scope and why.
3. **For every item in the category's default list**:
   - Read the relevant code / plan / tests.
   - Decide `PASS`, `FAIL`, or `N/A`.
   - Paste or link the evidence that supports the status.
4. **If the preset defines extra items**, run them too. Do not silently skip.
5. **Failed items go in their own table** with a remediation note and owner task id (create a new `T<NNN>` in `tasks.md` if none exists).
6. **Sign off** when every non-`N/A` item is `PASS` or has an owner task.

## Rules

- Do not mark an item `PASS` without evidence. "Looks fine" is not evidence.
- Do not fix findings inline. Open a task instead; the fix goes through `implement` like any other work.
- Do not combine categories. One file per category keeps reviewers honest.

## Hand-off

- All items resolved → append the checklist result to the PR body in `requesting-code-review`.
- Failed items with owner tasks → the owner tasks go into the next `implement` run.
