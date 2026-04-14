---
name: constitution
description: "Amend constitution.md (framework, preset, or project). Enforces the amendment process: issue first, one article per PR, reviewer non-author."
version: 0.2.0
inputs:
  - type: text
    description: Proposed amendment (new article, edit, or repeal) with motivation.
outputs:
  - type: file
    path: constitution.md
  - type: file
    path: CHANGELOG.md
requires:
  - constitution
---

# Constitution

Edit the framework constitution (or a preset/project constitution) through its documented amendment process. This skill exists so amendments do not happen ad-hoc.

**Announce at start:** "Using the constitution skill. Amendment-only scope; I will follow the process in constitution.md."

## Preconditions

- A `constitution.md` exists at the target level (framework root, preset root, or project root).
- The caller has a concrete amendment in mind — "what changes and why".

## Loop

1. **Confirm the target file.** Framework-level? Preset-level? Project-level? These three have different amendment rules; check the specific `constitution.md` for the exact process.
2. **Check for an issue.** Amendment requires an issue on the repository stating article, motivation, and blast radius. If none exists, stop here and ask the user to open it before editing.
3. **One article per amendment.** If the user wants to change three articles, produce three separate PR plans — do not bundle.
4. **Edit the target file** minimally:
   - New article → append; renumber only if strictly necessary.
   - Edit an existing article → preserve the four fields (Statement, Rationale, Test, Waivable). Do not reformat unrelated text.
   - Repeal → move the article to a new **Repealed** section at the bottom with the version and reason; do not silently delete.
5. **Bump the version** at the top of the file per semver:
   - Patch: clarification, typo, wording.
   - Minor: new article, tightened test, added waiver.
   - Major: removed article, removed waiver condition, or any change that would retroactively fail existing plans.
6. **Add a `Changed` entry to `CHANGELOG.md [Unreleased]`** naming the article and version delta.
7. **Open the PR** with the issue linked, a summary of the amendment, and the blast radius assessment.

## Rules

- Do not amend the constitution as a side effect of another PR. The skill exists precisely to keep this explicit.
- Do not approve your own amendment. A non-author reviewer is required; major-bump amendments need two reviewers and a 48-hour comment window.
- Do not widen waivers without evidence that a narrower waiver is causing real harm.

## Hand-off

- PR merged → subsequent plans must update their Constitution Check to reflect the new article.
- Amendment rejected → document the rejection rationale under the issue; do not silently resubmit.
