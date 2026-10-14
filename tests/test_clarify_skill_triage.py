"""Clarify triage (spec 0030 T047, Story 5 sc3): cap, one at a time, recommendation."""
from __future__ import annotations

import os
import re
from pathlib import Path

ROOT = Path(os.environ.get("AIADEV_PROSE_ROOT") or Path(__file__).resolve().parents[1])
RAW = (ROOT / "skills" / "clarify" / "SKILL.md").read_text(encoding="utf-8")
TEXT = RAW.split("\n---\n", 1)[1]  # body after frontmatter


def test_caps_questions_at_five_per_session() -> None:
    assert re.search(r"(at most|max(imum)?|cap)[^\n]*\b5\b|\b5\b[^\n]*(per session|questions)", TEXT, re.I)


def test_asks_one_question_at_a_time() -> None:
    assert re.search(r"\*\*Ask one at a time\*\*", TEXT)


def test_orders_by_impact_and_uncertainty() -> None:
    assert re.search(r"impact[^\n]*uncertainty", TEXT, re.I)


def test_recommendation_accepted_with_one_word() -> None:
    assert re.search(r"one word", TEXT, re.I)
    assert "recommend" in TEXT.lower()


def test_overflow_becomes_assumptions() -> None:
    assert re.search(r"## Assumptions", TEXT)
    assert re.search(r"create it if missing", TEXT, re.I)


def test_existing_gates_kept() -> None:
    assert "## Clarifications" in TEXT
    assert "aiadev preflight clarify" in TEXT
    assert "cl-N" in TEXT
    assert re.search(r"invoke `plan`", TEXT)
    assert re.search(r"\*\*Re-grep\*\*", TEXT)
    assert re.search(r"never delete a marker without a real answer", TEXT, re.I)
