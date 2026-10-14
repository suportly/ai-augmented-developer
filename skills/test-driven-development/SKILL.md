---
name: test-driven-development
description: Use when implementing any feature or bugfix. Write the test first, always.
---

# Test-Driven Development (TDD)

## The Iron Law

```
NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST
```

Wrote code before the test? Delete it. Start over. No exceptions.

## RED → GREEN → REFACTOR Cycle

### RED — Write Failing Test

Write ONE minimal test showing what should happen.

**Requirements:**
- One behavior
- Clear name (what it tests + context)
- Real code (no unnecessary mocks)
- Must FAIL for the right reason (missing feature, not a typo)

**Verify RED — MANDATORY:**
- Test fails (not syntax error)
- Failure message is expected
- Fails because the feature is absent

### GREEN — Minimal Code

Write the simplest code to make the test pass. **Do not add features**, do not refactor other code.

**Verify GREEN — MANDATORY:**
- Test passes
- All other tests still pass
- Clean output (no errors, warnings)

### REFACTOR — Clean Up

Only after green. Keep tests green. Do not add behavior.

If `references/stack.md` exists beside this file, read it for stack-specific guidance.

## Exceptions (Ask the User)

- Throwaway prototypes
- Auto-generated code (automatic migrations)
- Configuration files

## TDD Commits

Always commit in complete cycles:
```bash
# After GREEN for each test
git add <tested-and-implemented-files>
git commit -m "test(<app>): RED→GREEN <tested-behavior>"
```
