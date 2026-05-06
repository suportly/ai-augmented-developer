"""Unit tests for ``aiadev.tasks_status`` — parse / validate / mark_done.

Spec: ``specs/0013-implement-task-status-tracking/spec.md``.
Covers Story 1 sc2, Story 2 sc1, sc2, sc3, sc4.

These tests are RED until T004 lands ``src/aiadev/tasks_status.py``: the
``import`` below fails with ``ModuleNotFoundError`` on a clean tree, which
is the right red signal per Article II.
"""
from __future__ import annotations

import pathlib
import shutil

import pytest

from aiadev.tasks_status import (
    TasksMdError,
    mark_done,
    parse,
    validate,
)

FIXTURES = pathlib.Path(__file__).parent / "fixtures" / "tasks_md_samples"

OUT_OF_ORDER_ERROR = (
    "ERROR: tasks.md inconsistency — T003 is done but T002 is pending. "
    "Fix tasks.md manually before resuming."
)


def test_parse_clean_returns_three_pending_rows() -> None:
    rows = parse(FIXTURES / "clean_3_tasks.md")

    assert [r.id for r in rows] == ["T001", "T002", "T003"]
    assert all(r.status == "pending" for r in rows)


def test_parse_all_done_returns_three_done_rows() -> None:
    rows = parse(FIXTURES / "all_done.md")

    assert [r.status for r in rows] == ["done", "done", "done"]


def test_parse_in_progress_preserves_raw_status() -> None:
    """Story 2 sc4: helper reports ``in_progress`` verbatim; the
    "treated as pending" mapping is the skill prose's job, not the
    helper's. The unit test guarantees the helper does not silently
    rewrite the value."""
    rows = parse(FIXTURES / "in_progress_mid_list.md")

    assert [r.status for r in rows] == ["done", "in_progress", "pending"]


def test_parse_malformed_block_yields_row_with_none_status() -> None:
    """``parse`` is tolerant; ``validate`` is the strict layer."""
    rows = parse(FIXTURES / "malformed_missing_status.md")

    assert rows[1].id == "T002"
    assert rows[1].status is None


def test_validate_clean_passes() -> None:
    rows = parse(FIXTURES / "clean_3_tasks.md")

    validate(rows)  # must not raise


def test_validate_all_done_passes() -> None:
    """Story 2 sc3: an all-``done`` file is internally consistent."""
    rows = parse(FIXTURES / "all_done.md")

    validate(rows)


def test_validate_in_progress_passes() -> None:
    """In-progress is a valid taxonomy value; validate does not reject it."""
    rows = parse(FIXTURES / "in_progress_mid_list.md")

    validate(rows)


def test_validate_malformed_raises_with_file_and_task_id() -> None:
    """cl-2 (resolved in spec): malformed Status lines must abort, not
    auto-repair, and the error must name both the task id and the
    1-based line number for the spec author to find the defect."""
    rows = parse(FIXTURES / "malformed_missing_status.md")

    with pytest.raises(TasksMdError) as excinfo:
        validate(rows)

    msg = str(excinfo.value)
    assert "T002" in msg
    assert "Status" in msg
    # Spec cl-2 mandates ``(line <N>)`` in the malformed error.
    malformed_row = next(r for r in rows if r.id == "T002")
    assert f"(line {malformed_row.line})" in msg


def test_validate_out_of_order_raises_exact_error_string() -> None:
    """Story 2 sc2: ``done`` ids must form a contiguous prefix; the
    error message is verbatim per the spec."""
    rows = parse(FIXTURES / "out_of_order_done_pending_done.md")

    with pytest.raises(TasksMdError) as excinfo:
        validate(rows)

    assert str(excinfo.value) == OUT_OF_ORDER_ERROR


def test_mark_done_flips_only_targeted_status_line(
    tmp_path: pathlib.Path,
) -> None:
    """Story 1 sc2: the per-task commit's diff touches only T002's
    status line — every other byte is unchanged."""
    src = FIXTURES / "clean_3_tasks.md"
    target = tmp_path / "tasks.md"
    shutil.copyfile(src, target)

    mark_done(target, "T002")

    after = target.read_text(encoding="utf-8")
    before = src.read_text(encoding="utf-8")

    expected = before.replace(
        "### T002 — second\n\n- **Status:** pending",
        "### T002 — second\n\n- **Status:** done",
        1,
    )
    assert after == expected


def test_mark_done_is_idempotent_on_already_done(
    tmp_path: pathlib.Path,
) -> None:
    """Story 2 sc1: re-running over an already-done row is a no-op
    (resume safety — the orchestrator skips done rows but a defensive
    second call must not corrupt the file)."""
    src = FIXTURES / "all_done.md"
    target = tmp_path / "tasks.md"
    shutil.copyfile(src, target)

    mark_done(target, "T002")

    assert target.read_text(encoding="utf-8") == src.read_text(encoding="utf-8")


def test_mark_done_unknown_task_raises(tmp_path: pathlib.Path) -> None:
    src = FIXTURES / "clean_3_tasks.md"
    target = tmp_path / "tasks.md"
    shutil.copyfile(src, target)

    with pytest.raises(TasksMdError):
        mark_done(target, "T999")
