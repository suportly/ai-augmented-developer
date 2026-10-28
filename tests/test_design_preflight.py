"""preflight ``implement``: aviso não bloqueante quando a spec declara UI e falta design.md (0033 T002)."""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from aiadev import preflight
from aiadev.cli import main

SPEC = """# Spec

**UI:** {ui}

## Success criteria

- um critério

## User stories

### Story 1 — A (P1)

1. dado x
2. dado y
"""
TASKS = "# Tasks\n\n## Task list\n\n### T001 — a\n\n- **Spec scenarios:** Story 1 scenario 1, scenario 2\n"
WARN = "design.md is missing"


def _feature(tmp_path: Path, ui: str, *, design: bool = False, tasks: bool = True) -> Path:
    feature = tmp_path / "specs" / "0099-demo"
    feature.mkdir(parents=True)
    (feature / "spec.md").write_text(SPEC.format(ui=ui), encoding="utf-8")
    (feature / "plan.md").write_text("# Plan\n", encoding="utf-8")
    if tasks:
        (feature / "tasks.md").write_text(TASKS, encoding="utf-8")
    if design:
        (feature / "design.md").write_text("# Design\n", encoding="utf-8")
    return feature


def _check(tmp_path: Path, feature: Path, env=None):
    return preflight.check(
        "implement", feature, env=env or {}, current_branch=lambda: "", repo_root=tmp_path
    )


def _warnings(issues):
    return [i for i in issues if WARN in i.message]


def test_ui_yes_without_design_warns_non_blocking(tmp_path: Path) -> None:
    issues = _check(tmp_path, _feature(tmp_path, "yes"))
    found = _warnings(issues)
    assert len(found) == 1
    assert found[0].would_abort is False
    assert "/aia:design" in found[0].message
    assert not any(i.would_abort for i in issues)


def test_ui_yes_with_design_has_no_warning(tmp_path: Path) -> None:
    assert _check(tmp_path, _feature(tmp_path, "yes", design=True)) == []


def test_ui_no_has_no_warning(tmp_path: Path) -> None:
    assert _check(tmp_path, _feature(tmp_path, "no")) == []


def test_real_error_still_aborts_with_warning_present(tmp_path: Path) -> None:
    issues = _check(tmp_path, _feature(tmp_path, "yes", tasks=False))
    assert len(_warnings(issues)) == 1
    aborting = [i for i in issues if i.would_abort]
    assert any("tasks.md missing" in i.message for i in aborting)


def test_cli_exits_zero_prints_warning_and_payload_ok(tmp_path: Path, monkeypatch) -> None:
    _feature(tmp_path, "yes")
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("AIADEV_PREFLIGHT", raising=False)
    runner = CliRunner()
    result = runner.invoke(main, ["preflight", "implement", "--feature", "0099-demo"])
    assert result.exit_code == 0
    assert WARN in result.output

    as_json = runner.invoke(main, ["preflight", "implement", "--feature", "0099-demo", "--format", "json"])
    assert as_json.exit_code == 0
    payload = json.loads(as_json.stdout)
    assert payload["ok"] is True
    assert any(WARN in i["message"] for i in payload["issues"])
