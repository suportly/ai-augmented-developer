"""T001–T004, T009 — the `aiadev learn` pattern-detection engine (spec 0018).

The engine is read-only and reuses the public metrics primitives. Test setup
injects plain dicts (spec_id -> review entries) so no filesystem is needed.
"""
from __future__ import annotations

import pytest

from aiadev import learn as _learn


def _entry(ts: str, reviewer: str, verdict: str, task_id: str = "branch-review", note: str = ""):
    return {
        "timestamp": ts,
        "reviewer": reviewer,
        "verdict": verdict,
        "has_why_no_issues_block": verdict == "APPROVED",
        "task_id": task_id,
        "note": note,
    }


def _spec_where_reviewer_fails_first_pass(reviewer: str, note: str = "some prose"):
    # First (chronological) entry is CHANGES_REQUESTED → first pass failed.
    return [
        _entry("2026-07-01T10:00:00Z", reviewer, "CHANGES_REQUESTED", note=note),
        _entry("2026-07-01T10:30:00Z", reviewer, "APPROVED"),
    ]


# --- T001: recurring reviewer first-pass failures ---------------------------


def test_detects_recurring_reviewer_failure() -> None:
    per_spec = {
        "0001": _spec_where_reviewer_fails_first_pass("plan-document-reviewer"),
        "0002": _spec_where_reviewer_fails_first_pass("plan-document-reviewer"),
    }
    patterns = _learn.recurring_reviewer_failures(per_spec)
    subjects = {p.subject: p for p in patterns}
    assert "plan-document-reviewer" in subjects
    p = subjects["plan-document-reviewer"]
    assert p.kind == "reviewer-recurrence"
    assert p.occurrences == 2
    assert p.features == ("0001", "0002")


def test_reviewer_passing_first_pass_is_not_a_pattern() -> None:
    per_spec = {
        "0001": [_entry("2026-07-01T10:00:00Z", "code-reviewer", "APPROVED")],
    }
    patterns = _learn.recurring_reviewer_failures(per_spec)
    assert all(p.subject != "code-reviewer" for p in patterns)


# --- T002: recurring task rework --------------------------------------------


def test_detects_task_rework_pattern() -> None:
    per_spec = {
        "0001": [
            _entry("2026-07-01T10:00:00Z", "code-reviewer", "CHANGES_REQUESTED", task_id="T003"),
            _entry("2026-07-01T11:00:00Z", "code-reviewer", "APPROVED", task_id="T003"),
        ],
    }
    patterns = _learn.recurring_task_rework(per_spec)
    rework = [p for p in patterns if p.kind == "task-rework"]
    assert rework, "expected a task-rework pattern"
    p = rework[0]
    assert p.subject == "T003"
    assert p.occurrences == 2  # rounds
    assert p.features == ("0001",)


def test_task_without_rework_is_not_a_pattern() -> None:
    per_spec = {
        "0001": [_entry("2026-07-01T10:00:00Z", "code-reviewer", "APPROVED", task_id="T003")],
    }
    assert _learn.recurring_task_rework(per_spec) == []
