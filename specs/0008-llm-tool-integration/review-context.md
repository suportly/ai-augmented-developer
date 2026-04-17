# Code Review Context: aiadev LLM Tool Integration

## What Was Built

The 8 pipeline skills (`specify`, `clarify`, `plan`, `tasks`, `implement`, `analyze`, `checklist`, `constitution`) are now exposed as LLM-callable tools via two transports sharing a common core: an in-process Python library (`aiadev.tools`) and an MCP stdio server (`aiadev.mcp_server` via FastMCP). Both follow the **skill-as-prompt-loader** model — the handler validates inputs, computes the target path, and returns a structured `ToolPayload` containing the skill prompt + template + context. The caller LLM does the actual file creation. A transversal change introduces stable `cl-N` ids for `[NEEDS CLARIFICATION]` markers, with back-compat for legacy markers.

## Spec Reference

- Spec: `specs/0008-llm-tool-integration/spec.md`
- Plan: `specs/0008-llm-tool-integration/plan.md`
- Tasks: `specs/0008-llm-tool-integration/tasks.md`
- Contracts: `specs/0008-llm-tool-integration/contracts/`

## Changed Files

46 files changed, +3644 / -9 lines across 27 commits.

New modules:
- `src/aiadev/_tooling/` (6 files) — shared core
- `src/aiadev/tools/` (2 files) — Python lib
- `src/aiadev/mcp_server/` (3 files) — MCP server
- `schemas/vendor/` (3 files) — vendored MCP schemas
- `tests/` (16 new test files, 1 modified)

Modified:
- `templates/spec-template.md` — marker example → `cl-N`
- `skills/specify/SKILL.md` — step 4 → `cl-N` stamping
- `skills/clarify/SKILL.md` — step 3 → `answers=[{id, answer}]`
- `scripts/validate_skills.py` — `check_markers()` with legacy tolerance
- `pyproject.toml` — `[mcp]` extra, `pytest-asyncio`, `aiadev-mcp-server` script
- `CHANGELOG.md`, `CREDITS.md`, `README.md`

## Key Decisions Made

- **ADR 1:** New MCP server lives at `aiadev.mcp_server` (not `aiadev.mcp`) to avoid name collision with existing `mcp.py` (mcps.yaml loader).
- **ADR 2:** `mcp` SDK as optional dependency `[mcp]` — core CLI doesn't need it.
- **ADR 3:** Shared core in `aiadev._tooling` — underscore prefix signals internal; both transports consume it.
- **ADR 4:** Marker ids (`cl-N`) stamped at creation time, not at read time, for stability.
- **ADR 5:** MCP `prompts/get` as primary primitive (judgment call, not obvious); `tools/call` as fallback. Both return identical `ToolPayload`.
- **Deviation from plan:** T021 (`transport.py` custom provider) replaced by direct FastMCP usage — Article III, wrapper was YAGNI.

## Areas Needing Attention

- **Security:** `workspace.assert_within()` uses `Path.is_relative_to()` — reviewer should verify the 3 traversal vectors (dotdot, symlink, absolute-outside) are covered.
- **`_tooling/payload.py`:** orchestrates 4 modules — most complex file; verify schema validation actually runs.
- **MCP server handler closures:** `_make_handler()` creates closures in a loop; verify `skill_name` capture is correct (not a late-binding bug).
- **E2E tests:** rely on a deterministic fake LLM that doesn't validate content quality — this is a documented limitation, not a bug.

## Test Coverage

- **Full suite:** 416 tests, all passing (`pytest -ra`)
- **Skills validation:** `python3 scripts/validate_skills.py` — all OK
- **New test files:** 16 covering workspace, markers, skill_loader, payload, telemetry, tools lib, MCP server, E2E specify, E2E pipeline, fake LLM, vendored schemas, packaging, framework artifacts
- **Manual verification:** `aiadev-mcp-server` starts and responds to initialize request; `from aiadev.tools import specify; specify(...)` returns valid ToolPayload in Python REPL
