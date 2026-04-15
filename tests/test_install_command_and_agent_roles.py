"""Tests for the new ``command`` and ``agent`` roles across handlers.

These roles were introduced when the installer started shipping the
framework-generic pipeline (slash commands + reviewer agents) alongside
every preset. This file exercises the per-platform layout contract so
that any regression in one handler is caught independently of the
others.
"""
from __future__ import annotations

import pathlib

import pytest

from aiadev.platforms import claude_code as cc
from aiadev.platforms import codex, cursor, gemini, opencode


class TestResolveTargetCommand:
    @pytest.mark.parametrize(
        "handler, expected_suffix",
        [
            (cc, pathlib.Path(".claude") / "commands" / "aiadev" / "specify.md"),
            (cursor, pathlib.Path(".cursor") / "commands" / "aiadev" / "specify.md"),
            (codex, pathlib.Path(".codex") / "commands" / "aiadev" / "specify.md"),
            (opencode, pathlib.Path(".opencode") / "commands" / "aiadev" / "specify.md"),
            (gemini, pathlib.Path(".gemini") / "commands" / "aiadev" / "specify.toml"),
        ],
    )
    def test_command_lands_in_platform_dir(
        self, tmp_path: pathlib.Path, handler, expected_suffix: pathlib.Path
    ) -> None:
        assert handler.resolve_target("command", "specify", tmp_path) == tmp_path / expected_suffix


class TestResolveTargetAgent:
    @pytest.mark.parametrize(
        "handler, expected_suffix",
        [
            (cc, pathlib.Path(".claude") / "agents" / "code-reviewer.md"),
            (cursor, pathlib.Path(".cursor") / "agents" / "code-reviewer.md"),
            (codex, pathlib.Path(".codex") / "agents" / "code-reviewer.md"),
            (opencode, pathlib.Path(".opencode") / "agents" / "code-reviewer.md"),
            (gemini, pathlib.Path(".gemini") / "agents" / "code-reviewer.md"),
        ],
    )
    def test_agent_lands_in_platform_dir(
        self, tmp_path: pathlib.Path, handler, expected_suffix: pathlib.Path
    ) -> None:
        assert handler.resolve_target("agent", "code-reviewer", tmp_path) == tmp_path / expected_suffix


class TestResolveTargetRejectsEmptyName:
    @pytest.mark.parametrize("handler", [cc, cursor, codex, opencode, gemini])
    @pytest.mark.parametrize("role", ["command", "agent", "rule"])
    def test_empty_name_raises(self, tmp_path: pathlib.Path, handler, role: str) -> None:
        with pytest.raises(ValueError, match="non-empty name"):
            handler.resolve_target(role, "", tmp_path)


class TestResolveTargetRule:
    @pytest.mark.parametrize(
        "handler, expected_suffix",
        [
            (cc, pathlib.Path(".claude") / "rules" / "code-style.md"),
            (cursor, pathlib.Path(".cursor") / "rules" / "code-style.mdc"),
            (codex, pathlib.Path(".codex") / "rules" / "code-style.md"),
            (opencode, pathlib.Path(".opencode") / "rules" / "code-style.md"),
            (gemini, pathlib.Path(".gemini") / "rules" / "code-style.md"),
        ],
    )
    def test_rule_lands_in_platform_dir(
        self, tmp_path: pathlib.Path, handler, expected_suffix: pathlib.Path
    ) -> None:
        assert handler.resolve_target("rule", "code-style", tmp_path) == tmp_path / expected_suffix


class TestUserScopeSupportsNewRoles:
    @pytest.mark.parametrize("handler", [cc, cursor, codex, opencode, gemini])
    @pytest.mark.parametrize("role", ["command", "agent", "skill", "rule"])
    def test_user_scope_supports_shareable_roles(self, handler, role: str) -> None:
        assert handler.user_scope_supported(role) is True


class TestIterPresetArtifactsIncludesCommandsAndAgents:
    def test_claude_code_yields_commands_and_agents_from_preset(
        self, tmp_path: pathlib.Path
    ) -> None:
        (tmp_path / "CLAUDE.md").write_text("agent", encoding="utf-8")
        (tmp_path / "commands").mkdir()
        (tmp_path / "commands" / "foo.md").write_text("---\ndescription: f\n---\n", encoding="utf-8")
        (tmp_path / "agents").mkdir()
        (tmp_path / "agents" / "bar.md").write_text("---\nname: bar\n---\n", encoding="utf-8")
        artifacts = list(cc.iter_preset_artifacts(tmp_path))
        roles = [(r, n) for (r, n, _p) in artifacts]
        assert ("command", "foo") in roles
        assert ("agent", "bar") in roles

    @pytest.mark.parametrize("handler", [cursor, codex, opencode, gemini])
    def test_other_handlers_also_yield_new_roles(
        self, tmp_path: pathlib.Path, handler
    ) -> None:
        (tmp_path / "commands").mkdir()
        (tmp_path / "commands" / "baz.md").write_text("---\ndescription: x\n---\n", encoding="utf-8")
        (tmp_path / "agents").mkdir()
        (tmp_path / "agents" / "qux.md").write_text("---\nname: qux\n---\n", encoding="utf-8")
        roles = [(r, n) for (r, n, _p) in handler.iter_preset_artifacts(tmp_path)]
        assert ("command", "baz") in roles
        assert ("agent", "qux") in roles


class TestGeminiCommandConversion:
    def test_render_target_converts_markdown_command_to_toml(self) -> None:
        markdown = (
            "---\n"
            "description: Short spec wrapper.\n"
            "allowed-tools: Read, Write\n"
            "---\n"
            "Invoke the specify skill for demand: $ARGUMENTS\n"
        )
        out = gemini.render_target("command", "specify", markdown)
        assert 'description = "Short spec wrapper."' in out
        assert 'prompt = """' in out
        assert "{{args}}" in out
        assert "$ARGUMENTS" not in out

    def test_render_target_pass_through_for_agent(self) -> None:
        body = "---\nname: code-reviewer\n---\nAgent body"
        assert gemini.render_target("agent", "code-reviewer", body) == body

    def test_render_target_pass_through_for_skill(self) -> None:
        body = "---\nname: specify\n---\n{{BRANCH}} should stay."
        assert gemini.render_target("skill", "specify", body) == body

    def test_converter_handles_missing_description(self) -> None:
        markdown = "---\nallowed-tools: Read\n---\nBody only"
        out = gemini.render_target("command", "noname", markdown)
        assert "description" not in out
        assert 'prompt = """' in out

    def test_converter_escapes_triple_quotes_in_body(self) -> None:
        markdown = '---\ndescription: d\n---\nBody with """ triple.'
        out = gemini.render_target("command", "q", markdown)
        # The dangerous """ sequence must be neutralised.
        assert '"""\nBody with ""\\" triple.\n"""' in out
