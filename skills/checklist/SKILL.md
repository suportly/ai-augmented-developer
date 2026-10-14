---
name: checklist
description: Run a category-specific quality pass (security / performance / accessibility / i18n / privacy / observability / token-economy) against the current plan and code.
metadata:
  aiadev:
    version: 0.2.0
    inputs:
    - type: text
      description: Category name (security, performance, accessibility, internationalization, privacy, observability, token-economy, or a preset-defined category).
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

Focused quality pass in one category.

**Announce at start:** "Using the checklist skill in <category> mode."

## Preconditions

- `plan.md` exists. Running a checklist before `plan` is premature.
- `templates/checklist-template.md` is available.

## Loop

1. **Copy the template** to `specs/<branch>/checklists/<category>.md`.
2. **Set the Scope section.** Which parts of the plan does this pass cover; which are out of scope and why.
3. **For every item in the category's list**:
   - Read the relevant code / plan / tests.
   - Decide `PASS`, `FAIL`, or `N/A`.
   - Paste or link the evidence that supports the status.
4. **If the preset defines extra items**, run them too. Do not silently skip.
5. **Failed items go in their own table** with a remediation note and owner task id (create a new `T<NNN>` in `tasks.md` if none exists).
6. **Sign off** when every non-`N/A` item is `PASS` or has an owner task.

## Items per category

Read only `references/<category>.md`: security, performance, accessibility, i18n (internationalization), token-economy. Without a file (privacy, observability, preset-defined) use preset/plan items

## Rules

- No `PASS` without evidence; "looks fine" is not evidence.
- Do not fix findings inline; open a task, and the fix goes through `implement`.
- One category per file; never combine.

## Hand-off

- All items resolved → append the checklist result to the PR body in `requesting-code-review`.
- Failed items with owner tasks → the owner tasks go into the next `implement` run.
