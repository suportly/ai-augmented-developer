"""T017 — Smoke end-to-end across platforms for the 0016 feature set.

Spec: specs/0016-agent-skills-interop/spec.md
  Story 1 sc4 (skill frontmatter auto-migration on sync)
  Story 2 sc2 (``paths:`` rule transport per platform, no error on codex)
  Story 3 sc3 (AGENTS.md convergence, thin CLAUDE.md wrapper)
  Story 4 sc4 (manifests --check + repo-wide SKILL.md conformance)

This module does NOT re-test any single unit — each concern already has
a dedicated suite (tests/test_agents_md_canonical.py,
tests/test_rules_paths*.py, tests/test_sync_migrates_frontmatter.py,
tests/test_manifests_command.py, tests/test_skills_conformance.py). It
proves the pieces still compose when exercised together.

Multi-platform layout note: ``aiadev sync`` auto-detects the platform
from the single ``.claude``/``.cursor``/``.codex``/... marker directory
and errors out if more than one is present (``sync._detect_platform``),
so one physical project cannot host three platforms at once. This test
therefore installs the lean preset into three sibling tmp projects and
asserts cross-platform consistency, mirroring the pattern of
``TestCursorCodexShareAgentsMd`` in tests/test_agents_md_canonical.py.
"""
from __future__ import annotations

import json
import os
import pathlib
import re

import pytest
import yaml
from click.testing import CliRunner
from jsonschema import Draft202012Validator

from aiadev.commands.install import install_command
from aiadev.commands.sync import sync_command
from aiadev.validate import extract_frontmatter, iter_skill_files

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]


def _install(project: pathlib.Path, *, platform: str) -> object:
    runner = CliRunner()
    return runner.invoke(
        install_command,
        ["--project-root", str(project), "--preset", "lean",
         "--non-interactive", "--platform", platform,
         "--vars", "PROJECT_NAME=InteropSmoke"],
    )


def _sync(project: pathlib.Path, *, platform: str):
    runner = CliRunner()
    return runner.invoke(
        sync_command,
        ["--project-root", str(project), "--platform", platform],
    )


def _frontmatter(text: str) -> dict:
    _, _, rest = text.partition("---\n")
    fm_text, _, _ = rest.partition("\n---\n")
    parsed = yaml.safe_load(fm_text)
    assert isinstance(parsed, dict)
    return parsed


@pytest.fixture
def three_platform_projects(
    isolated_framework: pathlib.Path, tmp_path: pathlib.Path, monkeypatch
) -> dict[str, pathlib.Path]:
    """Sibling projects: claude-code, codex, cursor -- each lean-installed."""
    # isolated_framework (tests/conftest.py) does not copy the root-level
    # rules/ dir, but rules/ is a framework-generic artifact too (see
    # aiadev.framework_artifacts) and Story 2 sc2 needs rules/testing.md's
    # `paths:` key — so mirror it onto the isolated copy here.
    import shutil

    shutil.copytree(REPO_ROOT / "rules", isolated_framework / "rules")
    monkeypatch.setenv("AIADEV_ROOT", str(isolated_framework))
    projects = {}
    for platform in ("claude-code", "codex", "cursor"):
        project = tmp_path / f"proj-{platform}"
        project.mkdir()
        result = _install(project, platform=platform)
        assert result.exit_code == 0, result.output
        sync_result = _sync(project, platform=platform)
        assert sync_result.exit_code == 0, sync_result.output
        projects[platform] = project
    return projects


class TestStory3AgentsMdConvergence:
    """(Story 3 sc3) AGENTS.md is the single canonical agent file."""

    def test_agents_md_generated_content_is_byte_identical_across_platforms(
        self, three_platform_projects: dict[str, pathlib.Path]
    ):
        texts = {}
        for platform, project in three_platform_projects.items():
            agents_md = project / "AGENTS.md"
            assert agents_md.is_file(), f"{platform}: missing AGENTS.md"
            texts[platform] = agents_md.read_text(encoding="utf-8")

        # The auto-stack block is the generated, platform-independent
        # payload; compare from its start marker on. The block embeds a
        # per-second `generated_at` timestamp (sync's `_utc_now_iso`) and
        # the three sequential syncs can straddle a second boundary, so
        # normalize that timestamp out before the byte comparison.
        marker = "<!-- aiadev:auto-stack:start -->"
        ts = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")
        bodies = {
            p: ts.sub("<TS>", t[t.index(marker):]) for p, t in texts.items()
        }
        claude_body = bodies["claude-code"]
        assert claude_body.replace("<TS>", "").strip(), "empty after normalizing"
        for platform, body in bodies.items():
            assert body == claude_body, f"{platform} AGENTS.md diverges from claude-code"

        # Single auto-stack block per project, not duplicated.
        for platform, text in texts.items():
            assert text.count(marker) == 1, platform

    def test_claude_project_has_thin_claude_md_wrapper(
        self, three_platform_projects: dict[str, pathlib.Path]
    ):
        claude_project = three_platform_projects["claude-code"]
        wrapper = (claude_project / "CLAUDE.md").read_text(encoding="utf-8")
        lines = [line for line in wrapper.splitlines() if line.strip()]
        assert len(lines) <= 5
        assert "AGENTS.md" in wrapper
        assert "<!-- aiadev:auto-stack:start -->" not in wrapper

    def test_codex_and_cursor_have_no_wrapper_just_agents_md(
        self, three_platform_projects: dict[str, pathlib.Path]
    ):
        for platform in ("codex", "cursor"):
            project = three_platform_projects[platform]
            assert not (project / "CLAUDE.md").exists()
            assert (project / "AGENTS.md").is_file()


class TestStory2PathsRuleTransport:
    """(Story 2 sc2) testing.md's ``paths:`` transports per platform."""

    def test_claude_code_keeps_paths_no_always_apply(
        self, three_platform_projects: dict[str, pathlib.Path]
    ):
        installed = (
            three_platform_projects["claude-code"] / ".claude" / "rules" / "testing.md"
        )
        assert installed.is_file()
        fm = _frontmatter(installed.read_text(encoding="utf-8"))
        assert fm["paths"] == [
            "tests/**",
            "**/*.test.*",
            "**/*_test.*",
            "conftest.py",
        ]
        assert fm.get("alwaysApply") is not True

    def test_cursor_translates_paths_to_mdc_globs(
        self, three_platform_projects: dict[str, pathlib.Path]
    ):
        installed = (
            three_platform_projects["cursor"] / ".cursor" / "rules" / "testing.mdc"
        )
        assert installed.is_file()
        fm = _frontmatter(installed.read_text(encoding="utf-8"))
        assert "paths" not in fm
        assert "globs" in fm
        patterns = [p.strip() for p in fm["globs"].split(",")]
        assert patterns == ["tests/**", "**/*.test.*", "**/*_test.*", "conftest.py"]
        assert fm["alwaysApply"] is False

    def test_codex_strips_paths_with_no_error_or_warning(
        self, three_platform_projects: dict[str, pathlib.Path]
    ):
        installed = (
            three_platform_projects["codex"] / ".codex" / "rules" / "testing.md"
        )
        assert installed.is_file()
        fm = _frontmatter(installed.read_text(encoding="utf-8"))
        assert "paths" not in fm

        # Re-running install/sync for codex must surface no error/warning
        # about the stripped `paths:` key (Story 2 sc2's "no error, no
        # warning" guarantee).
        result = _install(three_platform_projects["codex"], platform="codex")
        assert result.exit_code == 0, result.output
        assert "error" not in result.output.lower()
        assert "warning" not in result.output.lower()


class TestStory1SkillFrontmatterMigration:
    """(Story 1 sc4) old-format skill auto-migrates on sync."""

    # Same 5 proprietary top-level fields as
    # test_sync_migrates_frontmatter.py's OLD_FORMAT_SKILL, but with
    # schema-conformant *values* (semver string; object-shaped
    # inputs/outputs, cf. skills/specify/SKILL.md) so the migrated
    # result can validate against both schemas below.
    OLD_FORMAT_SKILL = """---
name: legacy-interop-skill
description: A skill installed under the old aiadev frontmatter shape.
version: 0.1.0
inputs:
  - type: text
    description: demand description
outputs:
  - type: file
    path: spec.md
requires:
  - none
handoffs:
  - clarify
---

# Legacy Interop Skill

Body content that must survive migration byte-for-byte.
"""

    def test_migrated_skill_validates_against_both_schemas(
        self, three_platform_projects: dict[str, pathlib.Path]
    ):
        claude_project = three_platform_projects["claude-code"]
        skill_dir = claude_project / ".claude" / "skills" / "legacy-interop-skill"
        skill_dir.mkdir(parents=True)
        skill_path = skill_dir / "SKILL.md"
        skill_path.write_text(self.OLD_FORMAT_SKILL, encoding="utf-8")

        result = _sync(claude_project, platform="claude-code")
        assert result.exit_code == 0, result.output
        assert "migrat" in result.output.lower()

        migrated = skill_path.read_text(encoding="utf-8")
        assert "metadata:" in migrated and "aiadev:" in migrated
        # Body preserved byte-for-byte.
        old_body = self.OLD_FORMAT_SKILL.split("---", 2)[2]
        new_body = migrated.split("---", 2)[2]
        assert new_body == old_body

        fm, error = extract_frontmatter(skill_path)
        assert fm is not None, error

        agent_skills_schema = json.loads(
            (REPO_ROOT / "schemas" / "agent-skills.schema.json").read_text(
                encoding="utf-8"
            )
        )
        skill_frontmatter_schema = json.loads(
            (REPO_ROOT / "schemas" / "skill-frontmatter.schema.json").read_text(
                encoding="utf-8"
            )
        )
        for schema in (agent_skills_schema, skill_frontmatter_schema):
            errors = list(Draft202012Validator(schema).iter_errors(fm))
            assert not errors, [e.message for e in errors]


class TestStory4ManifestsAndRepoSkillConformance:
    """(Story 4 sc4) manifests --check + shipped SKILL.md conformance.

    Light re-assertion only; the heavy lifting for repo-wide SKILL.md
    conformance lives in tests/test_skills_conformance.py.
    """

    def test_manifests_check_exits_zero_at_repo_root(self):
        from aiadev.cli import main

        runner = CliRunner()
        cwd_before = os.getcwd()
        os.chdir(REPO_ROOT)
        try:
            result = runner.invoke(main, ["manifests", "--check"])
        finally:
            os.chdir(cwd_before)
        assert result.exit_code == 0, result.output

    def test_every_shipped_skill_md_validates_against_standard_schema(self):
        agent_skills_schema = json.loads(
            (REPO_ROOT / "schemas" / "agent-skills.schema.json").read_text(
                encoding="utf-8"
            )
        )
        skill_files = list(iter_skill_files(REPO_ROOT))
        assert skill_files, "expected the repo to ship at least one SKILL.md"

        validator = Draft202012Validator(agent_skills_schema)
        for skill_path in skill_files:
            fm, error = extract_frontmatter(skill_path)
            assert fm is not None, f"{skill_path}: {error}"
            errors = list(validator.iter_errors(fm))
            assert not errors, f"{skill_path}: {[e.message for e in errors]}"
