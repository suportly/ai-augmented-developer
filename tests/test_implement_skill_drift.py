"""Drift tests for the two ``implement`` SKILL.md copies.

Spec: ``specs/0013-implement-task-status-tracking/spec.md`` (Story 3).

Two distinct red conditions, intentionally introduced in this single file:

1. ``check_implement_mirror`` does not yet exist on ``validate_skills`` —
   resolving it raises ``AttributeError`` (the right red until T005). All
   tests in this file fail at module-collection time on a clean tree.
2. Even after T005 lands the function (turning condition 1 green), the
   content assertions below still fail because the loop sub-procedure
   wording lands later, in T006 (bare-form file) and T007 (mirror).

Tests therefore go red→green in two stages:
- T005 makes the import resolve and the byte-equality assertion pass
  (the two files start out identical in the tree, so byte equality
  holds before T006/T007 land their identical edit).
- T006 makes the bare-form content assertion pass; T007 makes the
  mirror content assertion pass and keeps byte equality.
"""
from __future__ import annotations

import importlib.util
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location(
    "validate_skills_drift",
    ROOT / "scripts" / "validate_skills.py",
)
_mod = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
sys.modules["validate_skills_drift"] = _mod
_spec.loader.exec_module(_mod)  # type: ignore[union-attr]

# This attribute lookup raises ``AttributeError`` until T005 adds the
# function; the AttributeError aborts collection of every test below.
check_implement_mirror = _mod.check_implement_mirror

BARE_SKILL = ROOT / "skills" / "implement" / "SKILL.md"
MIRROR_SKILL = ROOT / ".claude" / "skills" / "implement" / "SKILL.md"

# Substrings the loop sub-procedure must contain after T006/T007 land.
# Anchored on the orchestrator's status-flip contract (spec Story 3 sc1).
REQUIRED_LOOP_PHRASES = (
    "**Status:** pending",
    "**Status:** done",
    "git restore --staged tasks.md",
    "git checkout -- tasks.md",
    "orchestrator",
)


def test_check_implement_mirror_runs_clean_on_current_tree() -> None:
    """The two SKILL.md files start identical (loop section); the
    drift validator must therefore exit cleanly. Becomes green at T005
    and must stay green through T007."""
    check_implement_mirror()  # must not raise


@pytest.mark.parametrize("skill_path", [BARE_SKILL, MIRROR_SKILL])
def test_loop_section_contains_status_flip_subprocedure(
    skill_path: pathlib.Path,
) -> None:
    """Story 3 sc1 + sc3: each copy of the implement skill must spell
    out the orchestrator's status-flip sub-procedure verbatim. Goes
    green at T006 (bare) and T007 (mirror)."""
    text = skill_path.read_text(encoding="utf-8")

    # Slice just the ``## The loop`` section so an unrelated mention
    # of these phrases elsewhere in the file does not satisfy us.
    start = text.index("## The loop")
    end = text.index("\n## ", start + 1)
    loop_section = text[start:end]

    missing = [phrase for phrase in REQUIRED_LOOP_PHRASES if phrase not in loop_section]
    assert not missing, (
        f"{skill_path.relative_to(ROOT)} loop section missing required "
        f"status-flip phrases: {missing}"
    )
