"""T001 (spec 0033): `**UI:**` header drives the /aia:design recommendation."""
from __future__ import annotations

from pathlib import Path

import pytest

from aiadev.pipeline_state import declares_ui, pipeline_snapshot

ROOT = Path(__file__).resolve().parent.parent


def _feature(tmp_path: Path, ui_line: str, statuses=("pending", "pending"), design=False):
    d = tmp_path / "specs" / "0001-x"
    d.mkdir(parents=True)
    (d / "spec.md").write_text(f"# S\n\n**Branch:** `b`\n{ui_line}\n", encoding="utf-8")
    (d / "plan.md").write_text("# P\n", encoding="utf-8")
    (d / "tasks.md").write_text(
        "".join(f"### T00{i}\n\n- **Status:** {s}\n\n" for i, s in enumerate(statuses)),
        encoding="utf-8",
    )
    if design:
        (d / "design.md").write_text("# D\n", encoding="utf-8")
    return tmp_path


def test_ui_yes_pending_no_design_recommends_design(tmp_path):
    snap = pipeline_snapshot(_feature(tmp_path, "**UI:** yes"), feature="0001-x")
    assert snap.command == "/aia:design"
    assert "design" in snap.reason and snap.ui is True


def test_ui_yes_with_design_goes_to_implement(tmp_path):
    snap = pipeline_snapshot(_feature(tmp_path, "**UI:** yes", design=True), feature="0001-x")
    assert snap.command == "/aia:implement"


@pytest.mark.parametrize(
    "line",
    ["**UI:** no <!-- yes if the feature adds or changes screens -->", "", "**UI:** yes|no", "**UI:** yes | no"],
)
def test_no_ui_unchanged(tmp_path, line):
    snap = pipeline_snapshot(_feature(tmp_path, line), feature="0001-x")
    assert snap.command == "/aia:implement"
    assert snap.ui is False


def test_some_task_done_skips_design(tmp_path):
    snap = pipeline_snapshot(
        _feature(tmp_path, "**UI:** yes", statuses=("done", "pending")), feature="0001-x"
    )
    assert snap.command == "/aia:implement"


def test_declares_ui_variants():
    assert declares_ui("a\n**UI:** yes\n")
    assert declares_ui("**UI:** yes <!-- c -->")
    assert not declares_ui("**UI:** yes|no")
    assert not declares_ui("**UI:** yes | no")
    assert not declares_ui("**UI:** no")


def test_template_has_ui_line():
    text = (ROOT / "templates" / "spec-template.md").read_text(encoding="utf-8")
    line = next(ln for ln in text.splitlines() if ln.startswith("**UI:**"))
    assert "<!--" in line and not declares_ui(line)
