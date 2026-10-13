"""``aiadev sync`` and the files the framework stopped shipping (spec 0030 Story 6 sc1).

The engine's own rules (hash rule, shared owner, the MCP file) are covered
in ``test_install_engine.py``; this file is about what sync hands the engine.
"""
from __future__ import annotations

import pathlib

import pytest
from click.testing import CliRunner

from aiadev.commands import sync as sync_module
from aiadev.install_engine import InstallReport
from aiadev.install_manifest import InstalledPreset, Manifest, save as save_manifest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent


@pytest.mark.parametrize("dry_run", [True, False], ids=["dry-run", "real-run"])
def test_dry_run_hands_every_preset_the_same_manifest_object(
    tmp_path: pathlib.Path, monkeypatch, dry_run: bool
) -> None:
    # A dry run saves nothing, so the only way for the second preset to see
    # what the first one would have recorded is the manifest object itself;
    # a real run keeps reading the saved one.
    monkeypatch.setenv("AIADEV_ROOT", str(REPO_ROOT))
    project = tmp_path / "project"
    save_manifest(
        Manifest(
            aiadev_version="0.0.0",
            installed_presets=[
                InstalledPreset(name, "1.0.0", "2026-04-14T12:00:00Z")
                for name in ("alpha", "beta")
            ],
        ),
        project / ".aiadev" / "installed.yaml",
    )
    handed: list[Manifest | None] = []

    def fake_install(preset_path, project_root, variables, **kwargs):
        handed.append(kwargs.get("manifest"))
        return InstallReport(preset_name="fake", mode=kwargs["mode"])

    monkeypatch.setattr(sync_module, "run_install", fake_install)
    monkeypatch.setattr(sync_module, "_locate_preset", lambda root, name: tmp_path)

    args = ["--project-root", str(project), "--platform", "claude-code"]
    result = CliRunner().invoke(
        sync_module.sync_command, [*args, "--dry-run"] if dry_run else args
    )

    assert result.exit_code == 0, result.output
    assert len(handed) == 2
    if dry_run:
        assert handed[0] is not None and handed[0] is handed[1]
    else:
        assert handed == [None, None]
