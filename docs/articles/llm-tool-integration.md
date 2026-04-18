# Using aiadev as LLM tools

This guide covers how to integrate the aiadev pipeline into your own LLM agents, CI pipelines, or autonomous development workflows.

## Architecture

aiadev follows the **skill-as-prompt-loader** model:

1. You call a tool (e.g., `specify(demand="...", workspace_path="...")`).
2. The tool returns a `ToolPayload` containing the skill prompt, template, constitution excerpt, and a computed `target_path`.
3. Your LLM (the caller) follows the prompt instructions using its own filesystem tools to create the artifact at `target_path`.

aiadev itself does **not** call any LLM — it only serves prompts and validates inputs.

## Quick start

### Python library

```bash
pip install aiadev
```

```python
from aiadev.tools import specify

payload = specify(
    demand="Add OAuth2 login with Google and GitHub",
    workspace_path="/path/to/your/project",
    language="en",
)

# payload is a dict with keys:
#   skill, version, prompt, context, target_path, marker_format,
#   existing_markers, needs_renumbering
#
# Feed payload["prompt"] + payload["context"] to your LLM
# and instruct it to write the artifact at payload["target_path"].
```

### MCP stdio server

```bash
pip install 'aiadev[mcp]'
```

Add to `.mcp.json` (or your MCP config):

```json
{
  "mcpServers": {
    "aiadev": {
      "command": "aiadev-mcp-server",
      "args": []
    }
  }
}
```

The server registers 8 prompts and 8 tools (one per pipeline skill):
`specify`, `clarify`, `plan`, `tasks`, `implement`, `analyze`, `checklist`, `constitution`.

## Smoke tests

### Python lib

```bash
python -c "
from aiadev.tools import specify
import json, tempfile, pathlib

with tempfile.TemporaryDirectory() as tmp:
    result = specify(demand='test', workspace_path=tmp)
    print(json.dumps({
        'skill': result['skill'],
        'target_path': result['target_path'],
        'marker_next_id': result['marker_format']['next_id'],
    }, indent=2))
"
```

Expected: JSON with `skill: "specify"`, a valid `target_path` inside the temp dir, and `marker_next_id: 1`.

### MCP server

```bash
# Start the server (it reads from stdin, writes to stdout)
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' | aiadev-mcp-server
```

Expected: JSON-RPC response with server capabilities including `prompts` and `tools`.

## Telemetry

Each invocation emits one JSON line to stderr:

```json
{"ts": "2026-04-16T23:42:02Z", "tool": "specify", "workspace_path": "/tmp/test", "latency_ms": 12, "status": "ok"}
```

Only metadata fields are logged — `demand`, payload content, and any user-provided text are **never** included (Article VI).

## Full pipeline example

```python
from aiadev.tools import specify, clarify, plan, tasks

# 1. specify
spec_payload = specify(demand="Add user profiles", workspace_path="/project")
# → your LLM creates spec.md at spec_payload["target_path"]

# 2. clarify (if markers exist)
if spec_payload["existing_markers"]:
    answers = [{"id": m["id"], "answer": "..."} for m in spec_payload["existing_markers"] if m["id"]]
    clarify_payload = clarify(spec_path="...", workspace_path="/project", answers=answers)

# 3. plan
plan_payload = plan(spec_path="...", workspace_path="/project")
# → your LLM creates plan.md

# 4. tasks
tasks_payload = tasks(plan_path="...", workspace_path="/project")
# → your LLM creates tasks.md

# 5. implement (optional — your LLM follows tasks.md on its own, or use:)
# implement_payload = implement(workspace_path="/project")
```

## Error handling

All tools raise typed exceptions with a stable `.code` attribute:

| Exception | Code | When |
|---|---|---|
| `InvalidWorkspaceError` | `invalid_workspace` | Path traversal, non-directory, or non-existent workspace |
| `ArtifactExistsError` | `artifact_exists` | Spec with same slug already has the target artifact |
| `SpecNotFoundError` | `spec_not_found` | `spec_path` points to a non-existent file |
| `SpecInvalidError` | `spec_invalid` | Spec is missing required sections |
| `UnknownMarkerIdError` | `unknown_marker_id` | `clarify` answer references a `cl-N` id not in the spec |

All exceptions are importable from `aiadev._tooling`.

## The payload contract

A caller that ships `payload["prompt"]` to an LLM (with filesystem tools
scoped to `workspace_path`) does not need to read `payload["context"]`
separately — `aiadev.tools` already inlines the fields below into the
prompt body. The context dict is preserved for callers that want direct
access (for example, a UI that renders the template before the user
approves a run).

| Payload field | Always embedded in `prompt` | Also exposed in `context`/top-level |
|---|---|---|
| `demand` (from `specify`)                   | Yes (issue #14) | no — call arg |
| `resolved_answers` (from `clarify`)          | Yes, in a batch block that overrides the interactive loop (issue #16) | no — call arg |
| `context.template.content`                  | Yes, as a fenced `markdown` block (issue #17) | `payload["context"]["template"]` |
| `context.constitution_excerpt`              | No — pass explicitly if relevant to your LLM prompt | `payload["context"]["constitution_excerpt"]` |
| `context.extra_files` (spec_path / plan_path) | No — pass explicitly; artifacts can be large | `payload["context"]["extra_files"]` |
| `target_path`                               | Yes, flagged as *authoritative* (issue #19) | `payload["target_path"]` |
| Single-artifact directive                   | Yes — the LLM is told not to write `contracts/`, `data-model.md`, etc. during this turn (issue #18) | — |
| English schema-header guard (non-English runs) | Yes, when `language != "en"` (issue #15) | — |

### Picking a slug

By default, `specify(demand=...)` slugifies the demand. If the demand is
short and your LLM is likely to invent a richer slug during writing, pass
`slug=` explicitly so `target_path` matches what the LLM will produce:

```python
payload = specify(
    demand="aplicativo",
    slug="aplicativo-fornecedor",   # wins over demand-derived slug
    workspace_path="/project",
    language="pt-BR",
)
```

If you cannot predict the slug, use the fallback helper after the LLM
writes:

```python
from aiadev.tools import locate_latest_artifact

written = locate_latest_artifact("/project", artifact="spec.md")
if written is None:
    raise RuntimeError("LLM did not produce spec.md")
```

### Minimum `max_tokens` per skill

Anthropic's default `max_tokens` (often 8192 in SDK examples) is too low
for the larger skills. A medium-sized `tasks.md` is ~40 KB; an LLM given
only 8k output tokens narrates its plan and runs out of budget before the
`Write` tool call lands.

Since v0.14.2 every payload carries a `recommended_max_tokens` field so
SDK callers can bump the Anthropic parameter without reading this table:

```python
payload = tasks(plan_path=..., workspace_path=...)
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=payload["recommended_max_tokens"],   # 32768 for tasks
    ...
)
```

| Skill | `recommended_max_tokens` | Typical artifact size |
|---|---|---|
| `specify`   | 16,384 | 8–12 KB spec |
| `clarify`   | 16,384 | edits in place |
| `plan`      | 32,768 | 15–25 KB |
| `tasks`     | 32,768 | 30–45 KB |
| `analyze`   | 8,192  | report |
| `checklist` | 8,192  | report |
| `implement` | 32,768 | code + tests per task |
| `constitution` | 16,384 | article text |

aiadev prompts also include an explicit "call `Write` in your first
response" directive so the model does not narrate before the tool call,
but the budget still needs to fit the artifact.

### Writing specs in non-English languages

When `language != "en"`, `spec-template.md` ships HTML comment anchors
above every required section:

```markdown
<!-- section: Problem -->
## Problema

...conteúdo em português...
```

`_validate_spec_sections` looks at the anchors first and the heading text
second, so the LLM is free to translate headings as long as it keeps the
anchors verbatim. If both are dropped, validation fails with the usual
`SpecInvalidError` listing the missing sections.
