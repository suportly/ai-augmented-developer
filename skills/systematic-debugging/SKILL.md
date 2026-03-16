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

**4. Collect evidence by layer**

**Django Backend:**
```bash
# Django logs
cd backend && python manage.py shell
>>> from django.test import Client; c = Client()
>>> # reproduce manually

# SQL generated
>>> from django.db import connection; connection.queries

# Celery worker logs
docker compose logs -f celery
```

**React Frontend:**
```bash
# Console errors
# Network tab — see exact request/response
# React Query Devtools — inspect query state
cd frontend && npx tsc --noEmit  # check TypeScript errors
```

**Celery/Redis:**
```bash
# Watch tasks in real-time
docker compose exec redis redis-cli monitor
# Check task errors
cd backend && celery -A config inspect active
```

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

## Bug Patterns by Stack

### Django — Common Bugs

```python
# Lazy queryset evaluation bug
# WRONG: objects never evaluated properly
items = MyModel.objects.filter(user=user)
if items:  # Evaluates, but creates new query on each access
    process(items[0])  # Another query

# CORRECT:
items = list(MyModel.objects.filter(user=user).select_related('user'))

# Test transaction bug
# Symptom: "object created but not found in service"
# Fix: @pytest.mark.django_db(transaction=True)

# Signal firing in test causing unexpected side effects
# Fix: disconnect signal in test or mock it
```

### Celery — Common Bugs

```python
# Bug: task not executing
# Check: CELERY_TASK_ALWAYS_EAGER=True in test settings?
# Check: task registered? celery -A config inspect registered

# Bug: retry storm
# Symptom: task retrying infinitely
# Fix: verify max_retries and exponential countdown

# Bug: object not found in task
# Cause: task ran before DB transaction committed
# Fix: use transaction.on_commit() to dispatch task
from django.db import transaction
transaction.on_commit(lambda: my_task.delay(obj.id))
```

### LiteLLM/AI — Common Bugs

```python
# Bug: API key not found
# Check: settings.ANTHROPIC_API_KEY / GEMINI_API_KEY configured?
# Check: _get_api_key_for_model() resolves the provider correctly?

# Bug: AI response timeout
# Check: LiteLLM default timeout (300s)
# Fix: add explicit timeout in kwargs

# Bug: JSON parsing fails
# Cause: model returned text before/after JSON
# Fix: use re.search to extract JSON
import re, json
match = re.search(r'\{.*\}', content, re.DOTALL)
if match:
    data = json.loads(match.group())
```

### TypeScript/React — Common Bugs

```typescript
// Bug: undefined not handled
// Symptom: "Cannot read properties of undefined"
// Fix: optional chaining + nullish coalescing
const value = data?.field ?? defaultValue;

// Bug: stale closure in useEffect
// Symptom: outdated value inside effect
// Fix: include correct dependencies in array
useEffect(() => {
  doSomething(currentValue);  // currentValue must be in deps
}, [currentValue]);

// Bug: TanStack Query not refetching
// Check: queryKey includes all params that affect the result?
const { data } = useQuery({
  queryKey: ['resource', userId, filter],  // include BOTH userId AND filter
  queryFn: () => fetchResource(userId, filter),
});
```

## Bug Report Format

After identifying root cause:
```
**Bug**: [short description]
**Root Cause**: [identified cause with evidence]
**Fix Applied**: [description of fix]
**Regression Test**: `tests/path/test_bug_fix.py::test_name`
**Verified**: [test passes + all other tests still pass]
```
