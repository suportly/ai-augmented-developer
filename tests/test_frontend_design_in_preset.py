"""T041 — frontend-design lives in the django-drf-react preset, not in the
framework root (spec 0030, Story 4 scenario 1, plan D11)."""
from __future__ import annotations

import importlib.util
import pathlib

import pytest
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
PRESET = ROOT / "presets" / "django-drf-react"


@pytest.fixture(scope="module")
def installer():
    spec = importlib.util.spec_from_file_location(
        "instruction_budget", ROOT / "scripts" / "instruction_budget.py"
    )
    module = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module.install_preset


@pytest.fixture(scope="module")
def django_project(installer, tmp_path_factory):
    dest = tmp_path_factory.mktemp("django")
    installer("django-drf-react", dest)
    return dest


@pytest.fixture(scope="module")
def lean_project(installer, tmp_path_factory):
    dest = tmp_path_factory.mktemp("lean")
    installer("lean", dest)
    return dest


def test_framework_root_no_longer_ships_frontend_design():
    assert not (ROOT / "skills" / "frontend-design").exists()
    assert not (ROOT / "commands" / "frontend-design.md").exists()


def test_preset_ships_skill_and_command():
    assert (PRESET / "skills" / "frontend-design" / "SKILL.md").is_file()
    assert (PRESET / "commands" / "frontend-design.md").is_file()


def test_preset_yaml_provides_skill_and_command():
    provides = yaml.safe_load((PRESET / "preset.yaml").read_text("utf-8"))["provides"]
    assert "skills/frontend-design" in provides["skills"]
    assert "commands/frontend-design.md" in provides["commands"]


def test_preset_claude_md_lists_skill():
    assert "`frontend-design`" in (PRESET / "CLAUDE.md").read_text("utf-8")


def test_lean_claude_md_does_not_list_skill():
    assert "frontend-design" not in (ROOT / "presets/lean/CLAUDE.md").read_text("utf-8")


def test_django_install_has_skill_and_command(django_project):
    assert (django_project / ".claude/skills/frontend-design/SKILL.md").is_file()
    assert (django_project / ".claude/commands/aia/frontend-design.md").is_file()


def test_lean_install_has_neither(lean_project):
    assert not (lean_project / ".claude/skills/frontend-design").exists()
    assert not (lean_project / ".claude/commands/aia/frontend-design.md").exists()
