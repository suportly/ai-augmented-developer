"""RED tests for ``aiadev.review_log``.

Covers Story 3 acceptance criteria AC-1..AC-4 from
``specs/0014-bmad-inspired-evolutions/spec.md`` plus the cl-5 definition
of "non-trivial change":

  > ``git diff --shortstat --ignore-blank-lines`` reports > 10 changed
  > lines, EXCLUDING files with extension ``.md``, ``.json``, ``.lock``,
  > ``.toml`` and files under ``docs/``. Spec/plan creation (any diff
  > under ``specs/<branch>/{spec,plan}.md``) is ALWAYS non-trivial.

The module ``aiadev.review_log`` does not exist yet — every test in this
file MUST fail at import time with ``ModuleNotFoundError`` until T007
lands. See ``.claude/rules/testing.md``: write the test first.

Public API pinned by these tests (T007 GREEN must honour):

    is_non_trivial_change(diff_shortstat: str | dict, paths: list[str]) -> bool
    append_review_entry(workspace_path: Path, entry: dict) -> None
    last_review_entry(workspace_path: Path) -> dict | None

JSONL location: ``<workspace>/specs/<branch>/.review-log.jsonl``. The
branch is derived from the single child directory under ``specs/`` for
the workspace under test (the test fixtures pin a single branch slug).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from aiadev.review_log import (  # noqa: E402  RED: module does not exist yet
    append_review_entry,
    is_non_trivial_change,
    last_review_entry,
)

FIXTURES = Path(__file__).parent / "fixtures" / "review_log"


def _load_fixture(name: str) -> tuple[str, list[str]]:
    """Read ``shortstat.txt`` + ``paths.txt`` for a fixture directory."""
    fixture_dir = FIXTURES / name
    shortstat = (fixture_dir / "shortstat.txt").read_text(encoding="utf-8").strip()
    paths_text = (fixture_dir / "paths.txt").read_text(encoding="utf-8")
    paths = [line for line in paths_text.splitlines() if line.strip()]
    return shortstat, paths


# ---------------------------------------------------------------------------
# Detector tests: is_non_trivial_change
# ---------------------------------------------------------------------------

DETECTOR_FIXTURE_CASES = [
    # cl-5: 7 LOC (5 ins + 2 del) in src/ → ≤ 10 → trivial
    ("trivial_diff", False),
    # cl-5: 33 LOC across src/ + tests/ → > 10 and not excluded → non-trivial
    ("nontrivial_diff", True),
    # cl-5 override: spec.md creation under specs/<branch>/ → always non-trivial
    ("spec_creation", True),
    # cl-5: 50 LOC but ALL paths excluded (docs/ + .md) → trivial
    ("markdown_only_change", False),
]


@pytest.mark.parametrize(
    "fixture_name, expected_non_trivial",
    DETECTOR_FIXTURE_CASES,
    ids=[row[0] for row in DETECTOR_FIXTURE_CASES],
)
def test_is_non_trivial_change_for_fixture(
    fixture_name: str, expected_non_trivial: bool
) -> None:
    shortstat, paths = _load_fixture(fixture_name)

    result = is_non_trivial_change(shortstat, paths)

    assert result is expected_non_trivial, (
        f"fixture {fixture_name!r}: shortstat={shortstat!r} paths={paths!r}; "
        f"expected {expected_non_trivial}, got {result!r}"
    )


def test_is_non_trivial_change_returns_false_for_empty_paths() -> None:
    shortstat = " 1 file changed, 50 insertions(+)"
    paths: list[str] = []

    result = is_non_trivial_change(shortstat, paths)

    assert result is False, (
        f"empty paths must be treated as trivial (no diff to review), got {result!r}"
    )


# Boundary cases live outside the fixture loop to keep each side of the
# threshold readable in isolation. Both use code-only paths so the cl-5
# exclusions do not muddy the LOC count.
BOUNDARY_CASES = [
    # 10 LOC = boundary, NOT > 10 → trivial
    (" 1 file changed, 7 insertions(+), 3 deletions(-)", ["src/aiadev/cli.py"], False),
    # 11 LOC = first non-trivial integer above the threshold
    (" 1 file changed, 8 insertions(+), 3 deletions(-)", ["src/aiadev/cli.py"], True),
]


@pytest.mark.parametrize(
    "shortstat, paths, expected_non_trivial",
    BOUNDARY_CASES,
    ids=["boundary_exactly_10_loc", "boundary_11_loc"],
)
def test_is_non_trivial_change_threshold_boundary(
    shortstat: str, paths: list[str], expected_non_trivial: bool
) -> None:
    result = is_non_trivial_change(shortstat, paths)

    assert result is expected_non_trivial, (
        f"shortstat={shortstat!r} paths={paths!r}: "
        f"expected {expected_non_trivial}, got {result!r}"
    )


# ---------------------------------------------------------------------------
# Writer tests: append_review_entry
# ---------------------------------------------------------------------------


def _make_branch_dir(workspace: Path, branch_slug: str = "0001-x") -> Path:
    """Create ``<workspace>/specs/<branch_slug>/`` and return its path."""
    branch_dir = workspace / "specs" / branch_slug
    branch_dir.mkdir(parents=True)
    return branch_dir


def test_append_review_entry_creates_jsonl_in_fresh_workspace(tmp_path: Path) -> None:
    branch_dir = _make_branch_dir(tmp_path)
    entry = {
        "timestamp": "2026-05-13T10:00:00Z",
        "reviewer": "code-reviewer",
        "verdict": "APPROVED",
        "has_why_no_issues_block": True,
        "task_id": "T006",
    }

    append_review_entry(tmp_path, entry)

    log_path = branch_dir / ".review-log.jsonl"
    assert log_path.is_file(), f"expected {log_path} to be created"
    written = log_path.read_text(encoding="utf-8").splitlines()
    assert len(written) == 1, f"expected one line, got {len(written)}: {written!r}"
    assert json.loads(written[0]) == entry, (
        f"round-trip mismatch: read back {written[0]!r}, expected {entry!r}"
    )


def test_append_review_entry_preserves_prior_entries(tmp_path: Path) -> None:
    branch_dir = _make_branch_dir(tmp_path)
    first = {
        "timestamp": "2026-05-13T10:00:00Z",
        "reviewer": "code-reviewer",
        "verdict": "CHANGES_REQUESTED",
        "has_why_no_issues_block": False,
        "task_id": "T006",
    }
    second = {
        "timestamp": "2026-05-13T11:00:00Z",
        "reviewer": "code-reviewer",
        "verdict": "APPROVED",
        "has_why_no_issues_block": True,
        "task_id": "T006",
    }

    append_review_entry(tmp_path, first)
    append_review_entry(tmp_path, second)

    log_path = branch_dir / ".review-log.jsonl"
    lines = log_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2, f"expected 2 lines after two appends, got {len(lines)}"
    assert json.loads(lines[0]) == first, "first entry must be preserved verbatim"
    assert json.loads(lines[1]) == second, "second entry must be appended after the first"


def test_append_review_entry_raises_when_branch_dir_missing(tmp_path: Path) -> None:
    # Deliberately do NOT create specs/<branch>/ — append must not silently
    # invent a branch directory; the caller owns spec/branch lifecycle.
    entry = {
        "timestamp": "2026-05-13T10:00:00Z",
        "reviewer": "code-reviewer",
        "verdict": "APPROVED",
        "has_why_no_issues_block": True,
        "task_id": "T006",
    }

    with pytest.raises(FileNotFoundError):
        append_review_entry(tmp_path, entry)


# ---------------------------------------------------------------------------
# Reader tests: last_review_entry
# ---------------------------------------------------------------------------


def test_last_review_entry_returns_last_of_three(tmp_path: Path) -> None:
    branch_dir = _make_branch_dir(tmp_path)
    entries = [
        {
            "timestamp": "2026-05-13T10:00:00Z",
            "reviewer": "code-reviewer",
            "verdict": "CHANGES_REQUESTED",
            "has_why_no_issues_block": False,
            "task_id": "T001",
        },
        {
            "timestamp": "2026-05-13T10:30:00Z",
            "reviewer": "spec-document-reviewer",
            "verdict": "APPROVED",
            "has_why_no_issues_block": True,
            "task_id": "T002",
        },
        {
            "timestamp": "2026-05-13T11:00:00Z",
            "reviewer": "code-reviewer",
            "verdict": "APPROVED",
            "has_why_no_issues_block": True,
            "task_id": "T003",
        },
    ]
    log_path = branch_dir / ".review-log.jsonl"
    log_path.write_text(
        "\n".join(json.dumps(e) for e in entries) + "\n", encoding="utf-8"
    )

    result = last_review_entry(tmp_path)

    assert result == entries[-1], (
        f"expected last entry {entries[-1]!r}, got {result!r}"
    )


def test_last_review_entry_returns_none_when_file_missing(tmp_path: Path) -> None:
    _make_branch_dir(tmp_path)  # branch exists, but no .review-log.jsonl yet

    result = last_review_entry(tmp_path)

    assert result is None, f"missing log must return None, got {result!r}"


def test_last_review_entry_returns_none_for_empty_file(tmp_path: Path) -> None:
    branch_dir = _make_branch_dir(tmp_path)
    (branch_dir / ".review-log.jsonl").write_text("", encoding="utf-8")

    result = last_review_entry(tmp_path)

    assert result is None, f"empty log must return None, got {result!r}"


def test_last_review_entry_skips_malformed_lines(tmp_path: Path) -> None:
    branch_dir = _make_branch_dir(tmp_path)
    valid_first = {
        "timestamp": "2026-05-13T10:00:00Z",
        "reviewer": "code-reviewer",
        "verdict": "APPROVED",
        "has_why_no_issues_block": True,
        "task_id": "T001",
    }
    valid_second = {
        "timestamp": "2026-05-13T11:00:00Z",
        "reviewer": "spec-document-reviewer",
        "verdict": "APPROVED",
        "has_why_no_issues_block": True,
        "task_id": "T002",
    }
    log_path = branch_dir / ".review-log.jsonl"
    log_path.write_text(
        json.dumps(valid_first) + "\n"
        + "{ this is not valid json,,,\n"
        + json.dumps(valid_second) + "\n"
        + "another garbage line\n",
        encoding="utf-8",
    )

    result = last_review_entry(tmp_path)

    assert result == valid_second, (
        f"reader must skip malformed lines and return last VALID entry "
        f"{valid_second!r}, got {result!r}"
    )
