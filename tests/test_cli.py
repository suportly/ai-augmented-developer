"""Smoke tests for the top-level ``aiadev`` entry point."""
from __future__ import annotations

from click.testing import CliRunner

from aiadev.cli import main


def test_cli_version_command() -> None:
    result = CliRunner().invoke(main, ["--version"])
    assert result.exit_code == 0
    assert "aiadev" in result.output


def test_cli_help_lists_subcommands() -> None:
    result = CliRunner().invoke(main, ["--help"])
    assert result.exit_code == 0
    for command in ("validate", "init", "install", "doctor"):
        assert command in result.output
