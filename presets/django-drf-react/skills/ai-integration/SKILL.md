---
name: ai-integration
description: Integrate AI capabilities using LiteLLM (multi-provider) or Claude Agent SDK. Use when adding AI-generated content, streaming responses, or autonomous code execution.
---

# AI Integration

Patterns and guidelines for integrating AI into Django + React projects using LiteLLM and Claude Agent SDK.

## LiteLLM — Multi-Provider AI Service

The `AIService` class (in `backend/ai/service.py`) is the centralized AI layer. Always use it — never call LiteLLM directly from views or tasks.

### Adding a New AI Feature

**1. Add the prompt template to `backend/ai/prompts.py`:**

```python
from string import Template

# Use Template ($variable) NOT str.format({variable})
# This prevents format-string injection from user-controlled data
MY_FEATURE_SYSTEM_PROMPT = """You are a [role]. [Instructions].

Respond in JSON format: {"field1": "...", "field2": [...]}"""

MY_FEATURE_USER_TEMPLATE = Template("""
Context: $context_variable
Input: $user_input
""")
```

**2. Add the method to `AIService`:**

```python
# backend/ai/service.py
def generate_my_feature(self, context: str, user_input: str) -> dict:
    """Generate [description]. Returns dict with field1, field2."""
    language_instruction = self._get_language_instruction()
    system = MY_FEATURE_SYSTEM_PROMPT + "\n" + language_instruction

    user_msg = MY_FEATURE_USER_TEMPLATE.substitute(
        context_variable=context,
        user_input=user_input,
    )

    result = self._call(
        model=self.chat_model,  # or self.fast_model for cheaper/faster
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_msg},
        ],
        json_mode=True,
    )

    # Parse JSON response robustly
    import json, re
    try:
        return json.loads(result.content)
    except json.JSONDecodeError:
        match = re.search(r'\{.*\}', result.content, re.DOTALL)
        if match:
            return json.loads(match.group())
        raise ValueError(f"AI returned non-JSON: {result.content[:200]}")
```

**3. Call from Celery task (preferred) or view:**

```python
# backend/<app>/tasks.py
from ai.service import AIService

@app.task(bind=True, max_retries=3)
def generate_my_feature_task(self, obj_id: str) -> None:
    obj = MyModel.objects.get(id=obj_id)
    service = AIService()

    try:
        result = service.generate_my_feature(
            context=obj.build_context(),
            user_input=obj.description,
        )
        obj.ai_output = result
        obj.status = 'completed'
        obj.save()
    except Exception as exc:
        obj.status = 'failed'
        obj.save()
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
```

### Model Selection Guide

| Use Case | Model Setting | Why |
|----------|--------------|-----|
| Complex reasoning, long context | `self.chat_model` (gemini-2.5-pro) | Best quality |
| Fast generation, simple tasks | `self.fast_model` (gemini-2.5-flash) | Cheaper + faster |
| Fallback | `self.fallback_model` (groq/llama) | When primary fails |
| Code execution, tool use | `anthropic/claude-sonnet-4-6` | Best for code |

### SSE Streaming (for chatbot/real-time responses)

```python
# backend/<app>/views.py
from django.http import StreamingHttpResponse
from ai.service import AIService

def stream_response(request, session_id):
    service = AIService()

    def event_stream():
        stream = service._call(
            model=service.chat_model,
            messages=build_messages(session_id),
            stream=True,
        )
        for chunk in stream:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                yield f"data: {json.dumps({'content': content})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingHttpResponse(
        event_stream(),
        content_type='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',  # Required for Nginx SSE
        }
    )
```

**Frontend SSE consumption:**
```typescript
// src/hooks/useStreamingChat.ts
export function useStreamingChat(sessionId: string) {
  const [content, setContent] = useState('');

  const startStream = useCallback(() => {
    const es = new EventSource(`/api/v1/chat/${sessionId}/stream/`);
    es.onmessage = (e) => {
      if (e.data === '[DONE]') { es.close(); return; }
      const { content: chunk } = JSON.parse(e.data);
      setContent(prev => prev + chunk);
    };
    return () => es.close();
  }, [sessionId]);

  return { content, startStream };
}
```

---

## Claude Agent SDK — Autonomous Code Execution

Use for autonomous code generation, the autodev pipeline, and any task requiring multi-step tool use.

### Setup

```python
# backend/autodev/services/code_executor.py
import claude_agent_sdk as sdk

async def execute_implementation(spec: str, repo_path: str) -> ExecutionResult:
    """Execute implementation plan using Claude Agent SDK in isolated environment."""

    system_prompt = f"""You are an expert software engineer implementing a feature.

Follow these rules:
1. Use TDD: write failing test → implement → verify passing
2. Follow existing codebase patterns
3. Make atomic commits after each working change
4. Stop and report if blocked after 3 attempts

Spec:
{spec}
"""

    result = await sdk.run(
        prompt=system_prompt,
        tools=["bash", "read", "write", "edit"],
        working_directory=repo_path,
        max_turns=50,
        timeout=1800,  # 30 minutes max
    )

    return ExecutionResult(
        success=result.exit_code == 0,
        output=result.output,
        files_changed=result.files_changed,
    )
```

### Security Constraints

- **Always run in isolated Docker container** — never on host
- **Mount repo as volume** — not the entire filesystem
- **Network access:** only to package registries (pip, npm) — not to production databases
- **Resource limits:** CPU 2 cores, RAM 4GB, disk 10GB

```yaml
# docker-compose.yml for sandbox
services:
  agent-sandbox:
    image: python:3.12-slim
    volumes:
      - ./repos/${REPO_ID}:/workspace:rw
    network_mode: none  # No network (install deps before running)
    mem_limit: 4g
    cpus: '2'
    read_only: false
    tmpfs:
      - /tmp
```

### Token Usage Tracking

Always log token usage for cost tracking:

```python
from ai.models import AIUsageLog

AIUsageLog.objects.create(
    user=user,
    feature='autodev_pipeline',
    model=result.model,
    prompt_tokens=result.prompt_tokens,
    completion_tokens=result.completion_tokens,
    total_tokens=result.total_tokens,
    cost_usd=calculate_cost(result),
)
```

---

## Testing AI Features

Always mock the AI service in tests — never call real APIs:

```python
from unittest.mock import patch, MagicMock

@pytest.mark.django_db
def test_my_feature_generates_content(db):
    mock_result = MagicMock()
    mock_result.content = '{"field1": "test", "field2": ["item1"]}'
    mock_result.total_tokens = 500

    with patch.object(AIService, '_call', return_value=mock_result):
        service = AIService()
        result = service.generate_my_feature(
            context='test context',
            user_input='test input',
        )

    assert result['field1'] == 'test'
    assert 'item1' in result['field2']
```
