---
description: Branch naming, commit messages, PR hygiene conventions.
alwaysApply: true
---

# Git workflow

## Branches

- One feature / fix per branch. Do not mix refactors with features.
- Branch names: `<type>/<short-kebab-slug>`.
  - `feature/` — new capability
  - `fix/` — bug fix
  - `chore/` — tooling, deps, build, CI
  - `docs/` — documentation only
  - `refactor/` — behaviour-preserving change
- Keep branches short-lived. If a branch is older than a week and not
  shipped, rebase or split.

## Commits

- Conventional-commits-style subject line, imperative mood,
  under 72 characters: `feat(orders): add soft-cancellation endpoint`.
- Body (optional) explains **why**, not what — the diff is the what.
  Wrap at 72 columns.
- One logical change per commit. If you need the word "and" in the
  subject, split it.
- No `WIP`, `fix stuff`, `wip later` on shared branches. Rebase them
  out before pushing.
- Never amend or force-push a commit that others may have pulled.

## Rebasing

- Prefer rebase over merge for keeping feature branches up to date with
  `main`. The history stays linear and `git bisect` stays useful.
- Resolve conflicts locally, run tests, then push. Do not push a
  half-rebased branch and "fix later".

## Pull requests

- Title = the subject of the top commit. Body answers three questions:
  1. **What changed?** bullet list of what reviewers will see in the diff.
  2. **Why?** the user story / ticket / incident this resolves.
  3. **How to verify?** commands, URLs, or manual steps the reviewer runs.
- Include screenshots for any UI change.
- Link the spec or issue. PRs that ship code without a spec violate
  Article I.
- Keep PRs under ~500 changed lines where possible. Bigger PRs are
  valid only for mechanical refactors, migrations, or generated code.

## Forbidden

- Committing build artefacts, `.env`, `node_modules`, `.venv`,
  `__pycache__`, or IDE config (unless the project checks those in
  deliberately).
- `git commit --no-verify` to skip hooks without explicit authorisation.
- Force-push to `main` / `master` / any protected branch.
- "Co-Authored-By" lines for automated tools unless the project
  explicitly requires them.
