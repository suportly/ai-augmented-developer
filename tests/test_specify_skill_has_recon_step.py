"""Regression tests pinning the Reconnaissance step in the specify skill (issue #26)."""
from __future__ import annotations

import pathlib


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
