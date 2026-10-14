---
name: constitution
description: 'Bootstrap or amend constitution.md (framework, preset, or project). Inspects existing project context first; enforces the amendment process: issue first, one article per PR, reviewer non-author.'
metadata:
  aiadev:
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

Bootstrap a missing `constitution.md` or amend an existing one (framework, preset, or project) through its documented process; never ad hoc.

## Mode detection (run before anything else)

1. **Locate `constitution.md`**: project root first, then the closest preset, then the framework root.
2. **None at the project root → Bootstrap mode.**
   - Read what describes the project: `CLAUDE.md`, `.claude/rules/*`, package manifests, `README.md`, top-level layout.
   - Render `templates/constitution-template.md` from that context: project name, stack, articles drawn from existing rules, framework articles tightened where rules imply it.
   - Present the draft; ask only what cannot be inferred (adoption date, named reviewers, waivers).
   - On approval write `constitution.md`, add an `Added` entry to `CHANGELOG.md [Unreleased]` at `1.0.0`, and stop (no amendment loop).
3. **Exists + amendment text** → amendment loop.
4. **Exists, no text** → list the articles (number + title) and ask which to amend or add; continue with the loop.

## Amendment loop

1. **Confirm the level** (framework, preset, project); each has its own process in that `constitution.md`.
2. **An issue must exist** stating article, motivation, blast radius; otherwise stop and ask for it.
3. **One article per amendment**; several articles mean separate PR plans.
4. **Edit minimally.** New article: append, renumber only if necessary. Edit: keep the four fields (Statement, Rationale, Test, Waivable) and leave unrelated text alone. Repeal: move to a **Repealed** section at the bottom with version and reason, never silently delete.
5. **Bump the version** (semver): patch = clarification/typo; minor = new article, tightened test, added waiver; major = removed article or waiver condition, or anything that would retroactively fail existing plans.
6. **Add a `Changed` entry** to `CHANGELOG.md [Unreleased]` naming article and version delta.
7. **Open the PR** with the issue linked, a summary, and the blast radius.

## Rules

- Inspect project context before asking anything; no generic "what change do you want?".
- Never amend as a side effect of another PR; never approve your own amendment. A non-author reviewer is required; major bumps need two reviewers and a 48-hour comment window.
- Do not widen waivers without evidence a narrower one causes real harm.
- Bootstrap: no articles unbacked by existing context; when in doubt leave it out.

## Hand-off

Bootstrap or amendment merged → subsequent plans' Constitution Check covers the new articles. Rejected → record the rationale under the issue; do not silently resubmit.
