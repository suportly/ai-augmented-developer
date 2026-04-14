"""Tests for the ``aiadev install`` stub."""
from __future__ import annotations

import pathlib

from click.testing import CliRunner

from aiadev.commands.install import install_command


def test_install_lists_preset_contents(
    isolated_framework: pathlib.Path, monkeypatch
) -> None:
    monkeypatch.chdir(isolated_framework)
    result = CliRunner().invoke(
        install_command,
        ["--platform", "claude-code", "--preset", "django-drf-react"],
    )
    assert result.exit_code == 0, result.output
    assert "django-drf-react" in result.output
    assert "CLAUDE.md" in result.output


def test_install_rejects_unknown_preset(
    isolated_framework: pathlib.Path, monkeypatch
) -> None:
    monkeypatch.chdir(isolated_framework)
    result = CliRunner().invoke(
        install_command,
        ["--platform", "cursor", "--preset", "does-not-exist"],
    )
    assert result.exit_code == 1
    assert "not found" in result.output


def test_install_rejects_unknown_platform(
    isolated_framework: pathlib.Path, monkeypatch
) -> None:
    monkeypatch.chdir(isolated_framework)
    result = CliRunner().invoke(
        install_command,
        ["--platform", "windows-notepad", "--preset", "lean"],
    )
    assert result.exit_code == 2  # Click rejects the invalid choice
