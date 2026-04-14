"""Tests for :mod:`aiadev.platforms.cursor`."""
from __future__ import annotations

import pathlib

import pytest

from aiadev.platforms import cursor

FIXTURES = pathlib.Path(__file__).parent / "fixtures" / "mini-preset"


class TestResolveTarget:
    def test_agent_file_at_project_root_as_agents_md(
        self, tmp_path: pathlib.Path
    ) -> None:
        assert cursor.resolve_target("agent_file", "", tmp_path) == tmp_path / "AGENTS.md"

    def test_constitution_shared_with_claude_code_at_root(
        self, tmp_path: pathlib.Path
    ) -> None:
        assert (
            cursor.resolve_target("constitution", "", tmp_path)
            == tmp_path / "constitution.md"
        )

    def test_skill_lands_under_dot_cursor(self, tmp_path: pathlib.Path) -> None:
        assert cursor.resolve_target("skill", "hello-world", tmp_path) == (
            tmp_path / ".cursor" / "skills" / "hello-world" / "SKILL.md"
        )

    def test_skill_without_name_rejected(self, tmp_path: pathlib.Path) -> None:
        with pytest.raises(ValueError, match="non-empty name"):
            cursor.resolve_target("skill", "", tmp_path)

    def test_unknown_role_rejected(self, tmp_path: pathlib.Path) -> None:
        with pytest.raises(ValueError, match="unknown artifact role"):
            cursor.resolve_target("mystery", "x", tmp_path)  # type: ignore[arg-type]


class TestUserScope:
    def test_supports_only_skills(self) -> None:
        assert cursor.user_scope_supported("skill") is True
        assert cursor.user_scope_supported("agent_file") is False

    def test_user_scope_skill_path(self, tmp_path: pathlib.Path) -> None:
        target = cursor.resolve_target("skill", "hello", tmp_path, scope="user")
        assert target == tmp_path / ".cursor" / "skills" / "hello" / "SKILL.md"

    def test_user_scope_rejects_agent_file(self, tmp_path: pathlib.Path) -> None:
        with pytest.raises(ValueError, match="not installable at user scope"):
            cursor.resolve_target("agent_file", "", tmp_path, scope="user")


class TestIterPresetArtifacts:
    def test_yields_agent_and_skill_from_fixture(self) -> None:
        artifacts = list(cursor.iter_preset_artifacts(FIXTURES))
        assert artifacts[0][0] == "agent_file"
        assert artifacts[1] == (
            "skill",
            "hello-world",
            FIXTURES / "skills" / "hello-world" / "SKILL.md",
        )

    def test_empty_preset_root(self, tmp_path: pathlib.Path) -> None:
        assert list(cursor.iter_preset_artifacts(tmp_path)) == []

    def test_skills_sorted(self, tmp_path: pathlib.Path) -> None:
        for name in ("charlie", "alpha", "bravo"):
            skill_dir = tmp_path / "skills" / name
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                f"---\nname: {name}\n---\n", encoding="utf-8"
            )
        names = [n for (_r, n, _p) in cursor.iter_preset_artifacts(tmp_path)]
        assert names == ["alpha", "bravo", "charlie"]

    def test_skips_non_dir_in_skills(self, tmp_path: pathlib.Path) -> None:
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        (skills_dir / "stray.md").write_text("nope", encoding="utf-8")
        assert list(cursor.iter_preset_artifacts(tmp_path)) == []

    def test_skips_dir_without_skill_md(self, tmp_path: pathlib.Path) -> None:
        skill_dir = tmp_path / "skills" / "nope"
        skill_dir.mkdir(parents=True)
        (skill_dir / "README.md").write_text("not a skill", encoding="utf-8")
        assert list(cursor.iter_preset_artifacts(tmp_path)) == []

    def test_includes_constitution_when_present(self, tmp_path: pathlib.Path) -> None:
        (tmp_path / "CLAUDE.md").write_text("agent", encoding="utf-8")
        (tmp_path / "constitution.md").write_text("const", encoding="utf-8")
        roles = [r for (r, _n, _p) in cursor.iter_preset_artifacts(tmp_path)]
        assert roles == ["agent_file", "constitution"]
