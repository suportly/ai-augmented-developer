"""Behavioural content tests for ``skills/implement/SKILL.md``.

Spec: ``specs/0013-implement-task-status-tracking/spec.md`` (Story 3 sc1);
rewritten by spec 0030 (T030) to assert behaviour, not position or
literal prose, so rewrites of the loop section do not break it.

The single tracked source of truth is ``skills/implement/SKILL.md``
(``.claude/skills/`` and ``src/aiadev/_assets/skills/`` are ignored
build artefacts). Set ``AIADEV_PROSE_ROOT`` to point the test at a copy
of the repo text (used to prove the assertions catch regressions).
"""
from __future__ import annotations

import os
import pathlib
import re

ROOT = pathlib.Path(
    os.environ.get("AIADEV_PROSE_ROOT")
    or pathlib.Path(__file__).resolve().parent.parent
)
BARE_SKILL = ROOT / "skills" / "implement" / "SKILL.md"

# Status flip: manual edit of the row marker OR the CLI helper.
_FLIP = re.compile(
    r"\*\*Status:\*\*\s*pending[\s\S]{0,400}?\*\*Status:\*\*\s*done"
    r"|aiadev tasks done",
)
# The flip rides in the same commit as the task's code.
_ATOMIC = re.compile(
    r"atomic|same commit|one (?:git )?commit|(?:code|test)[^.\n]{0,80}together|together[^.\n]{0,60}tasks\.md",
    re.I,
)
# Rollback of the marker when the commit fails.
_ROLLBACK = re.compile(
    r"git restore --staged tasks\.md"
    r"|git checkout -- tasks\.md"
    r"|roll(?:ing)?[ -]?back[^.\n]{0,80}(?:marker|status|tasks\.md)"
    r"|(?:marker|status)[^.\n]{0,80}(?:rolled back|reverted)",
    re.I,
)
_COMMIT_FAILS = re.compile(r"commit (?:fail|is rejected|rejected)|hook (?:reject|fail)|signing error", re.I)


def _text() -> str:
    return BARE_SKILL.read_text(encoding="utf-8")


def test_loop_flips_status_atomically_with_the_commit() -> None:
    """The loop describes flipping the task status to done (manual
    ``**Status:**`` rewrite or ``aiadev tasks done``) inside the same
    commit as the task's files."""
    text = _text()
    assert _FLIP.search(text), "implement skill must describe the pending->done status flip"
    assert _ATOMIC.search(text), "status flip must ride in the same commit as the task code"


def test_loop_rolls_back_the_marker_when_commit_fails() -> None:
    """On commit failure the done marker is rolled back (never --no-verify)."""
    text = _text()
    match = _ROLLBACK.search(text)
    assert match, "implement skill must describe rolling back the status marker"
    window = text[max(0, match.start() - 500): match.end() + 500]
    assert _COMMIT_FAILS.search(window), "rollback must be tied to a failing commit"


def test_orchestrator_owns_tasks_md_not_the_implementer() -> None:
    text = _text()
    assert re.search(
        r"orchestrator[\s\S]{0,300}tasks\.md|tasks\.md[\s\S]{0,300}orchestrator", text, re.I
    ), "the orchestrator must be named as the owner of tasks.md"
