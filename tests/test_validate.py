"""Tests for the validator core and the ``aiadev validate`` command."""
from __future__ import annotations

import pathlib

from click.testing import CliRunner

from aiadev.commands.validate import validate_command
from aiadev.validate import validate_paths

FIXTURES = pathlib.Path(__file__).parent / "fixtures"


def test_all_repository_skills_pass(framework_root: pathlib.Path) -> None:
    """The repo must never ship a skill that fails its own validator."""
    report = validate_paths([], root=framework_root)
    assert report.ok, "\n".join(issue.format() for issue in report.failed)
    # Sanity: we expect at least a dozen skills shipped (pipeline + quality).
    assert len(report.passed) >= 10


def test_valid_fixture_passes(framework_root: pathlib.Path) -> None:
    report = validate_paths([FIXTURES / "valid-skill" / "SKILL.md"], root=framework_root)
    assert report.ok


def test_mismatched_name_fails(framework_root: pathlib.Path) -> None:
    report = validate_paths(
        [FIXTURES / "mismatched-name" / "SKILL.md"], root=framework_root
    )
    assert not report.ok
    assert "does not match directory" in report.failed[0].message


def test_missing_frontmatter_fails(framework_root: pathlib.Path) -> None:
    report = validate_paths(
        [FIXTURES / "missing-frontmatter" / "SKILL.md"], root=framework_root
    )
    assert not report.ok
    assert "frontmatter" in report.failed[0].message


def test_short_description_fails(framework_root: pathlib.Path) -> None:
    report = validate_paths(
        [FIXTURES / "short-description" / "SKILL.md"], root=framework_root
    )
    assert not report.ok
    assert "description" in report.failed[0].message


def test_cli_exits_zero_on_valid(isolated_framework: pathlib.Path, monkeypatch) -> None:
    monkeypatch.chdir(isolated_framework)
    result = CliRunner().invoke(validate_command, [])
    assert result.exit_code == 0, result.output
    assert "passed" in result.output.lower()


def test_cli_exits_one_on_failure(
    isolated_framework: pathlib.Path, tmp_path: pathlib.Path, monkeypatch
) -> None:
    monkeypatch.chdir(isolated_framework)
    # Break a skill by corrupting its frontmatter.
    broken = isolated_framework / "skills" / "implement" / "SKILL.md"
    broken.write_text(
        "---\nname: wrong-name\ndescription: something sufficiently long to pass.\n---\n"
        "# body\n",
        encoding="utf-8",
    )
    result = CliRunner().invoke(validate_command, [])
    assert result.exit_code == 1
    assert "FAIL" in result.output
