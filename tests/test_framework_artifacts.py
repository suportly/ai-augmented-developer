"""Tests for :mod:`aiadev.framework_artifacts`."""
from __future__ import annotations

import pathlib
import re

from aiadev.framework_artifacts import iter_framework_artifacts


def _write(path: pathlib.Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


class TestIterFrameworkArtifacts:
    def test_yields_command_markdown(self, tmp_path: pathlib.Path) -> None:
        _write(tmp_path / "commands" / "specify.md", "---\ndescription: x\n---\nhi")
        roles = [(r, n) for (r, n, _p) in iter_framework_artifacts(tmp_path)]
        assert roles == [("command", "specify")]

    def test_yields_agent_only_when_frontmatter_has_name(
        self, tmp_path: pathlib.Path
    ) -> None:
        _write(tmp_path / "agents" / "code-reviewer.md", "---\nname: code-reviewer\n---\nbody")
        _write(tmp_path / "agents" / "README.md", "# agents\n\nNot an agent.")
        roles = [(r, n) for (r, n, _p) in iter_framework_artifacts(tmp_path)]
        assert roles == [("agent", "code-reviewer")]

    def test_skips_agent_without_frontmatter(self, tmp_path: pathlib.Path) -> None:
        _write(tmp_path / "agents" / "stray.md", "no frontmatter here")
        assert list(iter_framework_artifacts(tmp_path)) == []

    def test_skill_directory_requires_skill_md(self, tmp_path: pathlib.Path) -> None:
        (tmp_path / "skills" / "specify").mkdir(parents=True)
        _write(tmp_path / "skills" / "plan" / "SKILL.md", "---\nname: plan\n---\nbody")
        names = [n for (r, n, _p) in iter_framework_artifacts(tmp_path) if r == "skill"]
        assert names == ["plan"]

    def test_order_is_role_then_alpha(self, tmp_path: pathlib.Path) -> None:
        _write(tmp_path / "rules" / "code-style.md", "---\ndescription: x\n---")
        _write(tmp_path / "commands" / "bravo.md", "---\ndescription: b\n---")
        _write(tmp_path / "commands" / "alpha.md", "---\ndescription: a\n---")
        _write(tmp_path / "agents" / "zeta.md", "---\nname: zeta\n---")
        _write(tmp_path / "skills" / "omega" / "SKILL.md", "---\nname: omega\n---")
        roles_names = [(r, n) for (r, n, _p) in iter_framework_artifacts(tmp_path)]
        assert roles_names == [
            ("rule", "code-style"),
            ("command", "alpha"),
            ("command", "bravo"),
            ("agent", "zeta"),
            ("skill", "omega"),
        ]

    def test_yields_rule_markdown(self, tmp_path: pathlib.Path) -> None:
        _write(tmp_path / "rules" / "testing.md", "---\ndescription: t\n---\nBody")
        roles = [(r, n) for (r, n, _p) in iter_framework_artifacts(tmp_path)]
        assert roles == [("rule", "testing")]

    def test_empty_root_yields_nothing(self, tmp_path: pathlib.Path) -> None:
        assert list(iter_framework_artifacts(tmp_path)) == []

    def test_ignores_non_markdown_in_commands(self, tmp_path: pathlib.Path) -> None:
        _write(tmp_path / "commands" / "notes.txt", "stray")
        _write(tmp_path / "commands" / "valid.md", "---\ndescription: x\n---")
        roles_names = [(r, n) for (r, n, _p) in iter_framework_artifacts(tmp_path)]
        assert roles_names == [("command", "valid")]


class TestSpecTemplateMarkerExample:
    """spec-template.md must illustrate the cl-N marker grammar (T004)."""

    _CL_N_MARKER = re.compile(r"\[NEEDS CLARIFICATION:cl-([1-9][0-9]*)\s+([^\]]+)\]")

    def test_template_contains_cl_n_marker_example(
        self, framework_root: pathlib.Path
    ) -> None:
        template = (framework_root / "templates" / "spec-template.md").read_text(
            encoding="utf-8"
        )
        match = self._CL_N_MARKER.search(template)
        assert match, (
            "templates/spec-template.md must contain at least one "
            "[NEEDS CLARIFICATION:cl-N <question>] example so that authors "
            "see the canonical format."
        )
