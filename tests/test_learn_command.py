"""T005–T008, T010 — the `aiadev learn` CLI command (spec 0018)."""
from __future__ import annotations

import json
import os
import pathlib

from click.testing import CliRunner

from aiadev.cli import main


def _write_log(spec_dir: pathlib.Path, entries: list[dict]) -> None:
    spec_dir.mkdir(parents=True, exist_ok=True)
    with (spec_dir / ".review-log.jsonl").open("w", encoding="utf-8") as fh:
        for e in entries:
            fh.write(json.dumps(e) + "\n")


def _entry(ts, reviewer, verdict, task_id="branch-review", note=""):
    return {
        "timestamp": ts,
        "reviewer": reviewer,
        "verdict": verdict,
        "has_why_no_issues_block": verdict == "APPROVED",
        "task_id": task_id,
        "note": note,
    }


def _reviewer_fails(reviewer, note="prose"):
    return [
        _entry("2026-07-01T10:00:00Z", reviewer, "CHANGES_REQUESTED", note=note),
        _entry("2026-07-01T10:30:00Z", reviewer, "APPROVED"),
    ]


def _build_workspace(tmp_path: pathlib.Path) -> pathlib.Path:
    ws = tmp_path / "ws"
    specs = ws / "specs"
    _write_log(specs / "0001-a", _reviewer_fails("plan-document-reviewer"))
    _write_log(specs / "0002-b", _reviewer_fails("plan-document-reviewer"))
    _write_log(
        specs / "0003-c",
        [
            _entry("2026-07-02T09:00:00Z", "code-reviewer", "CHANGES_REQUESTED", task_id="T007"),
            _entry("2026-07-02T09:30:00Z", "code-reviewer", "APPROVED", task_id="T007"),
        ],
    )
    return ws


def _invoke(ws: pathlib.Path, args: list[str]):
    runner = CliRunner()
    before = os.getcwd()
    os.chdir(ws)
    try:
        return runner.invoke(main, ["learn", *args])
    finally:
        os.chdir(before)


# --- T005 -------------------------------------------------------------------


def test_learn_text_output_ranks_patterns(tmp_path) -> None:
    ws = _build_workspace(tmp_path)
    result = _invoke(ws, [])
    assert result.exit_code == 0, result.output
    assert "plan-document-reviewer" in result.output
    assert "T007" in result.output  # task-rework subject surfaced
