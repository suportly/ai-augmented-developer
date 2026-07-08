"""T007 — ``aiadev sync`` auto-migrates installed skills' frontmatter.

Spec: specs/0016-agent-skills-interop/spec.md, Story 1 scenario 4 + cl-5.
Plan: ADR-4 — reuse the pure migrator in
:mod:`aiadev.frontmatter_migrate` (``migrate_skill_file``). After the
artifact re-sync step, ``aiadev sync`` sweeps every installed skill
directory for the detected platform and rewrites any SKILL.md still in
the old proprietary-top-level-fields format into the new
``metadata.aiadev`` shape, without touching the Markdown body. A second
sync run must be a no-op (byte-identical file). A malformed SKILL.md
must not abort the sync (exit code stays 0; a warning is printed).
"""
from __future__ import annotations

import pathlib

import pytest
from click.testing import CliRunner

from aiadev.commands.install import install_command
from aiadev.commands.sync import sync_command

OLD_FORMAT_SKILL = """---
name: legacy-skill
description: A skill installed under the old aiadev frontmatter shape.
version: 1
inputs:
  - demand description
outputs:
  - spec.md
requires:
  - none
handoffs:
  - clarify
---

# Legacy Skill

Body content that must survive migration byte-for-byte.

- bullet one
- bullet two
"""

NEW_FORMAT_SKILL = """---
name: modern-skill
description: A skill already installed in the new frontmatter shape.
license: MIT
metadata:
  aiadev:
    version: 1
    inputs:
      - demand description
    outputs:
      - spec.md
    requires:
      - none
    handoffs:
      - clarify
---

# Modern Skill

Already conformant body.
"""

MALFORMED_SKILL = """---
name: broken-skill
description: [this is a list, not fixable
version: 1
---

# Broken Skill
"""


@pytest.fixture
def synced_project(
    isolated_framework: pathlib.Path, tmp_path: pathlib.Path, monkeypatch
) -> pathlib.Path:
    """A project with the lean preset installed under Claude Code."""
    monkeypatch.setenv("AIADEV_ROOT", str(isolated_framework))
    project = tmp_path / "consumer"
    project.mkdir()
    runner = CliRunner()
    result = runner.invoke(
        install_command,
        [
            "--project-root",
            str(project),
            "--preset",
            "lean",
            "--non-interactive",
            "--vars",
            "PROJECT_NAME=SyncMigrate",
        ],
    )
    assert result.exit_code == 0, result.output
    return project


def _run_sync(project: pathlib.Path):
    runner = CliRunner()
    return runner.invoke(sync_command, ["--project-root", str(project)])


def test_sync_migrates_old_format_skill_body_preserved(synced_project: pathlib.Path):
    skill_dir = synced_project / ".claude" / "skills" / "legacy-skill"
    skill_dir.mkdir(parents=True)
    skill_path = skill_dir / "SKILL.md"
    skill_path.write_text(OLD_FORMAT_SKILL, encoding="utf-8")

    result = _run_sync(synced_project)
    assert result.exit_code == 0, result.output

    migrated = skill_path.read_text(encoding="utf-8")
    assert "metadata:" in migrated
    assert "aiadev:" in migrated
    # Proprietary fields no longer live at the top level.
    lines = migrated.split("\n")
    fm_end = lines.index("---", 1)
    top_level_keys = {
        line.split(":", 1)[0]
        for line in lines[1:fm_end]
        if line and not line.startswith((" ", "-"))
    }
    assert top_level_keys.isdisjoint({"version", "inputs", "outputs", "requires", "handoffs"})

    # Body preserved byte-for-byte.
    old_body = OLD_FORMAT_SKILL.split("---", 2)[2]
    new_body = migrated.split("---", 2)[2]
    assert new_body == old_body

    # Sync reports the migration count in its output.
    assert "migrat" in result.output.lower()


def test_second_sync_run_is_a_noop(synced_project: pathlib.Path):
    skill_dir = synced_project / ".claude" / "skills" / "legacy-skill"
    skill_dir.mkdir(parents=True)
    skill_path = skill_dir / "SKILL.md"
    skill_path.write_text(OLD_FORMAT_SKILL, encoding="utf-8")

    first = _run_sync(synced_project)
    assert first.exit_code == 0, first.output
    migrated_bytes = skill_path.read_bytes()

    second = _run_sync(synced_project)
    assert second.exit_code == 0, second.output
    assert skill_path.read_bytes() == migrated_bytes


def test_malformed_skill_does_not_abort_sync(synced_project: pathlib.Path):
    skill_dir = synced_project / ".claude" / "skills" / "broken-skill"
    skill_dir.mkdir(parents=True)
    skill_path = skill_dir / "SKILL.md"
    skill_path.write_text(MALFORMED_SKILL, encoding="utf-8")
    original_bytes = skill_path.read_bytes()

    result = _run_sync(synced_project)

    assert result.exit_code == 0, result.output
    assert "warning" in result.output.lower()
    # File left untouched since migration failed.
    assert skill_path.read_bytes() == original_bytes


def test_new_format_skill_untouched_byte_identical(synced_project: pathlib.Path):
    skill_dir = synced_project / ".claude" / "skills" / "modern-skill"
    skill_dir.mkdir(parents=True)
    skill_path = skill_dir / "SKILL.md"
    skill_path.write_text(NEW_FORMAT_SKILL, encoding="utf-8")
    original_bytes = skill_path.read_bytes()

    result = _run_sync(synced_project)

    assert result.exit_code == 0, result.output
    assert skill_path.read_bytes() == original_bytes


def test_stack_refresh_does_not_clobber_step1_manifest_records(
    synced_project: pathlib.Path, isolated_framework: pathlib.Path
):
    """Regression: step 2's manifest-hash refresh must not overwrite the
    manifest with the stale pre-step-1 snapshot.

    Step 1 (run_install) manages its own manifest lifecycle and saves
    fresh file records itself — including records for any artifact the
    framework grew since install. If step 2 then saves the manifest
    object loaded at the top of sync_command, those fresh records are
    wiped, and the *next* sync reports a false conflict on a file sync
    itself wrote.
    """
    # Grow the framework by one skill after install, so step 1 of the
    # next sync persists a brand-new manifest record that step 2 could
    # lose.
    new_skill_dir = isolated_framework / "skills" / "brand-new-skill"
    new_skill_dir.mkdir(parents=True)
    (new_skill_dir / "SKILL.md").write_text(NEW_FORMAT_SKILL, encoding="utf-8")

    first = _run_sync(synced_project)
    assert first.exit_code == 0, first.output
    installed_copy = (
        synced_project / ".claude" / "skills" / "brand-new-skill" / "SKILL.md"
    )
    assert installed_copy.is_file()

    manifest_text = (synced_project / ".aiadev" / "installed.yaml").read_text(
        encoding="utf-8"
    )
    assert "brand-new-skill" in manifest_text, (
        "step 2 clobbered the manifest record step 1 just persisted"
    )

    second = _run_sync(synced_project)
    assert second.exit_code == 0, second.output


def test_dry_run_touches_neither_skill_nor_manifest(synced_project: pathlib.Path):
    skill_dir = synced_project / ".claude" / "skills" / "legacy-skill"
    skill_dir.mkdir(parents=True)
    skill_path = skill_dir / "SKILL.md"
    skill_path.write_text(OLD_FORMAT_SKILL, encoding="utf-8")
    skill_bytes = skill_path.read_bytes()

    manifest_path = synced_project / ".aiadev" / "installed.yaml"
    manifest_bytes = manifest_path.read_bytes()

    runner = CliRunner()
    result = runner.invoke(
        sync_command, ["--project-root", str(synced_project), "--dry-run"]
    )

    assert result.exit_code == 0, result.output
    assert skill_path.read_bytes() == skill_bytes
    assert manifest_path.read_bytes() == manifest_bytes
