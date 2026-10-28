"""T002 (spec 0032 Story 3 sc1): find-skills ships with every preset of the catalog."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from aiadev.commands.install import install_command

ROOT = Path(__file__).resolve().parent.parent
PRESETS = [p["name"] for p in json.loads((ROOT / "presets" / "catalog.json").read_text())["presets"]]


def _vars_for(preset: str) -> list[str]:
    """``NAME=x`` for every variable the preset requires and does not default."""
    manifest = yaml.safe_load((ROOT / "presets" / preset / "preset.yaml").read_text())
    names = {"PROJECT_NAME"}
    for var in manifest.get("variables") or []:
        if var.get("required") and "default" not in var:
            names.add(var["name"])
    return [f"{name}=x" for name in sorted(names)]


def test_catalog_lists_presets():
    assert PRESETS, "catalog is empty"


@pytest.mark.parametrize("preset", PRESETS)
def test_preset_installs_find_skills(tmp_path, preset):
    args = ["--project-root", str(tmp_path), "--preset", preset, "--non-interactive"]
    for assignment in _vars_for(preset):
        args += ["--vars", assignment]
    result = CliRunner().invoke(install_command, args, env={"AIADEV_ROOT": str(ROOT)})
    assert result.exit_code == 0, result.output
    installed = list((tmp_path / ".claude" / "skills").glob("find-skills/SKILL.md"))
    assert installed, f"{preset}: find-skills not installed under .claude/skills"
    body = installed[0].read_text(encoding="utf-8")
    assert body.startswith("---") and "name: find-skills" in body
