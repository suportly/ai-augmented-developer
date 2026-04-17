"""Tests for ``aiadev lang`` — swap the Language header in an existing feature."""
from __future__ import annotations

import pathlib

from click.testing import CliRunner

from aiadev.commands.init import init_command
from aiadev.commands.lang import lang_command


def _init(runner: CliRunner, *args: str):
    return runner.invoke(init_command, list(args))


def _lang(runner: CliRunner, *args: str):
    return runner.invoke(lang_command, list(args))


def test_lang_rewrites_header_in_all_artifacts(
    isolated_framework: pathlib.Path, monkeypatch
) -> None:
    monkeypatch.chdir(isolated_framework)
    runner = CliRunner()
    assert _init(runner, "--feature", "Alpha one").exit_code == 0
    # init left us on branch feature/alpha-one with specs/0001-alpha-one/.

    result = _lang(runner, "pt-BR")

    assert result.exit_code == 0, result.output
    for artifact in ("spec.md", "plan.md", "tasks.md"):
        text = (
            isolated_framework / "specs" / "0001-alpha-one" / artifact
        ).read_text(encoding="utf-8")
        assert "Language:** pt-BR" in text, artifact
        assert "Language:** en" not in text, artifact


def test_lang_preserves_trailing_comment(
    isolated_framework: pathlib.Path, monkeypatch
) -> None:
    monkeypatch.chdir(isolated_framework)
    runner = CliRunner()
    assert _init(runner, "--feature", "beta").exit_code == 0

    assert _lang(runner, "fr").exit_code == 0

    spec = (isolated_framework / "specs" / "0001-beta" / "spec.md").read_text(
        encoding="utf-8"
    )
    # The template ships `**Language:** {{DOC_LANGUAGE}} <!-- BCP-47 tag; ... -->`.
    # The trailing HTML comment must survive the rewrite.
    assert "**Language:** fr <!-- BCP-47" in spec


def test_lang_explicit_feature_dir_wins(
    isolated_framework: pathlib.Path, monkeypatch
) -> None:
    monkeypatch.chdir(isolated_framework)
    runner = CliRunner()
    # Stay on main so branch-inference would not match.
    assert (
        _init(runner, "--feature", "gamma", "--branch", "-", "--no-git").exit_code
        == 0
    )

    result = _lang(runner, "es", "--feature", "0001-gamma")

    assert result.exit_code == 0, result.output
    text = (isolated_framework / "specs" / "0001-gamma" / "spec.md").read_text(
        encoding="utf-8"
    )
    assert "Language:** es" in text


def test_lang_dry_run_writes_nothing(
    isolated_framework: pathlib.Path, monkeypatch
) -> None:
    monkeypatch.chdir(isolated_framework)
    runner = CliRunner()
    assert _init(runner, "--feature", "delta").exit_code == 0
    spec_path = isolated_framework / "specs" / "0001-delta" / "spec.md"
    before = spec_path.read_text(encoding="utf-8")

    result = _lang(runner, "de", "--dry-run")

    assert result.exit_code == 0, result.output
    assert "dry-run" in result.output
    assert spec_path.read_text(encoding="utf-8") == before


def test_lang_errors_when_no_feature_matches_branch(
    isolated_framework: pathlib.Path, monkeypatch
) -> None:
    monkeypatch.chdir(isolated_framework)
    runner = CliRunner()

    result = _lang(runner, "pt-BR")

    assert result.exit_code != 0
    output = result.output.lower()
    assert (
        "no feature directory" in output
        or "could not detect" in output
        or "no specs/" in output
    ), result.output


def test_lang_errors_when_explicit_feature_dir_missing(
    isolated_framework: pathlib.Path, monkeypatch
) -> None:
    monkeypatch.chdir(isolated_framework)
    runner = CliRunner()

    result = _lang(runner, "pt-BR", "--feature", "9999-does-not-exist")

    assert result.exit_code != 0
    assert "not found" in result.output.lower()
