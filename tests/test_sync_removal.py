"""``aiadev sync`` and the files the framework stopped shipping (spec 0030 Story 6 sc1).

The engine's own rules (hash rule, shared owner, the MCP file, a dry run over
several presets) are covered in ``test_install_engine.py``; this file is about
what the command hands the engine and what it prints back.
"""
from __future__ import annotations

import pathlib
import re
import shutil

from click.testing import CliRunner

from aiadev.commands.sync import sync_command
from aiadev.install_engine import install
from aiadev.install_manifest import (
    InstalledFile,
    load as load_manifest,
    save as save_manifest,
)

_RULES = pathlib.PurePosixPath(".claude/rules")
FORGED = "../[/x].md"


def _ship(framework: pathlib.Path, **presets: tuple[str, ...]) -> None:
    """(Re)write the framework's presets so each ships exactly the given rules."""
    shutil.rmtree(framework / "presets", ignore_errors=True)
    for name, rules in presets.items():
        preset = framework / "presets" / name
        (preset / "rules").mkdir(parents=True)
        (preset / "preset.yaml").write_text(f"name: {name}\nversion: 1.0.0\n", encoding="utf-8")
        for rule in rules:
            (preset / "rules" / f"{rule}.md").write_text(f"# {rule}\n", encoding="utf-8")


def _rows(output: str, action: str) -> set[str]:
    """Paths of the report-table rows whose Action cell is exactly ``action``."""
    pattern = rf"^[│|]\s+{re.escape(action)}\s+[│|]\s+(\S+)\s+[│|]$"
    return set(re.findall(pattern, output, flags=re.MULTILINE))


def test_sync_lists_what_it_removes_and_what_it_keeps_in_dry_run_and_real_run(
    framework_root: pathlib.Path, tmp_path: pathlib.Path, monkeypatch
) -> None:
    framework = tmp_path / "framework"  # the bare minimum a root needs
    (framework / "templates").mkdir(parents=True)
    (framework / "constitution.md").write_text("# Constitution\n", encoding="utf-8")
    shutil.copytree(framework_root / "schemas", framework / "schemas")
    monkeypatch.setenv("AIADEV_ROOT", str(framework))
    project = tmp_path / "project"
    rules = project / _RULES

    # v1: alpha and beta both ship "shared". Beta has no record of the file
    # alpha already put there, which the engine calls a conflict, so it
    # installs with force.
    _ship(framework, alpha=("shared", "gone", "edited"), beta=("shared",))
    for name in ("alpha", "beta"):
        install(
            framework / "presets" / name, project, {}, force=True, framework_root=framework
        )
    (rules / "edited.md").write_text("my own rule\n", encoding="utf-8")
    # A manifest entry outside the project (the manifest is committable, so
    # untrusted) is listed but never touched; its name reads like Rich markup.
    manifest_file = project / ".aiadev" / "installed.yaml"
    manifest = load_manifest(manifest_file)
    manifest.find_preset("alpha").files.append(InstalledFile(FORGED, "0" * 64, "rule"))
    save_manifest(manifest, manifest_file)
    # v2 ships nothing: alpha releases "shared" (beta still records it), beta,
    # the last owner, retires it - which only a dry run that carries alpha's
    # outcome over to beta can foresee.
    _ship(framework, alpha=(), beta=())

    args = ["--project-root", str(project), "--platform", "claude-code"]
    runner = CliRunner()
    dry = runner.invoke(sync_command, [*args, "--dry-run"])
    assert dry.exit_code == 0, dry.output
    assert (rules / "shared.md").is_file() and (rules / "gone.md").is_file()

    real = runner.invoke(sync_command, args)
    assert real.exit_code == 0, real.output  # a kept file is not a failure
    assert not (rules / "shared.md").exists() and not (rules / "gone.md").exists()
    assert (rules / "edited.md").read_text(encoding="utf-8") == "my own rule\n"

    retired = {f"{_RULES}/shared.md", f"{_RULES}/gone.md"}
    assert _rows(dry.output, "would remove") == retired
    assert _rows(real.output, "remove") == retired
    kept = {f"{_RULES}/edited.md", FORGED}
    assert _rows(dry.output, "would keep") == kept
    assert _rows(real.output, "keep") == kept
