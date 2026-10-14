"""Synthetic review-log: single reviewer verdicts feed ``aiadev metrics``.

Spec 0030 (T032, Story 3 sc5): one CHANGES_REQUESTED followed by APPROVED
for the same task counts as one rework and a failed first pass.
"""
from __future__ import annotations

import json
from pathlib import Path

from aiadev import metrics


def _log(tmp_path: Path, rows: list[tuple[str, str, str]]) -> list[dict]:
    path = tmp_path / ".review-log.jsonl"
    with path.open("w", encoding="utf-8") as fh:
        for ts, task, verdict in rows:
            fh.write(json.dumps({
                "timestamp": ts, "reviewer": "code-reviewer", "verdict": verdict,
                "has_why_no_issues_block": verdict == "APPROVED", "task_id": task,
            }) + "\n")
    return metrics.read_review_log(path)


def test_changes_requested_then_approved_counts_one_rework(tmp_path: Path) -> None:
    entries = _log(tmp_path, [
        ("2026-10-01T10:00:00Z", "T001", "CHANGES_REQUESTED"),
        ("2026-10-01T11:00:00Z", "T001", "APPROVED"),
        ("2026-10-01T12:00:00Z", "T002", "APPROVED"),
    ])
    assert metrics.task_rework_counts(entries) == [("T001", 2, 1)]
    assert metrics.first_pass_rate_by_reviewer(entries) == {"code-reviewer": (1, 2)}
    assert metrics.tasks_reached_review(entries) == 2
