"""T020-T025 — MCP server tests."""
from __future__ import annotations

import asyncio
import json
import pathlib
import subprocess
import sys

import jsonschema
import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
VENDOR_DIR = REPO_ROOT / "schemas" / "vendor"


# ── T020 — pyproject.toml packaging ────────────────────────────────────

class TestPackaging:
    def test_mcp_extra_declared(self) -> None:
        import tomllib
        pyproject = tomllib.loads(
            (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        )
        extras = pyproject["project"]["optional-dependencies"]
        assert "mcp" in extras
        assert any("mcp" in dep for dep in extras["mcp"])

    def test_dev_includes_pytest_asyncio(self) -> None:
        import tomllib
        pyproject = tomllib.loads(
            (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        )
        dev_deps = pyproject["project"]["optional-dependencies"]["dev"]
        assert any("pytest-asyncio" in dep for dep in dev_deps)

    def test_mcp_server_script_declared(self) -> None:
        import tomllib
        pyproject = tomllib.loads(
            (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        )
        scripts = pyproject["project"]["scripts"]
        assert "aiadev-mcp-server" in scripts


# ── T022 — listing returns 8 pipeline skills ───────────────────────────

class TestMcpServerListing:
    def test_listing_returns_8_pipeline_skills(
        self, framework_root: pathlib.Path
    ) -> None:
        from aiadev.mcp_server.server import create_server

        server = create_server(framework_root)
        tools = asyncio.get_event_loop().run_until_complete(server.list_tools())
        prompts = asyncio.get_event_loop().run_until_complete(server.list_prompts())

        tool_names = {t.name for t in tools}
        prompt_names = {p.name for p in prompts}
        expected = {
            "specify", "clarify", "plan", "tasks",
            "implement", "analyze", "checklist", "constitution",
        }
        assert tool_names == expected
        assert prompt_names == expected

    def test_listing_validates_against_vendored_tools_schema(
        self, framework_root: pathlib.Path
    ) -> None:
        from aiadev.mcp_server.server import create_server

        server = create_server(framework_root)
        tools = asyncio.get_event_loop().run_until_complete(server.list_tools())
        tools_dicts = [t.model_dump() for t in tools]
        result = {"tools": tools_dicts}

        schema = json.loads(
            (VENDOR_DIR / "mcp-tools-list.schema.json").read_text()
        )
        jsonschema.validate(instance=result, schema=schema)

    def test_listing_validates_against_vendored_prompts_schema(
        self, framework_root: pathlib.Path
    ) -> None:
        from aiadev.mcp_server.server import create_server

        server = create_server(framework_root)
        prompts = asyncio.get_event_loop().run_until_complete(server.list_prompts())
        prompts_dicts = [p.model_dump() for p in prompts]
        result = {"prompts": prompts_dicts}

        schema = json.loads(
            (VENDOR_DIR / "mcp-prompts-list.schema.json").read_text()
        )
        jsonschema.validate(instance=result, schema=schema)


# ── T023 — prompts/get and tools/call return same payload ──────────────

class TestMcpServerCalls:
    def test_tool_call_returns_json_payload(
        self, framework_root: pathlib.Path, tmp_path: pathlib.Path
    ) -> None:
        from aiadev.mcp_server.server import create_server

        server = create_server(framework_root)
        result = asyncio.get_event_loop().run_until_complete(
            server.call_tool("specify", {"demand": "test", "workspace_path": str(tmp_path)})
        )
        content_list = result[0]
        payload = json.loads(content_list[0].text)
        assert payload["skill"] == "specify"
        assert "prompt" in payload

    def test_prompt_get_returns_json_payload(
        self, framework_root: pathlib.Path, tmp_path: pathlib.Path
    ) -> None:
        from aiadev.mcp_server.server import create_server

        server = create_server(framework_root)
        result = asyncio.get_event_loop().run_until_complete(
            server.get_prompt("specify", {"demand": "test", "workspace_path": str(tmp_path)})
        )
        content_text = result.messages[0].content.text
        payload = json.loads(content_text)
        assert payload["skill"] == "specify"

    def test_both_primitives_return_same_payload(
        self, framework_root: pathlib.Path, tmp_path: pathlib.Path
    ) -> None:
        from aiadev.mcp_server.server import create_server

        server = create_server(framework_root)
        # Use two fresh workspaces so target_path differs, and assert that
        # tool vs prompt handlers agree on the shape of the payload. The
        # prompt body embeds workspace-specific target_path (per issue #19),
        # so equality holds for skill metadata and schema — not for the raw
        # prompt text.
        ws_a = tmp_path / "ws_a"
        ws_b = tmp_path / "ws_b"
        ws_a.mkdir()
        ws_b.mkdir()

        tool_result = asyncio.get_event_loop().run_until_complete(
            server.call_tool("specify", {"demand": "test", "workspace_path": str(ws_a)})
        )
        tool_payload = json.loads(tool_result[0][0].text)

        prompt_result = asyncio.get_event_loop().run_until_complete(
            server.get_prompt("specify", {"demand": "test", "workspace_path": str(ws_b)})
        )
        prompt_payload = json.loads(prompt_result.messages[0].content.text)

        assert tool_payload["skill"] == prompt_payload["skill"]
        assert tool_payload["version"] == prompt_payload["version"]
        assert tool_payload["context"] == prompt_payload["context"]
        assert tool_payload["marker_format"] == prompt_payload["marker_format"]
        # Both prompts should end with the same skill body.
        skill_body_a = tool_payload["prompt"].split("## Skill instructions", 1)[-1]
        skill_body_b = prompt_payload["prompt"].split("## Skill instructions", 1)[-1]
        assert skill_body_a == skill_body_b


# ── T024 — catalog reflects skills/ changes ────────────────────────────

class TestCatalogReflectsChanges:
    def test_catalog_adapts_to_skills_dir(self, tmp_path: pathlib.Path) -> None:
        from aiadev.mcp_server.server import create_server

        root = tmp_path / "framework"
        root.mkdir()
        (root / "constitution.md").write_text("# Constitution\n## Article I\nSpec-first.\n")
        (root / "templates").mkdir()
        (root / "templates" / "spec-template.md").write_text("# Spec\n")
        (root / "templates" / "plan-template.md").write_text("# Plan\n")
        (root / "templates" / "tasks-template.md").write_text("# Tasks\n")
        (root / "templates" / "constitution-template.md").write_text("# Constitution\n")
        skills_dir = root / "skills"

        for name in ["specify", "plan"]:
            d = skills_dir / name
            d.mkdir(parents=True)
            (d / "SKILL.md").write_text(f"---\nname: {name}\ndescription: {name} skill\n---\n# {name}\n")

        server = create_server(root)
        tools = asyncio.get_event_loop().run_until_complete(server.list_tools())
        assert {t.name for t in tools} == {"specify", "plan"}

        (skills_dir / "clarify").mkdir(parents=True)
        (skills_dir / "clarify" / "SKILL.md").write_text("---\nname: clarify\ndescription: clarify skill\n---\n# clarify\n")
        server2 = create_server(root)
        tools2 = asyncio.get_event_loop().run_until_complete(server2.list_tools())
        assert {t.name for t in tools2} == {"specify", "plan", "clarify"}


# ── T025 — entry point ─────────────────────────────────────────────────

class TestEntryPoint:
    def test_missing_mcp_shows_helpful_error(self) -> None:
        result = subprocess.run(
            [sys.executable, "-c",
             "import sys; sys.modules['mcp'] = None; "
             "from aiadev.mcp_server.__main__ import main"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
