"""Tests for the ``mcp`` install role.

Covers both the canonical loader (``aiadev.mcp``) and each platform
handler's ``resolve_target`` + ``render_target`` contract for the new
role. End-to-end install coverage lives in ``test_install_e2e.py``.
"""
from __future__ import annotations

import json
import pathlib
import textwrap

import pytest

from aiadev import mcp
from aiadev.platforms import claude_code as cc
from aiadev.platforms import codex, cursor, gemini, opencode


_SAMPLE = textwrap.dedent(
    """
    servers:
      context7:
        command: npx
        args: ["-y", "@upstash/context7-mcp"]
        env:
          CONTEXT7_API_KEY: "${CONTEXT7_API_KEY}"
      playwright:
        command: npx
        args: ["@playwright/mcp@latest"]
    """
).strip()


class TestLoadServersFromText:
    def test_parses_canonical_form(self) -> None:
        servers = mcp.load_servers_from_text(_SAMPLE)
        assert [s.name for s in servers] == ["context7", "playwright"]
        assert servers[0].command == "npx"
        assert servers[0].args == ("-y", "@upstash/context7-mcp")
        assert servers[0].env == {"CONTEXT7_API_KEY": "${CONTEXT7_API_KEY}"}
        assert servers[1].env == {}

    def test_empty_servers_map(self) -> None:
        assert mcp.load_servers_from_text("servers: {}") == []

    def test_missing_command_rejected(self) -> None:
        with pytest.raises(ValueError, match="non-empty 'command'"):
            mcp.load_servers_from_text("servers:\n  broken:\n    args: ['x']\n")

    def test_non_string_args_rejected(self) -> None:
        with pytest.raises(ValueError, match="args must be a list of strings"):
            mcp.load_servers_from_text(
                "servers:\n  broken:\n    command: x\n    args: [1, 2]\n"
            )


class TestResolveTargetMcp:
    @pytest.mark.parametrize(
        "handler, expected_suffix",
        [
            (cc, pathlib.Path(".mcp.json")),
            (cursor, pathlib.Path(".cursor") / "mcp.json"),
            (codex, pathlib.Path(".codex") / "config.toml"),
            (gemini, pathlib.Path(".gemini") / "settings.json"),
            (opencode, pathlib.Path("opencode.json")),
        ],
    )
    def test_mcp_lands_in_platform_file(
        self, tmp_path: pathlib.Path, handler, expected_suffix: pathlib.Path
    ) -> None:
        assert (
            handler.resolve_target("mcp", "servers", tmp_path)
            == tmp_path / expected_suffix
        )

    @pytest.mark.parametrize("handler", [cc, cursor, codex, opencode, gemini])
    def test_empty_name_raises(self, tmp_path: pathlib.Path, handler) -> None:
        with pytest.raises(ValueError, match="non-empty name"):
            handler.resolve_target("mcp", "", tmp_path)


class TestUserScopeSupportsMcp:
    @pytest.mark.parametrize("handler", [cc, cursor, codex, opencode, gemini])
    def test_mcp_is_user_scope_installable(self, handler) -> None:
        assert handler.user_scope_supported("mcp") is True


class TestRenderTargetMcpJson:
    @pytest.mark.parametrize("handler", [cc, cursor, gemini])
    def test_json_platforms_emit_mcpServers_key(self, handler) -> None:
        rendered = handler.render_target("mcp", "servers", _SAMPLE)
        payload = json.loads(rendered)
        assert "mcpServers" in payload
        assert set(payload["mcpServers"]) == {"context7", "playwright"}
        ctx = payload["mcpServers"]["context7"]
        assert ctx == {
            "command": "npx",
            "args": ["-y", "@upstash/context7-mcp"],
            "env": {"CONTEXT7_API_KEY": "${CONTEXT7_API_KEY}"},
        }
        pw = payload["mcpServers"]["playwright"]
        assert pw == {"command": "npx", "args": ["@playwright/mcp@latest"]}

    def test_json_platforms_on_empty_servers(self) -> None:
        rendered = cc.render_target("mcp", "servers", "servers: {}")
        assert json.loads(rendered) == {"mcpServers": {}}


class TestRenderTargetMcpOpenCode:
    def test_opencode_uses_local_type_and_array_command(self) -> None:
        rendered = opencode.render_target("mcp", "servers", _SAMPLE)
        payload = json.loads(rendered)
        assert payload["$schema"] == "https://opencode.ai/config.json"
        ctx = payload["mcp"]["context7"]
        assert ctx == {
            "type": "local",
            "command": ["npx", "-y", "@upstash/context7-mcp"],
            "enabled": True,
            "environment": {"CONTEXT7_API_KEY": "${CONTEXT7_API_KEY}"},
        }
        pw = payload["mcp"]["playwright"]
        assert pw == {
            "type": "local",
            "command": ["npx", "@playwright/mcp@latest"],
            "enabled": True,
        }


class TestRenderTargetMcpCodex:
    def test_codex_emits_mcp_servers_tables(self) -> None:
        rendered = codex.render_target("mcp", "servers", _SAMPLE)
        assert "[mcp_servers.context7]" in rendered
        assert 'command = "npx"' in rendered
        assert 'args = ["-y", "@upstash/context7-mcp"]' in rendered
        assert 'env = { CONTEXT7_API_KEY = "${CONTEXT7_API_KEY}"' in rendered
        assert "[mcp_servers.playwright]" in rendered

    def test_codex_empty_emits_hint_comment(self) -> None:
        rendered = codex.render_target("mcp", "servers", "servers: {}")
        assert rendered.startswith("# Managed by aiadev.")


class TestRenderTargetPassthroughForOtherRoles:
    @pytest.mark.parametrize("handler", [cc, cursor, codex, opencode])
    def test_non_mcp_role_passes_through(self, handler) -> None:
        body = "---\nname: x\n---\nhi"
        assert handler.render_target("skill", "x", body) == body


class TestIterPresetYieldsMcp:
    @pytest.mark.parametrize("handler", [cc, cursor, codex, opencode, gemini])
    def test_handler_yields_mcp_when_preset_has_mcps_yaml(
        self, tmp_path: pathlib.Path, handler
    ) -> None:
        (tmp_path / "mcps.yaml").write_text("servers: {}\n", encoding="utf-8")
        roles = [(r, n) for (r, n, _p) in handler.iter_preset_artifacts(tmp_path)]
        assert ("mcp", mcp.MCP_ARTIFACT_NAME) in roles

    @pytest.mark.parametrize("handler", [cc, cursor, codex, opencode, gemini])
    def test_handler_skips_mcp_when_no_mcps_yaml(
        self, tmp_path: pathlib.Path, handler
    ) -> None:
        roles = [r for (r, _n, _p) in handler.iter_preset_artifacts(tmp_path)]
        assert "mcp" not in roles
