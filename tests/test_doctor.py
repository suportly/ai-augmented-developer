"""Tests for ``aiadev doctor``."""
from __future__ import annotations

import pathlib

import pytest
from click.testing import CliRunner

from aiadev.commands.doctor import doctor_command


@pytest.mark.xfail(
    reason="T004 migrates the 22 SKILL.md files to metadata.aiadev; until "
    "then doctor's skill sweep fails on 10 real skills with proprietary "
    "top-level fields (spec 0016 Story 1, T002 rewrites the schema first).",
    strict=False,
)
def test_doctor_on_clean_repo_passes(isolated_framework: pathlib.Path, monkeypatch) -> None:
    monkeypatch.chdir(isolated_framework)
    result = CliRunner().invoke(doctor_command, [])
    assert result.exit_code == 0, result.output
    assert "all checks passed" in result.output.lower()


def test_doctor_fails_when_constitution_missing(
    isolated_framework: pathlib.Path, monkeypatch
) -> None:
    monkeypatch.chdir(isolated_framework)
    (isolated_framework / "constitution.md").unlink()
    # Force AIADEV_ROOT to the now-broken isolated tree so the fallback
    # chain (cwd walk, git toplevel, package install location) does not
    # find the real framework elsewhere and paper over the problem.
    monkeypatch.setenv("AIADEV_ROOT", str(isolated_framework))
    result = CliRunner().invoke(doctor_command, [])
    assert result.exit_code == 2


def test_doctor_fails_when_template_missing(
    isolated_framework: pathlib.Path, monkeypatch
) -> None:
    monkeypatch.chdir(isolated_framework)
    (isolated_framework / "templates" / "spec-template.md").unlink()
    result = CliRunner().invoke(doctor_command, [])
    assert result.exit_code == 1
    assert "templates/ missing" in result.output
