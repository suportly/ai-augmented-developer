"""Tests for :mod:`aiadev.platforms.gemini`."""
from __future__ import annotations

import pathlib

import pytest

from aiadev.platforms import gemini

FIXTURES = pathlib.Path(__file__).parent / "fixtures" / "mini-preset"


class TestResolveTarget:
    def test_agent_file_is_agents_md(self, tmp_path: pathlib.Path) -> None:
        # Spec 0016 Story 3 / ADR-5: AGENTS.md is the canonical agent
        # file for every platform, including Gemini; GEMINI.md is a
        # thin wrapper (see TestWrapper below).
        assert gemini.resolve_target("agent_file", "", tmp_path) == tmp_path / "AGENTS.md"

    def test_constitution(self, tmp_path: pathlib.Path) -> None:
        assert gemini.resolve_target("constitution", "", tmp_path) == tmp_path / "constitution.md"

    def test_skill(self, tmp_path: pathlib.Path) -> None:
        assert gemini.resolve_target("skill", "hello", tmp_path) == (
            tmp_path / ".gemini" / "skills" / "hello" / "SKILL.md"
        )

    def test_skill_without_name_rejected(self, tmp_path: pathlib.Path) -> None:
        with pytest.raises(ValueError, match="non-empty name"):
            gemini.resolve_target("skill", "", tmp_path)

    def test_unknown_role_rejected(self, tmp_path: pathlib.Path) -> None:
        with pytest.raises(ValueError, match="unknown artifact role"):
            gemini.resolve_target("mystery", "x", tmp_path)  # type: ignore[arg-type]


class TestUserScope:
    def test_supports_only_skills(self) -> None:
        assert gemini.user_scope_supported("skill") is True
        assert gemini.user_scope_supported("agent_file") is False

    def test_user_scope_skill_path(self, tmp_path: pathlib.Path) -> None:
        target = gemini.resolve_target("skill", "hello", tmp_path, scope="user")
        assert target == tmp_path / ".gemini" / "skills" / "hello" / "SKILL.md"

    def test_user_scope_rejects_agent_file(self, tmp_path: pathlib.Path) -> None:
        with pytest.raises(ValueError, match="not installable at user scope"):
            gemini.resolve_target("agent_file", "", tmp_path, scope="user")


class TestWrapper:
    """Spec 0016 Story 3 / ADR-5: GEMINI.md is a thin wrapper pointing
    at the canonical AGENTS.md the engine writes."""

    def test_wrapper_target_is_gemini_md_for_agent_file(
        self, tmp_path: pathlib.Path
    ) -> None:
        assert gemini.wrapper_target("agent_file", "", tmp_path) == tmp_path / "GEMINI.md"

    def test_wrapper_target_is_none_for_other_roles(self, tmp_path: pathlib.Path) -> None:
        assert gemini.wrapper_target("constitution", "", tmp_path) is None
        assert gemini.wrapper_target("skill", "hello", tmp_path) is None

    def test_wrapper_target_is_none_at_user_scope(self, tmp_path: pathlib.Path) -> None:
        assert gemini.wrapper_target("agent_file", "", tmp_path, scope="user") is None

    def test_render_wrapper_points_at_agents_md(self) -> None:
        text = gemini.render_wrapper("agent_file", "AGENTS.md")
        assert text is not None
        assert "AGENTS.md" in text
        lines = [line for line in text.splitlines() if line.strip()]
        assert len(lines) <= 5

    def test_render_wrapper_is_none_for_other_roles(self) -> None:
        assert gemini.render_wrapper("constitution", "AGENTS.md") is None


class TestIterPresetArtifacts:
    def test_fixture(self) -> None:
        artifacts = list(gemini.iter_preset_artifacts(FIXTURES))
        assert artifacts[0][0] == "agent_file"
        assert artifacts[1] == (
            "skill",
            "hello-world",
            FIXTURES / "skills" / "hello-world" / "SKILL.md",
        )

    def test_empty(self, tmp_path: pathlib.Path) -> None:
        assert list(gemini.iter_preset_artifacts(tmp_path)) == []

    def test_constitution_included(self, tmp_path: pathlib.Path) -> None:
        (tmp_path / "CLAUDE.md").write_text("agent", encoding="utf-8")
        (tmp_path / "constitution.md").write_text("const", encoding="utf-8")
        roles = [r for (r, _n, _p) in gemini.iter_preset_artifacts(tmp_path)]
        assert roles == ["agent_file", "constitution"]

    def test_skills_sorted(self, tmp_path: pathlib.Path) -> None:
        for name in ("charlie", "alpha", "bravo"):
            d = tmp_path / "skills" / name
            d.mkdir(parents=True)
            (d / "SKILL.md").write_text(f"---\nname: {name}\n---\n", encoding="utf-8")
        names = [n for (_r, n, _p) in gemini.iter_preset_artifacts(tmp_path)]
        assert names == ["alpha", "bravo", "charlie"]

    def test_skips_non_dir(self, tmp_path: pathlib.Path) -> None:
        (tmp_path / "skills").mkdir()
        (tmp_path / "skills" / "stray.md").write_text("nope", encoding="utf-8")
        assert list(gemini.iter_preset_artifacts(tmp_path)) == []

    def test_skips_dir_without_skill_md(self, tmp_path: pathlib.Path) -> None:
        d = tmp_path / "skills" / "nope"
        d.mkdir(parents=True)
        (d / "README.md").write_text("doc", encoding="utf-8")
        assert list(gemini.iter_preset_artifacts(tmp_path)) == []
