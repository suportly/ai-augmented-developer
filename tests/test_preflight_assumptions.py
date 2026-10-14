"""Optional `## Assumptions` validation in preflight (spec 0030, T045)."""
from __future__ import annotations

import pathlib

import pytest

from aiadev.preflight import SPEC_ANCHORS, check

_BASE = (
    "# Feature\n\n**Branch:** `feature/x`\n**Language:** en\n\n"
    + "".join(f"<!-- section: {a} -->\n## {a}\n\nx\n\n" for a in SPEC_ANCHORS)
)


def _run(tmp_path: pathlib.Path, extra: str, skill: str = "plan", env=None):
    root = tmp_path / "specs" / "0001-x"
    root.mkdir(parents=True, exist_ok=True)
    (root / "spec.md").write_text(_BASE + extra, encoding="utf-8")
    return check(skill, root, env=env or {}, current_branch=lambda: "feature/x")


def _msgs(issues) -> list[str]:
    return [i.message for i in issues]


def test_spec_without_assumptions_stays_valid(tmp_path: pathlib.Path) -> None:
    assert _run(tmp_path, "") == []


def test_assumptions_is_not_a_required_anchor() -> None:
    assert "Assumptions" not in SPEC_ANCHORS


def test_valid_assumptions_pass(tmp_path: pathlib.Path) -> None:
    extra = "## Assumptions\n\n- Uses UTC. [impact: low]\n- Retries 3x [impact: medium]\n"
    assert _run(tmp_path, extra) == []


@pytest.mark.parametrize(
    "bullet",
    ["- Uses UTC.", "-", "- [impact: low]", "- Uses UTC [impact: high]", "- X [impact: huge]"],
)
def test_bad_assumption_is_flagged(tmp_path: pathlib.Path, bullet: str) -> None:
    extra = f"## Assumptions\n\n- ok [impact: low]\n{bullet}\n"
    msgs = _msgs(_run(tmp_path, extra))
    assert msgs == [
        "pre-flight: spec.md Assumptions item 2 lacks [impact: low|medium]"
    ]


def test_section_in_code_fence_is_ignored(tmp_path: pathlib.Path) -> None:
    extra = "```\n## Assumptions\n\n- no marker\n```\n"
    assert _run(tmp_path, extra) == []


def test_section_ends_at_next_heading(tmp_path: pathlib.Path) -> None:
    extra = "## Assumptions\n\n- ok [impact: low]\n\n## Other\n\n- no marker\n"
    assert _run(tmp_path, extra) == []


def test_warn_downgrades(tmp_path: pathlib.Path) -> None:
    issues = _run(
        tmp_path, "## Assumptions\n\n- bad\n", env={"AIADEV_PREFLIGHT": "warn"}
    )
    assert issues and all(not i.would_abort for i in issues)


def test_specify_and_clarify_unaffected(tmp_path: pathlib.Path) -> None:
    extra = "## Assumptions\n\n- bad\n"
    assert _run(tmp_path, extra, skill="specify") == []
    assert _run(tmp_path, extra, skill="clarify") == []
