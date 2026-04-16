"""T010 — skill_loader loads SKILL.md + template + constitution excerpt."""
from __future__ import annotations

import pathlib

import pytest


class TestLoadSkill:
    def test_loads_specify_returns_triple(
        self, framework_root: pathlib.Path
    ) -> None:
        from aiadev._tooling.skill_loader import load_skill

        result = load_skill("specify", framework_root)
        assert "prompt" in result
        assert "template" in result
        assert "constitution_excerpt" in result
        assert "specify" in result["prompt"].lower()
        assert result["template"]["path"] == "templates/spec-template.md"
        assert len(result["template"]["content"]) > 0
        assert "Article" in result["constitution_excerpt"]

    def test_unknown_skill_raises_key_error(
        self, framework_root: pathlib.Path
    ) -> None:
        from aiadev._tooling.skill_loader import load_skill

        with pytest.raises(KeyError):
            load_skill("nonexistent-skill", framework_root)

    def test_loads_plan_with_spec_path(
        self, framework_root: pathlib.Path, tmp_path: pathlib.Path
    ) -> None:
        from aiadev._tooling import SpecNotFoundError
        from aiadev._tooling.skill_loader import load_skill

        with pytest.raises(SpecNotFoundError):
            load_skill("plan", framework_root, spec_path=tmp_path / "missing.md")

    def test_constitution_excerpt_includes_referenced_articles(
        self, framework_root: pathlib.Path
    ) -> None:
        from aiadev._tooling.skill_loader import load_skill

        result = load_skill("specify", framework_root)
        assert "Article I" in result["constitution_excerpt"]
