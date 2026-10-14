"""Regression tests pinning the Reconnaissance step in the specify skill (issue #26)."""
from __future__ import annotations

import pathlib
import re


def _read_specify_skill(framework_root: pathlib.Path) -> str:
    return (framework_root / "skills" / "specify" / "SKILL.md").read_text(
        encoding="utf-8"
    )


def test_specify_skill_mentions_reconnaissance(framework_root: pathlib.Path) -> None:
    """The skill prose must teach the agent about the Reconnaissance step
    so it appears before any user story is drafted (Story 1 scenario 1)."""
    text = _read_specify_skill(framework_root)
    assert "Reconnaissance" in text
    assert "<!-- section: Reconnaissance -->" in text


def test_specify_skill_forbids_analogy_drafts(framework_root: pathlib.Path) -> None:
    """Skill must call out analogy-driven drafting under 'What not to do'
    (Story 1 scenario 1, skill-prose half)."""
    text = _read_specify_skill(framework_root)
    lower = text.lower()
    assert "analogy" in lower
    assert "what not to do" in lower


def test_specify_skill_pauses_on_premise_mismatch(framework_root: pathlib.Path) -> None:
    """Story 1 scenario 2: when recon contradicts the demand's premise,
    the skill must instruct the agent to pause and surface the mismatch."""
    text = _read_specify_skill(framework_root).lower()
    assert "pause" in text
    assert "mismatch" in text


def test_specify_skill_caps_markers_and_routes_rest_to_assumptions(
    framework_root: pathlib.Path,
) -> None:
    """Spec 0030 Story 5 scenario 1: at most 3 markers (scope, security, UX
    first); remaining unknowns become impact-tagged `## Assumptions`."""
    text = _read_specify_skill(framework_root)
    assert "at most 3" in text
    assert "## Assumptions" in text
    assert "[impact:" in text
    lower = text.lower()
    for word in ("scope", "security", "ux"):
        assert word in lower


def test_specify_skill_cap_regex_order_and_split_rule(
    framework_root: pathlib.Path,
) -> None:
    """Cap is tied to the marker, priority order is scope > security > UX,
    and >3 scope/security unknowns means split the demand, not assume."""
    text = _read_specify_skill(framework_root)
    assert re.search(r"at most 3\b[^.\n]{0,60}NEEDS CLARIFICATION", text)
    assert re.search(r"scope.*security.*ux", text, re.S | re.I)
    assert re.search(r"too broad.*splitting", text, re.S | re.I)
