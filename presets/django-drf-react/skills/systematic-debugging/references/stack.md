# Stack evidence and bug patterns (django-drf-react)

## Collect evidence by layer

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
