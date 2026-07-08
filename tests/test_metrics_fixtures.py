"""Sanity checks for the metrics test fixtures.

These tests do not exercise application code — they assert the fixture
trees on disk match the shape downstream tests rely on. If a fixture is
moved or its grammar drifts, this file fails first and points at the
problem before the real metric tests run.
"""

from __future__ import annotations

import json
import pathlib
import re

import pytest

FIXTURES_ROOT = pathlib.Path(__file__).parent / "fixtures" / "metrics"

_SPEC_ID_RE = re.compile(r"^\*\*Spec ID:\*\*\s*(\d+)", re.MULTILINE)
_STATUS_RE = re.compile(r"^\*\*Status:\*\*\s*([^\n<]+?)\s*(?:<!--|$)", re.MULTILINE)
_CREATED_RE = re.compile(r"^\*\*Created:\*\*\s*(\d{4}-\d{2}-\d{2})", re.MULTILINE)


def _read_header(spec_md: pathlib.Path) -> tuple[int, str, str]:
    text = spec_md.read_text(encoding="utf-8")
    spec_id_m = _SPEC_ID_RE.search(text)
    status_m = _STATUS_RE.search(text)
    created_m = _CREATED_RE.search(text)
    assert spec_id_m and status_m and created_m, f"spec.md at {spec_md} has unparseable header"
    return int(spec_id_m.group(1)), status_m.group(1).strip(), created_m.group(1)


# ---- pristine_first_pass ----------------------------------------------


def test_pristine_first_pass_has_post_cutoff_spec_with_log() -> None:
    spec_dir = FIXTURES_ROOT / "pristine_first_pass" / "specs" / "0001-x"
    spec_id, status, created = _read_header(spec_dir / "spec.md")
    assert spec_id > 10, "pristine fixture must be post-cutoff"
    assert status == "Merged"
    assert created.startswith("2026-")
    assert (spec_dir / "tasks.md").is_file()
    log = spec_dir / ".review-log.jsonl"
    assert log.is_file() and log.stat().st_size > 0


def test_pristine_log_entries_are_all_approved_first_pass() -> None:
    log = FIXTURES_ROOT / "pristine_first_pass" / "specs" / "0001-x" / ".review-log.jsonl"
    seen: dict[tuple[str, str], str] = {}
    for line in log.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        entry = json.loads(line)
        key = (entry["task_id"], entry["reviewer"])
        # In the pristine fixture, each (task, reviewer) appears once and is APPROVED.
        assert key not in seen, f"pristine fixture must have one entry per (task, reviewer); duplicate at {key}"
        seen[key] = entry["verdict"]
    assert seen, "pristine fixture must have entries"
    assert all(v == "APPROVED" for v in seen.values())


# ---- with_rework -------------------------------------------------------


def test_with_rework_has_changes_requested_then_approved() -> None:
    log = FIXTURES_ROOT / "with_rework" / "specs" / "0002-y" / ".review-log.jsonl"
    entries = [json.loads(l) for l in log.read_text(encoding="utf-8").splitlines() if l.strip()]
    # At least one task must have CHANGES_REQUESTED followed by APPROVED from the same reviewer.
    by_pair: dict[tuple[str, str], list[str]] = {}
    for e in entries:
        by_pair.setdefault((e["task_id"], e["reviewer"]), []).append(e["verdict"])
    assert any(
        verdicts[0] == "CHANGES_REQUESTED" and verdicts[-1] == "APPROVED"
        for verdicts in by_pair.values()
    ), "with_rework fixture must contain at least one CHANGES_REQUESTED → APPROVED chain"


# ---- pre_cutoff_no_log -------------------------------------------------


def test_pre_cutoff_has_no_review_log_and_low_spec_id() -> None:
    spec_dir = FIXTURES_ROOT / "pre_cutoff_no_log" / "specs" / "0001-old"
    spec_id, _, _ = _read_header(spec_dir / "spec.md")
    assert spec_id <= 10, "pre-cutoff fixture must have Spec ID ≤ 10"
    assert (spec_dir / "tasks.md").is_file()
    assert not (spec_dir / ".review-log.jsonl").exists()


# ---- empty_log ---------------------------------------------------------


def test_empty_log_fixture_has_zero_byte_log() -> None:
    log = FIXTURES_ROOT / "empty_log" / "specs" / "0003-empty" / ".review-log.jsonl"
    assert log.is_file()
    assert log.stat().st_size == 0


# ---- non_canonical_status ---------------------------------------------


def test_non_canonical_status_header_is_legacy_value() -> None:
    spec_dir = FIXTURES_ROOT / "non_canonical_status" / "specs" / "0004-pr-open"
    _, status, _ = _read_header(spec_dir / "spec.md")
    assert status == "PR Open", "fixture must carry a legacy Status value the parser has to bucket as 'other'"


# ---- coverage of all fixtures -----------------------------------------


@pytest.mark.parametrize(
    "fixture_name",
    ["pristine_first_pass", "with_rework", "pre_cutoff_no_log", "empty_log", "non_canonical_status"],
)
def test_every_fixture_root_exists(fixture_name: str) -> None:
    assert (FIXTURES_ROOT / fixture_name).is_dir(), f"missing fixture: {fixture_name}"
