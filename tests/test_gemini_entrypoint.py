"""T053 (spec 0030 Story 6 sc3): help / using-ai-augmented-developer are gone.

GEMINI.md keeps only the Gemini tool reference (now under ``docs/``) and a
pointer to AGENTS.md; ``aiadev sync`` retires the old skills from projects
that installed them (intact copy removed, edited copy kept).
"""
from __future__ import annotations

import pathlib
import re
import shutil

import pytest

from click.testing import CliRunner

from aiadev.commands.sync import sync_command
from aiadev.install_engine import install
from aiadev.platforms import gemini

OLD_SKILLS = ("help", "using-ai-augmented-developer")


def test_gemini_md_imports_docs_tools_not_removed_skill(framework_root: pathlib.Path) -> None:
    text = (framework_root / "GEMINI.md").read_text(encoding="utf-8")
    assert "skills/using-ai-augmented-developer" not in text
    assert "@./docs/gemini-tools.md" in text
    assert "@./CLAUDE.md" in text
    assert (framework_root / "docs" / "gemini-tools.md").is_file()


def test_removed_skills_and_command_do_not_exist(framework_root: pathlib.Path) -> None:
    for name in OLD_SKILLS:
        assert not (framework_root / "skills" / name).exists()
    assert not (framework_root / "commands" / "using-ai-augmented-developer.md").exists()
    assert not (framework_root / "commands" / "help.md").exists()


@pytest.mark.parametrize("platform", ["claude-code", "gemini"])
def test_sync_removes_intact_old_skills_and_keeps_edited_one(
    framework_root: pathlib.Path, tmp_path: pathlib.Path, monkeypatch, platform: str
) -> None:
    framework = tmp_path / "framework"
    (framework / "templates").mkdir(parents=True)
    (framework / "constitution.md").write_text("# Constitution\n", encoding="utf-8")
    shutil.copytree(framework_root / "schemas", framework / "schemas")
    monkeypatch.setenv("AIADEV_ROOT", str(framework))
    preset = framework / "presets" / "oldp"
    for name in OLD_SKILLS:
        d = preset / "skills" / name
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: old\n---\n\nold\n", encoding="utf-8"
        )
    cmd = preset / "commands" / "using-ai-augmented-developer.md"
    cmd.parent.mkdir(parents=True)
    cmd.write_text("---\ndescription: old\n---\n\nold\n", encoding="utf-8")
    (preset / "preset.yaml").write_text("name: oldp\nversion: 1.0.0\n", encoding="utf-8")
    project = tmp_path / "project"
    install(
        preset, project, {}, force=True, framework_root=framework,
        platform=platform.replace("-", "_"),
    )
    base = project / (".claude" if platform == "claude-code" else ".gemini")
    skills = base / "skills"
    old_cmd = (
        base / "commands" / "aia" / "using-ai-augmented-developer.md"
        if platform == "claude-code"
        else base / "commands" / "aia" / "using-ai-augmented-developer.toml"
    )
    assert old_cmd.is_file()
    assert all((skills / n / "SKILL.md").is_file() for n in OLD_SKILLS)
    (skills / "help" / "SKILL.md").write_text("my own help\n", encoding="utf-8")

    shutil.rmtree(preset / "skills")
    shutil.rmtree(preset / "commands")  # the new framework no longer ships them
    result = CliRunner().invoke(
        sync_command, ["--project-root", str(project), "--platform", platform]
    )
    assert result.exit_code == 0, result.output
    assert not old_cmd.exists()
    assert not (skills / "using-ai-augmented-developer" / "SKILL.md").exists()
    assert (skills / "help" / "SKILL.md").read_text(encoding="utf-8") == "my own help\n"


def test_every_gemini_md_reference_exists(framework_root: pathlib.Path) -> None:
    text = (framework_root / "GEMINI.md").read_text(encoding="utf-8")
    refs = re.findall(r"\]\(\./([^)]+)\)", text) + re.findall(r"^@\./(\S+)", text, re.M)
    assert refs
    for ref in refs:
        assert (framework_root / ref).exists(), ref


def test_wrapper_carries_tool_mapping_in_parity_with_docs(framework_root: pathlib.Path) -> None:
    wrapper = gemini.render_wrapper("agent_file", "AGENTS.md")
    assert wrapper is not None and "read_file" in wrapper
    docs = (framework_root / "docs" / "gemini-tools.md").read_text(encoding="utf-8")
    table = docs.split("## No Subagent Support")[0]
    for tool in re.findall(r"\| [^|]+ \| `([a-z_]+)` \|", table):
        assert tool in wrapper, tool


def test_agent_file_template_keeps_meta_skill_rules(framework_root: pathlib.Path) -> None:
    text = (framework_root / "templates" / "agent-file-template.md").read_text(encoding="utf-8")
    assert "activate_skill" in text and "upstream" in text and "Priority" in text
