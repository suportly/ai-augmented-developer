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


# --- T006 -------------------------------------------------------------------


def test_learn_json_is_stable(tmp_path) -> None:
    ws = _build_workspace(tmp_path)
    result = _invoke(ws, ["--format", "json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert "schema_version" in payload
    assert "timestamp" not in result.output  # no execution timestamp
    subjects = {p["subject"] for p in payload["patterns"]}
    assert "plan-document-reviewer" in subjects
    # stable: same input → identical output
    result2 = _invoke(ws, ["--format", "json"])
    assert result2.output == result.output


# --- T007 -------------------------------------------------------------------


def test_learn_since_window_defaults_90d(tmp_path) -> None:
    ws = tmp_path / "ws"
    specs = ws / "specs"
    # Two features with an OLD reviewer failure (well beyond 90 days).
    old = [
        _entry("2000-01-01T10:00:00Z", "plan-document-reviewer", "CHANGES_REQUESTED"),
        _entry("2000-01-01T10:30:00Z", "plan-document-reviewer", "APPROVED"),
    ]
    _write_log(specs / "0001-old", old)
    _write_log(specs / "0002-old", old)

    # Default 90d window: the 2000 entries fall outside → no pattern.
    default = _invoke(ws, ["--format", "json"])
    assert default.exit_code == 0, default.output
    assert json.loads(default.output)["patterns"] == []

    # Explicit --since before 2000 → the pattern appears.
    since = _invoke(ws, ["--since", "1999-01-01", "--format", "json"])
    subjects = {p["subject"] for p in json.loads(since.output)["patterns"]}
    assert "plan-document-reviewer" in subjects


# --- T008 -------------------------------------------------------------------


def _snapshot(root: pathlib.Path) -> dict[str, bytes]:
    return {
        str(p.relative_to(root)): p.read_bytes()
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }


def test_learn_readonly_default_no_writes(tmp_path) -> None:
    ws = _build_workspace(tmp_path)
    before = _snapshot(ws)
    result = _invoke(ws, [])
    assert result.exit_code == 0, result.output
    assert _snapshot(ws) == before  # no file created or modified without --write


def test_learn_makes_no_network_calls(tmp_path) -> None:
    ws = _build_workspace(tmp_path)

    def _boom(*a, **k):
        raise AssertionError("learn must not touch the network")

    from unittest import mock

    with mock.patch("socket.socket", _boom):
        result = _invoke(ws, ["--format", "json"])
    assert result.exit_code == 0, result.output
