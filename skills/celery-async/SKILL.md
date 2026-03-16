---
name: celery-async
description: Create, debug, and test Celery 5 async tasks with Redis. Use when adding background processing, scheduled jobs, or long-running AI operations.
---

# Celery Async Tasks

Patterns for Celery 5 + Redis with Django. All long-running operations (AI generation, git sync, notifications, pipeline execution) run as Celery tasks.

## When to Use Celery

| Use Celery | Don't use Celery |
|-----------|-----------------|
| AI content generation (> 1s) | Simple DB reads |
| Git repository sync | Short computations |
| Email/notification sending | Auth checks |
| Pipeline execution (autodev) | Data validation |
| PDF generation | CRUD operations |
| Anything user should not wait for | |

**Rule:** If a request takes > 2 seconds, move it to Celery.

## Standard Task Pattern

```python
# backend/<app>/tasks.py
import logging
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,     # 1 minute base delay
    time_limit=300,              # 5 minutes hard limit
    soft_time_limit=270,         # 4.5 minutes soft (raises SoftTimeLimitExceeded)
    name='<app>.tasks.<task_name>',  # Explicit name for stability
)
def my_task(self, obj_id: str) -> None:
    """<Description of what this task does>.

    Args:
        obj_id: UUID string of the target object
    """
    logger.info(f"[{self.name}] START obj_id={obj_id} attempt={self.request.retries + 1}")

    try:
        from .<app>.models import MyModel
        obj = MyModel.objects.get(id=obj_id)

        # Business logic here
        result = do_the_work(obj)

        obj.status = 'completed'
        obj.completed_at = timezone.now()
        obj.result = result
        obj.save(update_fields=['status', 'completed_at', 'result'])

        logger.info(f"[{self.name}] DONE obj_id={obj_id}")

    except MyModel.DoesNotExist:
        # Don't retry — object is gone
        logger.warning(f"[{self.name}] SKIP obj_id={obj_id} — not found")

    except SoftTimeLimitExceeded:
        # Clean up before hard kill
        obj.status = 'failed'
        obj.error = 'Timeout exceeded'
        obj.save(update_fields=['status', 'error'])
        logger.error(f"[{self.name}] TIMEOUT obj_id={obj_id}")
        raise

    except Exception as exc:
        logger.error(f"[{self.name}] ERROR obj_id={obj_id}: {exc}", exc_info=True)
        # Update status for visibility
        try:
            obj.status = 'failed'
            obj.error = str(exc)[:500]
            obj.save(update_fields=['status', 'error'])
        except Exception:
            pass  # Don't fail the retry on status update failure

        raise self.retry(
            exc=exc,
            countdown=60 * (2 ** self.request.retries),  # Exponential: 1min, 2min, 4min
        )
```

## Dispatching Tasks Safely

**Always use `transaction.on_commit`** to avoid race conditions:

```python
# backend/<app>/views.py or services/
from django.db import transaction

def create_and_process(user, data):
    obj = MyModel.objects.create(user=user, status='pending', **data)

    # This ensures the DB commit happens BEFORE the task reads the object
    transaction.on_commit(lambda: my_task.delay(str(obj.id)))

    return obj
```

**Never dispatch from a signal directly** (same race condition):
```python
# WRONG
@receiver(post_save, sender=MyModel)
def on_create(sender, instance, created, **kwargs):
    if created:
        my_task.delay(str(instance.id))  # Race condition!

# CORRECT
@receiver(post_save, sender=MyModel)
def on_create(sender, instance, created, **kwargs):
    if created:
        transaction.on_commit(lambda: my_task.delay(str(instance.id)))
```

## Scheduled Tasks (Celery Beat)

```python
# backend/config/celery.py
from celery.schedules import crontab

app.conf.beat_schedule = {
    'poll-issue-trackers': {
        'task': 'autodev.tasks.poll_issue_trackers',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
    },
    'sync-git-activity': {
        'task': 'gitdata.tasks.sync_all_providers',
        'schedule': crontab(hour='*/1'),  # Every hour
    },
    'generate-weekly-highlights': {
        'task': 'articles.tasks.generate_weekly_highlights',
        'schedule': crontab(day_of_week='monday', hour=9, minute=0),
    },
}
```

## Task Chaining and Groups

```python
from celery import chain, group, chord

# Chain: A → B → C (sequential)
pipeline = chain(
    analyze_demand.s(demand_id),
    generate_plan.s(),
    execute_implementation.s(),
    create_pr.s(),
)
pipeline.delay()

# Group: A + B + C (parallel, no dependency)
sync_jobs = group(
    sync_github.s(provider_id),
    sync_gitlab.s(provider_id),
)
sync_jobs.delay()

# Chord: parallel → single callback
processing = chord(
    group(process_repo.s(repo_id) for repo_id in repo_ids),
    generate_summary.s(),  # Called after all process_repo finish
)
processing.delay()
```

## Testing Celery Tasks

```python
# backend/tests/<app>/test_tasks.py
import pytest
from unittest.mock import patch, MagicMock
from <app>.tasks import my_task
from tests.factories import MyModelFactory


@pytest.mark.django_db
def test_task_processes_successfully(db):
    """Task changes status to completed on success."""
    obj = MyModelFactory(status='pending')

    # Execute task synchronously in test
    my_task.apply(args=[str(obj.id)])

    obj.refresh_from_db()
    assert obj.status == 'completed'


@pytest.mark.django_db
def test_task_retries_on_transient_error(db):
    """Task retries on transient errors (network, timeout)."""
    obj = MyModelFactory(status='pending')

    with patch('myapp.services.external_api.call', side_effect=ConnectionError('timeout')):
        with pytest.raises(my_task.MaxRetriesExceededError):
            my_task.apply(args=[str(obj.id)], retries=3)  # Exhaust retries

    obj.refresh_from_db()
    assert obj.status == 'failed'
    assert 'timeout' in obj.error.lower()


@pytest.mark.django_db
def test_task_skips_missing_object(db):
    """Task exits gracefully when object not found."""
    non_existent_id = '00000000-0000-0000-0000-000000000000'
    # Should not raise
    my_task.apply(args=[non_existent_id])
```

**Settings for testing (conftest.py):**
```python
# backend/conftest.py
@pytest.fixture(autouse=True)
def celery_eager(settings):
    """Execute Celery tasks synchronously in all tests."""
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.CELERY_TASK_EAGER_PROPAGATES = True
```

## Debugging

```bash
# Watch task execution in real-time
docker compose logs -f celery

# Inspect active tasks
celery -A config inspect active

# Inspect registered tasks
celery -A config inspect registered | grep <app>

# Purge a specific queue
celery -A config purge -Q <queue_name>

# Check Redis queue length
docker compose exec redis redis-cli llen celery

# Monitor with Flower (if configured)
celery -A config flower --port=5555
```

## Common Pitfalls

| Problem | Cause | Fix |
|---------|-------|-----|
| Object not found in task | Task ran before DB commit | Use `transaction.on_commit()` |
| Duplicate processing | Task not idempotent | Add `if obj.status != 'pending': return` guard |
| Task runs forever | No time_limit | Add `time_limit` + `soft_time_limit` |
| Memory leak in worker | No worker recycling | Set `CELERYD_MAX_TASKS_PER_CHILD=100` |
| N+1 in task | No prefetch in queryset | Add `select_related('user', 'config')` |
