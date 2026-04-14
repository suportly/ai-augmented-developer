"""Tests for :mod:`aiadev.platforms.opencode`."""
from __future__ import annotations

import pathlib

import pytest

from aiadev.platforms import opencode

FIXTURES = pathlib.Path(__file__).parent / "fixtures" / "mini-preset"


class TestResolveTarget:
    def test_agent_file(self, tmp_path: pathlib.Path) -> None:
        assert opencode.resolve_target("agent_file", "", tmp_path) == tmp_path / "AGENTS.md"

    def test_constitution(self, tmp_path: pathlib.Path) -> None:
        assert opencode.resolve_target("constitution", "", tmp_path) == tmp_path / "constitution.md"

    def test_skill(self, tmp_path: pathlib.Path) -> None:
        assert opencode.resolve_target("skill", "hello", tmp_path) == (
            tmp_path / ".opencode" / "skills" / "hello" / "SKILL.md"
        )

    def test_skill_without_name_rejected(self, tmp_path: pathlib.Path) -> None:
        with pytest.raises(ValueError, match="non-empty name"):
            opencode.resolve_target("skill", "", tmp_path)

    def test_unknown_role_rejected(self, tmp_path: pathlib.Path) -> None:
        with pytest.raises(ValueError, match="unknown artifact role"):
            opencode.resolve_target("mystery", "x", tmp_path)  # type: ignore[arg-type]


class TestIterPresetArtifacts:
    def test_fixture(self) -> None:
        artifacts = list(opencode.iter_preset_artifacts(FIXTURES))
        assert artifacts[0][0] == "agent_file"
        assert artifacts[1] == (
            "skill",
            "hello-world",
            FIXTURES / "skills" / "hello-world" / "SKILL.md",
        )

    def test_empty(self, tmp_path: pathlib.Path) -> None:
        assert list(opencode.iter_preset_artifacts(tmp_path)) == []

    def test_constitution_included(self, tmp_path: pathlib.Path) -> None:
        (tmp_path / "CLAUDE.md").write_text("agent", encoding="utf-8")
        (tmp_path / "constitution.md").write_text("const", encoding="utf-8")
        roles = [r for (r, _n, _p) in opencode.iter_preset_artifacts(tmp_path)]
        assert roles == ["agent_file", "constitution"]

    def test_skills_sorted(self, tmp_path: pathlib.Path) -> None:
        for name in ("charlie", "alpha", "bravo"):
            d = tmp_path / "skills" / name
            d.mkdir(parents=True)
            (d / "SKILL.md").write_text(f"---\nname: {name}\n---\n", encoding="utf-8")
        names = [n for (_r, n, _p) in opencode.iter_preset_artifacts(tmp_path)]
        assert names == ["alpha", "bravo", "charlie"]

    def test_skips_non_dir(self, tmp_path: pathlib.Path) -> None:
        (tmp_path / "skills").mkdir()
        (tmp_path / "skills" / "stray.md").write_text("nope", encoding="utf-8")
        assert list(opencode.iter_preset_artifacts(tmp_path)) == []

    def test_skips_dir_without_skill_md(self, tmp_path: pathlib.Path) -> None:
        d = tmp_path / "skills" / "nope"
        d.mkdir(parents=True)
        (d / "README.md").write_text("doc", encoding="utf-8")
        assert list(opencode.iter_preset_artifacts(tmp_path)) == []
