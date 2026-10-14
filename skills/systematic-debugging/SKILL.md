---
name: systematic-debugging
description: Use when encountering any bug, test failure, or unexpected behavior. Investigate root cause BEFORE proposing any fix.
---

# Systematic Debugging

## The Iron Law

```
NO FIX WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

After 3 failed fix attempts: STOP and question the architecture.

## The Four Phases

### Phase 1: Root Cause Investigation

**1. Read the error message carefully**
- Full stack trace — don't skip lines
- Exact line of error
- Exception type

**2. Reproduce consistently**
- If it doesn't reproduce reliably, debugging cannot begin
- Isolate: smallest test case that reproduces the problem

**3. Check recent changes**
```bash
git log --oneline -20
git diff HEAD~1 -- <suspect-file>
```

**4. Collect evidence by layer** — logs, the exact request/response, the state each layer received.

If `references/stack.md` exists beside this file, read it for stack-specific guidance.

### Phase 2: Pattern Analysis

1. **Find working examples** — similar code in the same codebase that works
2. **Compare with reference** — diff between what works and what doesn't
3. **Identify differences** — what changed, what's missing
4. **Understand dependencies** — error may be in a different layer than the symptom

### Phase 3: Hypothesis and Testing

**Form a single hypothesis** — the most likely cause

**Test minimally:**
- Write a test that reproduces the bug
- Verify the test fails for the correct reason
- Apply a minimal fix

**When you don't know — say so explicitly:**
> "I don't know the root cause. My best hypothesis is X, but I need more evidence."

### Phase 4: Fix Implementation

1. **Create a regression test** that reproduces the bug
2. **Confirm the test fails** (RED)
3. **Implement a single fix** — no multiple simultaneous changes
4. **Verify the test passes** (GREEN) + all other tests still pass
5. **If fix doesn't work after 3 attempts** — STOP

**After 3+ failed fixes: Question the Architecture**
- Does the current design support the required behavior?
- Does it need structural refactoring?
- Escalate to the user with collected evidence

## Bug Report Format

After identifying root cause:
```
**Bug**: [short description]
**Root Cause**: [identified cause with evidence]
**Fix Applied**: [description of fix]
**Regression Test**: `tests/path/test_bug_fix.py::test_name`
**Verified**: [test passes + all other tests still pass]
```
