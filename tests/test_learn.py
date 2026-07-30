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


def _task_reworked(task_id: str = "T003"):
    return [
        _entry("2026-07-01T10:00:00Z", "code-reviewer", "CHANGES_REQUESTED", task_id=task_id),
        _entry("2026-07-01T11:00:00Z", "code-reviewer", "APPROVED", task_id=task_id),
    ]


def test_detects_task_rework_pattern() -> None:
    # Same task reworked across two features → a recurring, sufficient pattern.
    per_spec = {"0001": _task_reworked("T003"), "0002": _task_reworked("T003")}
    patterns = _learn.recurring_task_rework(per_spec)
    rework = [p for p in patterns if p.kind == "task-rework"]
    assert rework, "expected a task-rework pattern"
    p = rework[0]
    assert p.subject == "T003"
    assert p.occurrences == 2  # features
    assert p.features == ("0001", "0002")
    assert p.sufficient is True


def test_single_feature_rework_is_insufficient() -> None:
    # Reworked in only one feature → not a recurring pattern (Story 3 sc2).
    per_spec = {"0001": _task_reworked("T003")}
    patterns = _learn.recurring_task_rework(per_spec, min_features=2)
    p = next(p for p in patterns if p.subject == "T003")
    assert p.sufficient is False


def test_task_without_rework_is_not_a_pattern() -> None:
    per_spec = {
        "0001": [_entry("2026-07-01T10:00:00Z", "code-reviewer", "APPROVED", task_id="T003")],
    }
    assert _learn.recurring_task_rework(per_spec) == []


# --- T003: evidence threshold -----------------------------------------------


def test_thin_trail_marks_insufficient_evidence() -> None:
    # Only one feature where the reviewer failed → below the default threshold.
    per_spec = {
        "0001": _spec_where_reviewer_fails_first_pass("plan-document-reviewer"),
    }
    patterns = _learn.recurring_reviewer_failures(per_spec, min_features=2)
    p = next(p for p in patterns if p.subject == "plan-document-reviewer")
    assert p.sufficient is False


def test_meets_threshold_is_sufficient() -> None:
    per_spec = {
        "0001": _spec_where_reviewer_fails_first_pass("plan-document-reviewer"),
        "0002": _spec_where_reviewer_fails_first_pass("plan-document-reviewer"),
    }
    patterns = _learn.recurring_reviewer_failures(per_spec, min_features=2)
    p = next(p for p in patterns if p.subject == "plan-document-reviewer")
    assert p.sufficient is True


# --- T004: reviewer prose excluded by default (Article VI) ------------------


def test_bodies_excluded_by_default() -> None:
    per_spec = {
        "0001": _spec_where_reviewer_fails_first_pass("plan-document-reviewer", note="secret prose"),
        "0002": _spec_where_reviewer_fails_first_pass("plan-document-reviewer", note="secret prose"),
    }
    default = _learn.recurring_reviewer_failures(per_spec)
    p = next(p for p in default if p.subject == "plan-document-reviewer")
    assert p.notes == ()  # no reviewer prose by default

    shown = _learn.recurring_reviewer_failures(per_spec, show_bodies=True)
    p2 = next(p for p in shown if p.subject == "plan-document-reviewer")
    assert "secret prose" in p2.notes


# --- T009: each sufficient pattern carries a reviewable proposal -------------


def test_pattern_carries_proposal_and_target() -> None:
    per_spec = {
        "0001": _spec_where_reviewer_fails_first_pass("plan-document-reviewer"),
        "0002": _spec_where_reviewer_fails_first_pass("plan-document-reviewer"),
    }
    patterns = _learn.detect_all(per_spec)
    p = next(p for p in patterns if p.subject == "plan-document-reviewer")
    assert p.proposal is not None
    # A target is either a rule file or a checklist category (spec 0021);
    # asserting the union keeps this test honest if the reviewer→category
    # map grows to cover this reviewer.
    target = p.proposal.target_file
    assert target.startswith("rules/") or target.startswith("checklist:")
    assert "constitution" not in target  # cl-3: never the constitution
    assert p.proposal.snippet.strip()


def test_insufficient_pattern_has_no_proposal() -> None:
    per_spec = {
        "0001": _spec_where_reviewer_fails_first_pass("plan-document-reviewer"),
    }
    patterns = _learn.detect_all(per_spec, min_features=2)
    p = next(p for p in patterns if p.subject == "plan-document-reviewer")
    assert p.sufficient is False
    assert p.proposal is None
