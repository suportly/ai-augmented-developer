"""RED tests for ``aiadev.pipeline_state.recommend_next_command``.

Covers Story 4 acceptance criteria AC-1..AC-8 from
``specs/0014-bmad-inspired-evolutions/spec.md`` plus the ≤ 200 ms
performance budget from ``plan.md``.

Spec 0030 / D6 (T028) extends it: ``feature`` slug, ``/aia:`` prefix and
branch review decided by ``.aiadev/review.yaml`` + review-log cutoff.
"""
from __future__ import annotations

import os
import runpy
import shutil
import time
from pathlib import Path

import pytest

from aiadev.pipeline_state import recommend_next_command

FIXTURES = Path(__file__).parent / "fixtures" / "pipeline_state"


# ---------------------------------------------------------------------------
# AC-1..AC-5 + AC-7 (review-pending) + AC-7 (review-approved): the eight
# state transitions, expressed as one parametrized row per acceptance
# criterion. Rows: (fixture_name, branch, expected_command_substring).
# ---------------------------------------------------------------------------

PIPELINE_STATE_CASES = [
    # AC-1: empty specs/ → /aia:specify
    ("empty", "feature/x", "/aia:specify"),
    # AC-2: spec with cl-N marker → /aia:clarify
    ("draft_spec", "feature/x", "/aia:clarify"),
    # AC-3: spec clean, no plan → /aia:plan
    ("clarified_spec", "feature/x", "/aia:plan"),
    # AC-4: spec + plan, no tasks → /aia:tasks
    ("planned", "feature/x", "/aia:tasks"),
    # AC-5: spec + plan + tasks with pending statuses → /aia:implement
    ("tasked", "feature/x", "/aia:implement"),
    # AC-5 variant: at least one pending task → still /aia:implement
    ("half_done", "feature/x", "/aia:implement"),
    # AC-7: all tasks done, no review log → /aia:requesting-code-review
    ("all_done", "feature/x", "/aia:requesting-code-review"),
    # AC-7: all done, review log last entry APPROVED but missing
    # has_why_no_issues_block → still /aia:requesting-code-review
    ("review_pending", "feature/x", "/aia:requesting-code-review"),
    # AC-7 (D6): review.yaml approved and not older than the log →
    # /aia:finishing-a-branch (fixture gets its review.yaml in tmp)
    ("review_approved", "feature/x", "/aia:finishing-a-branch"),
]
APPROVED_AT = '2026-05-13T12:00:00Z'  # after the fixture log's last entry


def _with_review(tmp_path: Path, fixture: str, review_yaml: str | None) -> Path:
    """Copy ``fixture`` to tmp and write ``.aiadev/review.yaml`` (gitignored dir)."""
    workspace = tmp_path / "ws"
    shutil.copytree(FIXTURES / fixture, workspace)
    if review_yaml is not None:
        (workspace / ".aiadev").mkdir()
        (workspace / ".aiadev" / "review.yaml").write_text(review_yaml, encoding="utf-8")
    return workspace



@pytest.mark.parametrize(
    "fixture_name, branch, expected_command",
    PIPELINE_STATE_CASES,
    ids=[row[0] for row in PIPELINE_STATE_CASES],
)
def test_recommend_next_command_for_pipeline_state(
    fixture_name: str, branch: str, expected_command: str, tmp_path: Path
) -> None:
    workspace = FIXTURES / fixture_name
    if fixture_name == "review_approved":
        review = f"status: approved\ntimestamp: \"{APPROVED_AT}\"\n"
        workspace = _with_review(tmp_path, fixture_name, review)

    result = recommend_next_command(workspace, branch=branch)

    assert isinstance(result, dict), f"expected dict, got {type(result).__name__}"
    assert "command" in result, f"missing 'command' key in {result!r}"
    assert "reason" in result, f"missing 'reason' key in {result!r}"
    assert result["command"] == expected_command, (
        f"fixture {fixture_name!r}: expected {expected_command!r}, got {result['command']!r}"
    )


# ---------------------------------------------------------------------------
# AC-8: branch-scoped — orphan specs (other branches) ignored. The
# orphan_branch fixture has 0001-x on feature/x and 0002-y on feature/y.
# When branch=feature/x, only 0001-x must drive the recommendation.
# ---------------------------------------------------------------------------


def test_orphan_branch_specs_are_ignored_when_scoping_by_current_branch() -> None:
    workspace = FIXTURES / "orphan_branch"

    result_x = recommend_next_command(workspace, branch="feature/x")
    result_y = recommend_next_command(workspace, branch="feature/y")

    # 0001-x is a clean approved spec with no plan → /aia:plan
    assert result_x["command"] == "/aia:plan", (
        f"branch feature/x should recommend /aia:plan based on 0001-x only, got {result_x!r}"
    )
    # 0002-y is also a clean approved spec with no plan → /aia:plan
    # (different spec dir, but same state class). The point is the
    # recommendation must be derived from the y-spec, not bleed across.
    assert result_y["command"] == "/aia:plan", (
        f"branch feature/y should recommend /aia:plan based on 0002-y only, got {result_y!r}"
    )


# ---------------------------------------------------------------------------
# Performance budget: ≤ 200 ms over a 50-spec corpus. The fixture is
# generated on demand by ``_generate_perf.py`` (its specs/ tree is
# gitignored). A session-scoped fixture runs the generator once.
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def perf_fixture_populated() -> Path:
    perf_dir = FIXTURES / "perf_50_specs"
    generator = perf_dir / "_generate_perf.py"

    runpy.run_path(str(generator), run_name="__main__")

    specs_dir = perf_dir / "specs"
    assert specs_dir.is_dir(), f"perf generator failed to create {specs_dir}"
    populated = list(specs_dir.glob("*/spec.md"))
    assert len(populated) == 50, f"expected 50 spec.md files, got {len(populated)}"
    return perf_dir


@pytest.mark.perf
def test_recommend_next_command_meets_200ms_budget_on_50_specs(
    perf_fixture_populated: Path,
) -> None:
    workspace = perf_fixture_populated

    start = time.perf_counter()
    result = recommend_next_command(workspace, branch="feature/x1")
    duration = time.perf_counter() - start

    assert isinstance(result, dict), f"expected dict, got {type(result).__name__}"
    assert duration < 0.200, (
        f"recommend_next_command took {duration * 1000:.1f} ms; budget is 200 ms"
    )


# ---------------------------------------------------------------------------
# T028 / D6: feature slug, plain removed, review.yaml cutoff.
# ---------------------------------------------------------------------------


def test_feature_slug_selects_spec_dir_instead_of_branch_or_mtime() -> None:
    workspace = FIXTURES / "orphan_branch"

    result = recommend_next_command(workspace, feature="0002-y")

    assert result["command"] == "/aia:plan", result
    assert "0002-y" in result["reason"] or "plan" in result["reason"]


def test_feature_slug_wins_over_branch() -> None:
    workspace = FIXTURES / "draft_spec"

    result = recommend_next_command(workspace, branch="feature/other", feature="0001-x")

    assert result["command"] == "/aia:clarify", result


def test_unknown_feature_slug_recommends_specify_without_raising() -> None:
    result = recommend_next_command(FIXTURES / "planned", feature="0099-nope")

    assert result["command"] == "/aia:specify", result
    assert "0099-nope" in result["reason"]
    assert "spec" in result["reason"]


@pytest.mark.parametrize("slug", ["../all_done", "..", "../specs/0001-x", "0001-x/.."])
def test_feature_slug_cannot_escape_specs_dir(tmp_path: Path, slug: str) -> None:
    # Every slug below resolves to a complete spec tree without the guard.
    src = FIXTURES / "all_done" / "specs" / "0001-x"
    ws = tmp_path / "ws"
    shutil.copytree(src, ws / "specs" / "0001-x")
    shutil.copytree(src, ws / "all_done")
    for item in src.iterdir():  # complete spec also at the workspace root
        shutil.copy(item, ws / item.name)

    result = recommend_next_command(ws, feature=slug)

    assert result["command"] == "/aia:specify", result


def test_unreadable_spec_dir_is_a_real_error(tmp_path: Path) -> None:
    ws = tmp_path / "ws"
    spec = ws / "specs" / "0001-x"
    spec.mkdir(parents=True)
    (spec / "spec.md").write_text("# s\n", encoding="utf-8")
    spec.chmod(0)
    try:
        if os.access(spec, os.R_OK):  # running as root: cannot simulate
            pytest.skip("permissions not enforced")
        with pytest.raises(OSError):
            recommend_next_command(ws, feature="0001-x")
    finally:
        spec.chmod(0o755)


def test_plain_mode_is_gone(monkeypatch: pytest.MonkeyPatch) -> None:
    # The retired plain-mode switch must stay inert.
    monkeypatch.setenv("AIADEV_HELP_PLAIN", "1")

    result = recommend_next_command(FIXTURES / "draft_spec", branch="feature/x")

    assert result["command"] == "/aia:clarify", result
    with pytest.raises(TypeError):
        recommend_next_command(FIXTURES / "draft_spec", plain=True)  # type: ignore[call-arg]


def test_stale_review_yaml_does_not_reach_finishing(tmp_path: Path) -> None:
    review = (FIXTURES / "review_yaml_stale" / "dot-aiadev" / "review.yaml").read_text()
    workspace = tmp_path / "ws"
    shutil.copytree(FIXTURES / "review_yaml_stale", workspace)
    (workspace / ".aiadev").mkdir()
    (workspace / ".aiadev" / "review.yaml").write_text(review, encoding="utf-8")

    result = recommend_next_command(workspace, feature="0001-x")

    assert result["command"] == "/aia:requesting-code-review", result


@pytest.mark.parametrize(
    "review_yaml, expected",
    [
        # newer, offset form, unquoted (yaml parses to datetime) → approved
        ("status: approved\ntimestamp: 2026-05-20T10:00:00+00:00\n", "/aia:finishing-a-branch"),
        # same instant as last log entry (09:00Z) written with an offset → approved
        ("status: approved\ntimestamp: '2026-05-20T06:00:00-03:00'\n", "/aia:finishing-a-branch"),
        # lexically larger string but earlier instant: datetime compare, not string
        ("status: approved\ntimestamp: '2026-05-20T05:00:00-03:00'\n", "/aia:requesting-code-review"),
        ("status: approved\n", "/aia:requesting-code-review"),
        ("status: approved\ntimestamp: not-a-date\n", "/aia:requesting-code-review"),
        ("status: rejected\ntimestamp: '2026-05-21T00:00:00Z'\n", "/aia:requesting-code-review"),
        (None, "/aia:requesting-code-review"),
    ],
    ids=["offset-newer", "equal-instant", "string-trap", "no-ts", "bad-ts", "rejected", "no-file"],
)
def test_review_yaml_cutoff_against_last_log_entry(
    tmp_path: Path, review_yaml: str | None, expected: str
) -> None:
    workspace = tmp_path / "ws"
    shutil.copytree(FIXTURES / "review_yaml_stale", workspace)
    if review_yaml is not None:
        (workspace / ".aiadev").mkdir()
        (workspace / ".aiadev" / "review.yaml").write_text(review_yaml, encoding="utf-8")

    result = recommend_next_command(workspace, feature="0001-x")

    assert result["command"] == expected, result


def test_feature_without_log_entries_has_no_cutoff(tmp_path: Path) -> None:
    # Known edge (same as the finishing-a-branch preflight): no log, no cutoff.
    workspace = _with_review(
        tmp_path, "all_done", "status: approved\ntimestamp: '2000-01-01T00:00:00Z'\n"
    )

    result = recommend_next_command(workspace, feature="0001-x")

    assert result["command"] == "/aia:finishing-a-branch", result


def test_log_entries_without_parseable_timestamp_fail_closed(tmp_path: Path) -> None:
    ws = _with_review(
        tmp_path, "all_done", "status: approved\ntimestamp: '2030-01-01T00:00:00Z'\n"
    )
    log = ws / "specs" / "0001-x" / ".review-log.jsonl"
    log.write_text('{"verdict": "APPROVED"}\n{"timestamp": "garbage"}\n', encoding="utf-8")

    result = recommend_next_command(ws, feature="0001-x")

    assert result["command"] == "/aia:requesting-code-review", result


@pytest.mark.parametrize("target", ["review.yaml", "log"])
def test_undecodable_review_files_fail_closed(tmp_path: Path, target: str) -> None:
    ws = _with_review(
        tmp_path, "review_approved", "status: approved\ntimestamp: '2030-01-01T00:00:00Z'\n"
    )
    if target == "review.yaml":
        (ws / ".aiadev" / "review.yaml").write_bytes(b"status: approved\n\xff\xfe")
    else:
        (ws / "specs" / "0001-x" / ".review-log.jsonl").write_bytes(b'{"a": 1}\n\xff\n')

    result = recommend_next_command(ws, feature="0001-x")

    assert result["command"] == "/aia:requesting-code-review", result
