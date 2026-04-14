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

## Patterns by Stack

### Django Backend (pytest + factory_boy)

```python
# Location: backend/<app>/tests/test_<module>.py
import pytest
from <app>.models import MyModel
from tests.factories import UserFactory, MyModelFactory

@pytest.mark.django_db
def test_my_behavior(db):
    # Arrange
    user = UserFactory()
    obj = MyModelFactory(user=user, status='pending')

    # Act
    result = my_service.process(obj.id)

    # Assert
    assert result.status == 'processed'
    obj.refresh_from_db()
    assert obj.status == 'processed'

@pytest.mark.django_db
def test_my_authenticated_endpoint(api_client, user_factory):
    user = user_factory()
    api_client.force_authenticate(user=user)
    response = api_client.post('/api/v1/<app>/action/', {'field': 'value'})
    assert response.status_code == 201
    assert response.data['field'] == 'value'
```

**Run:**
```bash
cd backend && pytest tests/<app>/test_<module>.py::test_my_behavior -v
```

### Celery Tasks (synchronous execution in tests)

```python
@pytest.mark.django_db
def test_my_task_processes_demand(db):
    demand = DemandFactory(status='pending')

    # Execute task synchronously in test
    result = my_task.apply(args=[str(demand.id)])

    assert result.successful()
    demand.refresh_from_db()
    assert demand.status == 'completed'
```

### AI Service (LiteLLM mock)

```python
from unittest.mock import patch, MagicMock

def test_ai_service_generates_content():
    mock_result = MagicMock()
    mock_result.content = '{"title": "Test", "content": "Content"}'
    mock_result.total_tokens = 100

    with patch('ai.service.AIService._call', return_value=mock_result):
        service = AIService()
        result = service.generate_diary(date='2026-03-16', commits=[])

    assert result['title'] == 'Test'
    assert result['content'] == 'Content'
```

### React Frontend (Jest + React Testing Library)

```typescript
// Location: frontend/src/__tests__/<Component>.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MyComponent } from '../components/MyComponent';

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } },
});

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
);

test('should display data after loading', async () => {
  render(<MyComponent />, { wrapper });

  expect(screen.getByRole('progressbar')).toBeInTheDocument();
  await waitFor(() => expect(screen.getByText('Expected Data')).toBeInTheDocument());
});
```

**Run:**
```bash
cd frontend && npx jest --no-coverage src/__tests__/MyComponent.test.tsx
```

### Mobile React Native (RNTL)

```typescript
// Location: <mobile-dir>/src/__tests__/<Screen>.test.tsx
import { render, screen } from '@testing-library/react-native';
import { MyScreen } from '../screens/MyScreen';

test('should render items list', async () => {
  render(<MyScreen />);
  await screen.findByText('Expected Item');
  expect(screen.getByText('Expected Item')).toBeTruthy();
});
```

**Run:**
```bash
cd <mobile-dir> && npx jest --no-coverage src/__tests__/MyScreen.test.tsx
```

## Exceptions (Ask the User)

- Throwaway prototypes
- Auto-generated code (automatic migrations)
- Configuration files

**Thinking about skipping TDD this time?** Stop. That's rationalization.

## TDD Commits

Always commit in complete cycles:
```bash
# After GREEN for each test
git add <tested-and-implemented-files>
git commit -m "test(<app>): RED→GREEN <tested-behavior>"
```
