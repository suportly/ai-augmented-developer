"""Tests for ``aiadev init``."""
from __future__ import annotations

import pathlib
import subprocess

import pytest
from click.testing import CliRunner

from aiadev.commands.init import init_command


def _run(runner: CliRunner, *args: str):
    return runner.invoke(init_command, list(args))


def test_init_creates_spec_plan_tasks(isolated_framework: pathlib.Path, monkeypatch) -> None:
    monkeypatch.chdir(isolated_framework)
    result = _run(CliRunner(), "--feature", "User login flow")
    assert result.exit_code == 0, result.output

    feature_dir = isolated_framework / "specs" / "feature-user-login-flow"
    assert feature_dir.is_dir()
    for name in ("spec.md", "plan.md", "tasks.md"):
        assert (feature_dir / name).is_file(), name

    spec_content = (feature_dir / "spec.md").read_text(encoding="utf-8")
    assert "User login flow" in spec_content
    # Placeholders should have been substituted.
    assert "{{FEATURE_NAME}}" not in spec_content
    assert "{{BRANCH}}" not in spec_content
    # The [NEEDS CLARIFICATION] marker in the template must survive — that
    # is intentional; `clarify` is the skill that resolves it.
    assert "[NEEDS CLARIFICATION" in spec_content


def test_init_refuses_to_overwrite(isolated_framework: pathlib.Path, monkeypatch) -> None:
    monkeypatch.chdir(isolated_framework)
    runner = CliRunner()
    first = _run(runner, "--feature", "alpha")
    assert first.exit_code == 0, first.output
    second = _run(runner, "--feature", "alpha")
    assert second.exit_code == 1
    assert "already exists" in second.output


def test_init_creates_branch(isolated_framework: pathlib.Path, monkeypatch) -> None:
    monkeypatch.chdir(isolated_framework)
    result = _run(CliRunner(), "--feature", "beta")
    assert result.exit_code == 0, result.output
    branch = subprocess.check_output(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=str(isolated_framework),
        text=True,
    ).strip()
    assert branch == "feature/beta"


def test_init_dry_run_writes_nothing(isolated_framework: pathlib.Path, monkeypatch) -> None:
    monkeypatch.chdir(isolated_framework)
    result = _run(CliRunner(), "--feature", "gamma", "--dry-run")
    assert result.exit_code == 0, result.output
    assert "dry-run" in result.output
    assert not (isolated_framework / "specs" / "feature-gamma").exists()


def test_init_spec_id_is_monotonic(isolated_framework: pathlib.Path, monkeypatch) -> None:
    monkeypatch.chdir(isolated_framework)
    runner = CliRunner()
    assert _run(runner, "--feature", "one").exit_code == 0
    # Stay on current branch so second init works without git issues.
    assert _run(runner, "--feature", "two", "--branch", "-", "--no-git").exit_code == 0
    first_spec = (isolated_framework / "specs" / "feature-one" / "spec.md").read_text(encoding="utf-8")
    second_spec = (isolated_framework / "specs" / "feature-two" / "spec.md").read_text(encoding="utf-8")
    assert "Spec ID:** 0001" in first_spec
    assert "Spec ID:** 0002" in second_spec
