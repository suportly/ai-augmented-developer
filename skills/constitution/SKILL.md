---
name: constitution
description: "Bootstrap or amend constitution.md (framework, preset, or project). Inspects existing project context first; enforces the amendment process: issue first, one article per PR, reviewer non-author."
version: 0.3.0
inputs:
  - type: text
    description: Optional. Proposed amendment (new article, edit, or repeal) with motivation. If omitted, the skill inspects the project context and either proposes a bootstrap draft (when no constitution exists yet) or lists the current articles and asks which one to amend.
outputs:
  - type: file
    path: constitution.md
  - type: file
    path: CHANGELOG.md
requires:
  - constitution
---

# Constitution

Bootstrap a missing `constitution.md` or amend an existing one (framework, preset, or project) through its documented process. This skill exists so neither bootstrap nor amendment happens ad-hoc.

**Announce at start:** "Using the constitution skill. Inspecting project context first; will bootstrap if no constitution exists, else follow the amendment process."

## Preconditions

- The skill is invoked at the level you intend to change (project root, preset root, or framework root).

## Mode detection (run before anything else)

1. **Locate the relevant `constitution.md`.** Prefer the project root (current working directory). If absent, fall back to the closest preset; if still absent, the framework root.
2. **If no `constitution.md` exists at the project root**, enter **Bootstrap mode**:
   - Read whatever already describes the project: `CLAUDE.md` (project + user), `.claude/rules/*`, `package.json` / `pyproject.toml` / `requirements.txt` / `Cargo.toml`, `README.md`, top-level folder layout.
   - Render `templates/constitution-template.md` with values inferred from that context — project name, stack, project-specific articles drawn from the existing rules, tightened framework articles where the rules already imply a stricter version.
   - Present the rendered draft for review. Only ask targeted questions for items that genuinely cannot be inferred (adoption date, named reviewers, project-wide waivers).
   - On approval, write `constitution.md`, add an `Added` entry to `CHANGELOG.md [Unreleased]` at version `1.0.0`, and stop. The amendment loop does not apply to bootstrap.
3. **If `constitution.md` exists** and the user provided amendment text → continue with the amendment loop below.
4. **If `constitution.md` exists** and the user provided no text → list the current articles (number + title) and ask which one to amend, or whether to add a new one. Use the answer as the amendment scope and continue with the loop.

## Amendment loop

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

- Inspect the project context **before** asking the user anything. Generic "what change do you want?" questions are forbidden when CLAUDE.md, rules, and package files are sitting right there.
- Do not amend the constitution as a side effect of another PR. The skill exists precisely to keep this explicit.
- Do not approve your own amendment. A non-author reviewer is required; major-bump amendments need two reviewers and a 48-hour comment window.
- Do not widen waivers without evidence that a narrower waiver is causing real harm.
- In bootstrap mode, do not invent project-specific articles that are not backed by something in the existing context. Inferred is not the same as fabricated — when in doubt, leave the article out and let the user add it later.

## Hand-off

- Bootstrap merged → all subsequent plans must include a Constitution Check that satisfies the new project articles.
- Amendment merged → subsequent plans must update their Constitution Check to reflect the new article.
- Amendment rejected → document the rejection rationale under the issue; do not silently resubmit.
