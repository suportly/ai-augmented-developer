"""RED tests for ``aiadev.pipeline_state.recommend_next_command``.

Covers Story 4 acceptance criteria AC-1..AC-8 from
``specs/0014-bmad-inspired-evolutions/spec.md`` plus the ≤ 200 ms
performance budget from ``plan.md``.

The module ``aiadev.pipeline_state`` does not exist yet — every test in
this file MUST fail at import time with ``ModuleNotFoundError`` until
T003 lands. See ``.claude/rules/testing.md``: write the test first.
"""
from __future__ import annotations

import os
import runpy
import time
from pathlib import Path

import pytest

from aiadev.pipeline_state import recommend_next_command  # noqa: E402  RED: module does not exist yet

FIXTURES = Path(__file__).parent / "fixtures" / "pipeline_state"


# ---------------------------------------------------------------------------
# AC-1..AC-5 + AC-7 (review-pending) + AC-7 (review-approved): the eight
# state transitions, expressed as one parametrized row per acceptance
# criterion. Rows: (fixture_name, branch, expected_command_substring).
# ---------------------------------------------------------------------------

PIPELINE_STATE_CASES = [
    # AC-1: empty specs/ → /aiadev:specify
    ("empty", "feature/x", "/aiadev:specify"),
    # AC-2: spec with cl-N marker → /aiadev:clarify
    ("draft_spec", "feature/x", "/aiadev:clarify"),
    # AC-3: spec clean, no plan → /aiadev:plan
    ("clarified_spec", "feature/x", "/aiadev:plan"),
    # AC-4: spec + plan, no tasks → /aiadev:tasks
    ("planned", "feature/x", "/aiadev:tasks"),
    # AC-5: spec + plan + tasks with pending statuses → /aiadev:implement
    ("tasked", "feature/x", "/aiadev:implement"),
    # AC-5 variant: at least one pending task → still /aiadev:implement
    ("half_done", "feature/x", "/aiadev:implement"),
    # AC-7: all tasks done, no review log → /aiadev:requesting-code-review
    ("all_done", "feature/x", "/aiadev:requesting-code-review"),
    # AC-7: all done, review log last entry APPROVED but missing
    # has_why_no_issues_block → still /aiadev:requesting-code-review
    ("review_pending", "feature/x", "/aiadev:requesting-code-review"),
    # AC-7: all done, review log last entry APPROVED with
    # has_why_no_issues_block=true → /aiadev:finishing-a-branch
    ("review_approved", "feature/x", "/aiadev:finishing-a-branch"),
]


@pytest.mark.parametrize(
    "fixture_name, branch, expected_command",
    PIPELINE_STATE_CASES,
    ids=[row[0] for row in PIPELINE_STATE_CASES],
)
def test_recommend_next_command_for_pipeline_state(
    fixture_name: str, branch: str, expected_command: str
) -> None:
    workspace = FIXTURES / fixture_name

    result = recommend_next_command(workspace, branch=branch)

    assert isinstance(result, dict), f"expected dict, got {type(result).__name__}"
    assert "command" in result, f"missing 'command' key in {result!r}"
    assert "reason" in result, f"missing 'reason' key in {result!r}"
    assert result["command"] == expected_command, (
        f"fixture {fixture_name!r}: expected {expected_command!r}, got {result['command']!r}"
    )


# ---------------------------------------------------------------------------
# AC-6: --plain / AIADEV_HELP_PLAIN=1 opt-out — logic-only, no fixture
# inspection. The function returns a sentinel with command=None.
# ---------------------------------------------------------------------------


def test_recommends_nothing_when_plain_mode_kwarg_set() -> None:
    workspace = FIXTURES / "draft_spec"  # would normally trigger /aiadev:clarify

    result = recommend_next_command(workspace, branch="feature/x", plain=True)

    assert result["command"] is None, f"plain mode must return command=None, got {result!r}"
    assert "reason" in result, f"plain mode must still expose a 'reason', got {result!r}"


def test_recommends_nothing_when_plain_env_var_set(monkeypatch: pytest.MonkeyPatch) -> None:
    workspace = FIXTURES / "draft_spec"
    monkeypatch.setenv("AIADEV_HELP_PLAIN", "1")

    result = recommend_next_command(workspace, branch="feature/x")

    assert result["command"] is None, (
        f"AIADEV_HELP_PLAIN=1 must return command=None, got {result!r}"
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

    # 0001-x is a clean approved spec with no plan → /aiadev:plan
    assert result_x["command"] == "/aiadev:plan", (
        f"branch feature/x should recommend /aiadev:plan based on 0001-x only, got {result_x!r}"
    )
    # 0002-y is also a clean approved spec with no plan → /aiadev:plan
    # (different spec dir, but same state class). The point is the
    # recommendation must be derived from the y-spec, not bleed across.
    assert result_y["command"] == "/aiadev:plan", (
        f"branch feature/y should recommend /aiadev:plan based on 0002-y only, got {result_y!r}"
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


# Belt-and-suspenders: exercise the AIADEV_HELP_PLAIN=0 (off) path so an
# accidentally-set env var in the developer shell does not hide failures
# elsewhere. Not a spec AC, but cheap insurance for the parametrized run.
def test_plain_env_var_off_does_not_short_circuit(monkeypatch: pytest.MonkeyPatch) -> None:
    workspace = FIXTURES / "draft_spec"
    monkeypatch.setenv("AIADEV_HELP_PLAIN", "0")

    result = recommend_next_command(workspace, branch="feature/x")

    assert result["command"] == "/aiadev:clarify", (
        f"AIADEV_HELP_PLAIN=0 must NOT bypass detection, got {result!r}"
    )

    # Sanity: clean up via monkeypatch's auto-undo at teardown — no manual os.environ pop.
    assert os.environ.get("AIADEV_HELP_PLAIN") == "0"
