"""Tests for :mod:`aiadev.platforms.claude_code`."""
from __future__ import annotations

import pathlib

import pytest

from aiadev.platforms import claude_code as cc

FIXTURES = pathlib.Path(__file__).parent / "fixtures" / "mini-preset"


class TestResolveTarget:
    def test_agent_file_lands_at_project_root(self, tmp_path: pathlib.Path) -> None:
        # Spec 0016 Story 3 / ADR-5: AGENTS.md is the canonical agent
        # file; CLAUDE.md is a thin wrapper (see TestWrapper below).
        assert cc.resolve_target("agent_file", "", tmp_path) == tmp_path / "AGENTS.md"

    def test_constitution_lands_at_project_root(self, tmp_path: pathlib.Path) -> None:
        assert cc.resolve_target("constitution", "", tmp_path) == tmp_path / "constitution.md"

    def test_skill_lands_under_dot_claude(self, tmp_path: pathlib.Path) -> None:
        target = cc.resolve_target("skill", "django-patterns", tmp_path)
        assert target == tmp_path / ".claude" / "skills" / "django-patterns" / "SKILL.md"

    def test_skill_without_name_is_rejected(self, tmp_path: pathlib.Path) -> None:
        with pytest.raises(ValueError, match="non-empty name"):
            cc.resolve_target("skill", "", tmp_path)

    def test_unknown_role_is_rejected(self, tmp_path: pathlib.Path) -> None:
        with pytest.raises(ValueError, match="unknown artifact role"):
            cc.resolve_target("mystery", "x", tmp_path)  # type: ignore[arg-type]


class TestUserScope:
    def test_user_scope_supports_only_skills(self) -> None:
        assert cc.user_scope_supported("skill") is True
        assert cc.user_scope_supported("agent_file") is False
        assert cc.user_scope_supported("constitution") is False

    def test_user_scope_skill_path_under_home(self, tmp_path: pathlib.Path) -> None:
        target = cc.resolve_target("skill", "hello", tmp_path, scope="user")
        assert target == tmp_path / ".claude" / "skills" / "hello" / "SKILL.md"

    def test_user_scope_rejects_agent_file(self, tmp_path: pathlib.Path) -> None:
        with pytest.raises(ValueError, match="not installable at user scope"):
            cc.resolve_target("agent_file", "", tmp_path, scope="user")

    def test_user_scope_rejects_constitution(self, tmp_path: pathlib.Path) -> None:
        with pytest.raises(ValueError, match="not installable at user scope"):
            cc.resolve_target("constitution", "", tmp_path, scope="user")


class TestWrapper:
    """Spec 0016 Story 3 / ADR-5: CLAUDE.md is a thin wrapper pointing
    at the canonical AGENTS.md the engine writes."""

    def test_wrapper_target_is_claude_md_for_agent_file(
        self, tmp_path: pathlib.Path
    ) -> None:
        assert cc.wrapper_target("agent_file", "", tmp_path) == tmp_path / "CLAUDE.md"

    def test_wrapper_target_is_none_for_other_roles(self, tmp_path: pathlib.Path) -> None:
        assert cc.wrapper_target("constitution", "", tmp_path) is None
        assert cc.wrapper_target("skill", "hello", tmp_path) is None

    def test_wrapper_target_is_none_at_user_scope(self, tmp_path: pathlib.Path) -> None:
        assert cc.wrapper_target("agent_file", "", tmp_path, scope="user") is None

    def test_render_wrapper_points_at_agents_md(self) -> None:
        text = cc.render_wrapper("agent_file", "AGENTS.md")
        assert text is not None
        assert "AGENTS.md" in text
        lines = [line for line in text.splitlines() if line.strip()]
        assert len(lines) <= 5

    def test_render_wrapper_is_none_for_other_roles(self) -> None:
        assert cc.render_wrapper("constitution", "AGENTS.md") is None


class TestIterPresetArtifacts:
    def test_yields_agent_file_and_skills_from_fixture(self) -> None:
        artifacts = list(cc.iter_preset_artifacts(FIXTURES))
        # agent_file first, then sorted skills.
        assert artifacts[0] == ("agent_file", "", FIXTURES / "CLAUDE.md")
        assert artifacts[1] == (
            "skill",
            "hello-world",
            FIXTURES / "skills" / "hello-world" / "SKILL.md",
        )

    def test_skips_missing_agent_file(self, tmp_path: pathlib.Path) -> None:
        # Preset with only a skill, no CLAUDE.md.
        skill_dir = tmp_path / "skills" / "only"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("---\nname: only\n---\n", encoding="utf-8")
        roles = [r for (r, _n, _p) in cc.iter_preset_artifacts(tmp_path)]
        assert roles == ["skill"]

    def test_includes_constitution_when_present(self, tmp_path: pathlib.Path) -> None:
        (tmp_path / "CLAUDE.md").write_text("agent", encoding="utf-8")
        (tmp_path / "constitution.md").write_text("const", encoding="utf-8")
        roles = [r for (r, _n, _p) in cc.iter_preset_artifacts(tmp_path)]
        assert roles == ["agent_file", "constitution"]

    def test_skips_skill_directory_without_skill_md(self, tmp_path: pathlib.Path) -> None:
        # A stray directory under skills/ without the SKILL.md must not
        # be yielded as an artifact.
        stray = tmp_path / "skills" / "notes"
        stray.mkdir(parents=True)
        (stray / "README.md").write_text("not a skill", encoding="utf-8")
        artifacts = list(cc.iter_preset_artifacts(tmp_path))
        assert artifacts == []

    def test_skips_files_directly_under_skills(self, tmp_path: pathlib.Path) -> None:
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        (skills_dir / "not-a-dir.md").write_text("stray", encoding="utf-8")
        artifacts = list(cc.iter_preset_artifacts(tmp_path))
        assert artifacts == []

    def test_empty_preset_root_yields_nothing(self, tmp_path: pathlib.Path) -> None:
        assert list(cc.iter_preset_artifacts(tmp_path)) == []

    def test_skills_are_sorted_alphabetically(self, tmp_path: pathlib.Path) -> None:
        for name in ("bravo", "alpha", "charlie"):
            skill_dir = tmp_path / "skills" / name
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                f"---\nname: {name}\n---\n", encoding="utf-8"
            )
        names = [n for (_r, n, _p) in cc.iter_preset_artifacts(tmp_path)]
        assert names == ["alpha", "bravo", "charlie"]
