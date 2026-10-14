"""Behaviour tests for the ``implement`` skill's task-context integration.

Spec: ``specs/0014-bmad-inspired-evolutions/spec.md`` Story 1 sc2 and sc3.
Rewritten by spec 0030 (T037) to assert behaviour instead of layout: the
integration may live in ``skills/implement/SKILL.md`` or in a
``references/*.md`` file it cites. The "effective text" is the SKILL.md
plus the cited references (helper shared with
``tests/test_review_redispatch_skills.py``). Set ``AIADEV_PROSE_ROOT`` to
point at a copy of the repo text.

- sc2: with the preset flag or CLI flag, the implementer gets a SHORT
  prompt that points at the composed per-task file by path.
- sc3: without them, the inline implementer prompt is unchanged.
"""
from __future__ import annotations

import re

from tests.test_review_redispatch_skills import effective_text

SKILL = "skills/implement/SKILL.md"


def _text() -> str:
    return effective_text(SKILL)


def test_opt_in_triggers_documented() -> None:
    """sc2/sc3: preset flag AND preflight CLI flag are both documented."""
    text = _text()
    assert "task_context: true" in text
    assert "--task-context" in text
    assert "preset.yaml" in text


def test_integration_invokes_compose_and_names_skill() -> None:
    """The brief is composed (aiadev.task_context compose) before dispatch,
    and the task-context skill is named. Dropped: the literal section
    heading assertion; it fixed layout, and this one proves the content
    is reachable from implement wherever it lives."""
    text = _text()
    assert "aiadev.task_context" in text
    assert re.search(r"\bcompose\b", text)
    assert "task-context" in text


def test_active_prompt_points_at_file_and_reads_it_first() -> None:
    """sc2: the short prompt references the composed file by path and
    tells the implementer to read it first."""
    text = _text()
    assert "task-context/" in text
    assert re.search(r"read it first", text, re.I)


def test_staleness_check_documented() -> None:
    """A fresh brief is reused across retries (is_stale)."""
    assert "is_stale" in _text()


def test_default_inline_prompt_preserved() -> None:
    """sc3: the inline implementer prompt markers remain in the effective
    text. Replaces the check for the ``## Implementer prompt`` heading
    (layout), keeping the markers that define the unchanged default."""
    text = _text()
    for marker in (
        "Spec context (relevant excerpt only):",
        "Plan context:",
        "Files to create or modify:",
    ):
        assert marker in text, f"default implementer prompt missing {marker!r}"


def test_backward_compatibility_called_out() -> None:
    """sc3: without the flags the existing behaviour runs unchanged."""
    text = _text()
    assert "byte-for-byte unchanged" in text or "purely additive" in text
