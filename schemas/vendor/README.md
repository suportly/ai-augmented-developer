# Vendored MCP Schemas

JSON Schemas extracted from the `mcp` Python SDK pydantic models.

- `mcp-tools-list.schema.json` — `ListToolsResult.model_json_schema()` (MCP `tools/list` response)
- `mcp-prompts-list.schema.json` — `ListPromptsResult.model_json_schema()` (MCP `prompts/list` response)

**Source:** `mcp` PyPI package v1.26.0 (Anthropic, MIT license).
**Extracted:** 2026-04-16.
**Purpose:** offline validation of aiadev's `tools/list` and `prompts/list` responses in CI (Story 4 sc2).
