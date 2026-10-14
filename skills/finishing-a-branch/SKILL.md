---
name: finishing-a-branch
description: Use after code review is approved to finalize, push, open PR, and clean up the development branch.
---

# Finishing a Development Branch

Complete the development cycle: final checks, push, open PR, link to issue, clean up.

**Announce at start:** "Using finishing-a-branch skill. Finalizing the branch."

## Pre-Flight Checklist

Before pushing:

- [ ] Run `aiadev preflight finishing-a-branch --feature <slug>` and confirm exit 0. The CLI checks every upstream artifact and refuses to proceed unless `.aiadev/review.yaml` records `status: approved`. Bypass is `AIADEV_PREFLIGHT=warn` (debug only).
- [ ] Code review approved (no outstanding CHANGES_REQUESTED)
- [ ] All tests pass
- [ ] No type errors
- [ ] No linting errors
- [ ] Migrations (if any) are clean: no unapplied, no conflicts
- [ ] Branch is rebased on main/develop
  ```bash
  git fetch origin && git rebase origin/main
  ```

## Commit Cleanup (Optional)

If commits are messy, squash into logical units:
```bash
# Squash last N commits into logical commits
git rebase -i HEAD~N
# Use 'r' (reword) for commits to keep, 's' (squash) for ones to fold in
```

**Commit message format:**
```
feat(<app>): short description of what was added

- Detail 1
- Detail 2

Closes #<issue_number>
```

## Push and Open PR

```bash
git push origin <branch-name>
```

Then open PR with this template:
```markdown
## Summary
- [What was built — bullet points]
- [Key technical decisions]

## Traceability
- Closes #<issue_number>
- Spec: `specs/YYYY-MM-DD-<feature>/spec.md`
- Plan: `specs/YYYY-MM-DD-<feature>/plan.md`

## Test Plan
- [ ] Test suite passes
- [ ] Type check and lint clean
- [ ] Manual smoke test performed

## Screenshots (if UI changes)
<add if applicable>
```

## After PR Is Opened

1. **Link PR to issue** in the description (`Closes #N`)
2. **Notify** relevant reviewers if needed
3. **Update spec status** in `specs/YYYY-MM-DD-<feature>/spec.md`:
   ```
   **Status**: PR Open — #<PR number>
   ```

## Merge Decision

When PR is approved and CI passes:

```bash
# Squash merge (preferred for clean history)
git checkout main && git merge --squash <branch>
git commit -m "feat(<scope>): <description> (#<PR>)"

# Or regular merge (preserves history)
git merge <branch>
```

After merge:
```bash
# Delete remote branch
git push origin --delete <branch>

# Delete local branch
git branch -d <branch>
```

## Deployment After Merge

Deploy according to what changed.

If `references/stack.md` exists beside this file, read it for stack-specific guidance.
