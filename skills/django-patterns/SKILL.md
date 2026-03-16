---
name: django-patterns
description: Conventions and patterns for Django 5.2 + DRF development. Use when creating new apps, models, serializers, views, or URLs.
---

# Django Patterns

Conventions for Django 5.2 + Django REST Framework based on the project architecture.

## New App Checklist

When creating a new Django app:

```bash
cd backend && python manage.py startapp <appname>
```

Then follow this order:
1. `models.py` — Models with proper fields, managers, Meta
2. `migrations/` — `makemigrations` after each model change
3. `serializers.py` — DRF serializers
4. `services/` — Business logic (never in views or models)
5. `views.py` — ViewSets, minimal logic
6. `urls.py` — Router registration
7. `admin.py` — Admin registration
8. `tasks.py` — Celery tasks (if async)
9. `tests/` — Tests for each layer
10. Register in `config/settings.py` → `INSTALLED_APPS`
11. Include in `config/urls.py`

## Models

### Standard Model Pattern

```python
# backend/<app>/models.py
import uuid
from django.conf import settings
from django.db import models
from core.fields import EncryptedTextField
from shared.managers import UserManager


class MyModel(models.Model):
    # Always UUID primary key
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # User FK with UserManager
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='<app>_<model_plural>',
    )

    # Status fields with choices
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Sensitive data — always encrypted
    api_token = EncryptedTextField(null=True, blank=True)

    # Flexible JSON storage for provider-specific config
    config = models.JSONField(default=dict, blank=True)

    # Audit timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # UserManager for automatic user-scoped querysets
    objects = UserManager()

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
        ]
        # unique_together for compound uniqueness
        unique_together = [('user', 'name')]

    def __str__(self):
        return f"{self.name} ({self.status})"
```

### Migration Best Practices

```bash
# After changing models:
python manage.py makemigrations <app>
python manage.py migrate

# Check for conflicts:
python manage.py showmigrations

# Squash migrations (when feature branch is complete):
python manage.py squashmigrations <app> 0001 0010
```

## Serializers

```python
# backend/<app>/serializers.py
from rest_framework import serializers
from .models import MyModel


class MyModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = MyModel
        fields = ['id', 'status', 'config', 'created_at', 'updated_at']
        read_only_fields = ['id', 'status', 'created_at', 'updated_at']

    def validate_config(self, value):
        """Validate config structure."""
        required_keys = ['key1', 'key2']
        for key in required_keys:
            if key not in value:
                raise serializers.ValidationError(f"Missing required key: {key}")
        return value


class MyModelCreateSerializer(serializers.ModelSerializer):
    """Separate serializer for creation — different fields."""
    class Meta:
        model = MyModel
        fields = ['name', 'config', 'api_token']
        extra_kwargs = {
            'api_token': {'write_only': True},  # Never expose in response
        }

    def create(self, validated_data):
        # Inject user from request context
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
```

## Views (ViewSets)

```python
# backend/<app>/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import MyModel
from .serializers import MyModelSerializer, MyModelCreateSerializer
from .services.my_service import MyService


class MyModelViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = MyModelSerializer

    def get_queryset(self):
        # Always scope to current user
        return MyModel.objects.for_user(self.request.user)

    def get_serializer_class(self):
        if self.action == 'create':
            return MyModelCreateSerializer
        return MyModelSerializer

    def perform_create(self, serializer):
        instance = serializer.save(user=self.request.user)
        # Trigger async work after creation
        from django.db import transaction
        transaction.on_commit(lambda: process_task.delay(str(instance.id)))

    @action(detail=True, methods=['post'])
    def trigger_action(self, request, pk=None):
        """Custom action endpoint: POST /api/v1/<app>/<id>/trigger_action/"""
        obj = self.get_object()
        service = MyService(obj)
        result = service.do_something()
        return Response({'status': 'ok', 'result': result})
```

## URLs

```python
# backend/<app>/urls.py
from rest_framework.routers import DefaultRouter
from .views import MyModelViewSet

router = DefaultRouter()
router.register(r'<endpoint>', MyModelViewSet, basename='<app>-<model>')

urlpatterns = router.urls
```

```python
# backend/config/urls.py
urlpatterns = [
    ...
    path('api/v1/<app>/', include('<app>.urls')),
]
```

## Services Layer

Business logic lives in `services/`, not in views or models:

```python
# backend/<app>/services/my_service.py
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class MyService:
    """Service for <description>. Never instantiated with user — always with domain object."""

    def __init__(self, obj: MyModel):
        self.obj = obj

    def do_something(self) -> dict:
        """<Description of what this does>."""
        logger.info(f"[{self.__class__.__name__}] do_something obj_id={self.obj.id}")
        try:
            result = self._internal_logic()
            logger.info(f"[{self.__class__.__name__}] completed obj_id={self.obj.id}")
            return result
        except Exception as e:
            logger.error(f"[{self.__class__.__name__}] failed obj_id={self.obj.id}: {e}")
            raise

    def _internal_logic(self) -> dict:
        # Private implementation
        ...
```

## Provider Pattern (for external integrations)

Used for Git providers, issue trackers, AI providers, etc.:

```python
# backend/integrations/providers/base.py
from typing import Protocol

class ExternalProvider(Protocol):
    def connect(self) -> bool: ...
    def fetch_data(self, cursor: str) -> list: ...
    def post_result(self, data: dict) -> str: ...

# Concrete implementations:
class GitHubProvider:
    def connect(self) -> bool: ...
class GitLabProvider:
    def connect(self) -> bool: ...

# Factory:
def get_provider(config: IntegrationConfig) -> ExternalProvider:
    providers = {
        'github': GitHubProvider,
        'gitlab': GitLabProvider,
    }
    return providers[config.provider_type](config)
```

## Testing

```python
# backend/tests/<app>/test_<module>.py
import pytest
from tests.factories import UserFactory, MyModelFactory


@pytest.fixture
def user(db):
    return UserFactory()


@pytest.fixture
def authenticated_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client


@pytest.mark.django_db
def test_create_endpoint(authenticated_client, user):
    payload = {'name': 'Test', 'config': {'key1': 'val', 'key2': 'val'}}
    response = authenticated_client.post('/api/v1/<app>/<endpoint>/', payload, format='json')
    assert response.status_code == 201
    assert response.data['name'] == 'Test'


@pytest.mark.django_db
def test_user_isolation(authenticated_client, db):
    """Users cannot see other users' data."""
    other_user = UserFactory()
    other_obj = MyModelFactory(user=other_user)

    response = authenticated_client.get(f'/api/v1/<app>/<endpoint>/{other_obj.id}/')
    assert response.status_code == 404  # Not 403 — don't leak existence
```
