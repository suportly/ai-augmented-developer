"""T052 - ``aiadev sync`` notices the removed terse-mode key and variable.

Spec 0030 Story 6 scenario 2: ``aiadev.terseMode`` in ``.claude/settings.json``
(flat or nested) or ``AIADEV_TERSE`` in the environment yields one notice line;
the setting is otherwise ignored and the exit code does not change.
"""
from __future__ import annotations

import json
import pathlib

import pytest
from click.testing import CliRunner

from aiadev.commands.install import install_command
from aiadev.commands.sync import sync_command


@pytest.fixture
def project(
    isolated_framework: pathlib.Path, tmp_path: pathlib.Path, monkeypatch
) -> pathlib.Path:
    monkeypatch.setenv("AIADEV_ROOT", str(isolated_framework))
    monkeypatch.delenv("AIADEV_TERSE", raising=False)
    root = tmp_path / "consumer"
    root.mkdir()
    result = CliRunner().invoke(
        install_command,
        ["--project-root", str(root), "--preset", "lean", "--non-interactive",
         "--vars", "PROJECT_NAME=TerseNotice"],
    )
    assert result.exit_code == 0, result.output
    return root


def _sync(project: pathlib.Path, *extra: str):
    return CliRunner().invoke(sync_command, ["--project-root", str(project), *extra])


def _settings(project: pathlib.Path, text: str) -> None:
    path = project / ".claude" / "settings.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _notices(output: str) -> list[str]:
    return [line for line in output.splitlines() if "terse mode was removed" in line]


@pytest.mark.parametrize(
    "settings",
    [
        json.dumps({"aiadev.terseMode": "full"}),
        json.dumps({"aiadev": {"terseMode": "full"}}),
    ],
    ids=["flat-key", "nested-key"],
)
def test_settings_key_gets_one_notice(project: pathlib.Path, settings: str) -> None:
    _settings(project, settings)
    result = _sync(project)
    assert result.exit_code == 0, result.output
    notices = _notices(result.output)
    assert len(notices) == 1, result.output
    assert "aiadev.terseMode" in notices[0] and "ignored" in notices[0]


def test_env_var_gets_one_notice(project: pathlib.Path, monkeypatch) -> None:
    monkeypatch.setenv("AIADEV_TERSE", "1")
    result = _sync(project)
    assert result.exit_code == 0, result.output
    notices = _notices(result.output)
    assert len(notices) == 1, result.output
    assert "AIADEV_TERSE" in notices[0]


def test_notice_also_appears_in_dry_run(project: pathlib.Path) -> None:
    _settings(project, json.dumps({"aiadev.terseMode": "lite"}))
    result = _sync(project, "--dry-run")
    assert result.exit_code == 0, result.output
    assert len(_notices(result.output)) == 1


def test_no_key_and_no_variable_means_no_notice(project: pathlib.Path) -> None:
    _settings(project, json.dumps({"aiadev": {"other": 1}, "model": "x"}))
    result = _sync(project)
    assert result.exit_code == 0, result.output
    assert _notices(result.output) == []


@pytest.mark.parametrize("text", ["{not json", "[1, 2]", ""], ids=["invalid", "list", "empty"])
def test_unusable_settings_is_ignored_silently(project: pathlib.Path, text: str) -> None:
    _settings(project, text)
    result = _sync(project)
    assert result.exit_code == 0, result.output
    assert _notices(result.output) == []
    assert "Traceback" not in result.output
