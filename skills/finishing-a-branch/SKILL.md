---
name: finishing-a-branch
description: Use after code review is approved to finalize, push, open PR, and clean up the development branch.
---

# Finishing a Development Branch

Final checks, push, open PR, clean up.

## Pre-Flight Checklist

- [ ] `aiadev preflight finishing-a-branch --feature <slug>` exits 0. It refuses unless `.aiadev/review.yaml` records `status: approved` (bypass `AIADEV_PREFLIGHT=warn`, debug only).
- [ ] No outstanding CHANGES_REQUESTED; tests, types, lint clean; migrations (if any) clean
- [ ] Rebased: `git fetch origin && git rebase origin/main`

## Commits

Squash messy commits into logical units (`git rebase -i HEAD~N`). Format: `feat(<app>): short description`, body bullets, `Closes #<issue>`.

## Push and open PR

`git push origin <branch-name>`, then open the PR with:

```markdown
## Summary
- [What was built; key technical decisions]

## Traceability
- Closes #<issue_number>
- Spec: `specs/<feature>/spec.md`
- Plan: `specs/<feature>/plan.md`

## Test Plan
- [ ] Test suite passes
- [ ] Type check and lint clean
- [ ] Manual smoke test performed
```

Then set the spec's status to `PR Open — #<PR number>` and notify reviewers.

## Merge and clean up

When approved and CI passes, squash merge (preferred) or regular merge. Afterwards delete the remote (`git push origin --delete <branch>`) and local (`git branch -d <branch>`) branch, and deploy according to what changed.

If `references/stack.md` exists beside this file, read it for stack-specific guidance.
