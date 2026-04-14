"""Tests for :mod:`aiadev.platforms.claude_code`."""
from __future__ import annotations

import pathlib

import pytest

from aiadev.platforms import claude_code as cc

FIXTURES = pathlib.Path(__file__).parent / "fixtures" / "mini-preset"


class TestResolveTarget:
    def test_agent_file_lands_at_project_root(self, tmp_path: pathlib.Path) -> None:
        assert cc.resolve_target("agent_file", "", tmp_path) == tmp_path / "CLAUDE.md"

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
