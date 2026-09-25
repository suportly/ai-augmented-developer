"""`specify` and `plan` read the product context when it exists (T012, T013).

Spec: specs/0023-product-context/spec.md, Story 3 sc1–sc5.

Both skills carry the product-context instructions in Loop step 2. The
tests read that step only — frontmatter stripped, bounded by the next
numbered step — so a later edit elsewhere in the file (frontmatter
inputs, other steps) cannot satisfy or break them by accident.
"""
from __future__ import annotations

import pathlib
import re

import pytest

_FRONTMATTER_RE = re.compile(r"\A---\n.*?\n---\n", re.DOTALL)


def _loop_step(framework_root: pathlib.Path, skill: str, number: int) -> str:
    """Return the text of numbered step ``number`` under the skill's ``## Loop``."""
    text = (framework_root / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
    body = _FRONTMATTER_RE.sub("", text, count=1)
    loop = body.split("## Loop", 1)[1].split("\n## ", 1)[0]
    match = re.search(
        rf"^{number}\. (.*?)(?=^\d+\. |\Z)", loop, re.MULTILINE | re.DOTALL
    )
    assert match, f"skills/{skill}/SKILL.md has no Loop step {number}"
    return match.group(1)


@pytest.fixture
def specify_step(framework_root: pathlib.Path) -> str:
    return _loop_step(framework_root, "specify", 2)


@pytest.fixture
def plan_step(framework_root: pathlib.Path) -> str:
    return _loop_step(framework_root, "plan", 2)


def test_specify_reads_mission_and_roadmap_when_present(specify_step: str) -> None:
    assert "specs/_product/mission.md" in specify_step
    assert "specs/_product/roadmap.md" in specify_step


def test_specify_cites_roadmap_entry_in_traceability(specify_step: str) -> None:
    """sc1: a matching roadmap entry is cited by its R<NNN> id in Traceability."""
    assert "R<NNN>" in specify_step
    assert "Traceability" in specify_step


def test_specify_pauses_on_mission_out_of_scope_conflict(specify_step: str) -> None:
    """sc2: conflict with the mission's Out of scope pauses, like premise mismatch."""
    assert "Out of scope" in specify_step
    assert "pause" in specify_step.lower()
    assert "premise-mismatch" in specify_step or "premise mismatch" in specify_step


def test_specify_product_reading_is_conditional(specify_step: str) -> None:
    """sc5: absent product files leave the skill's behaviour unchanged."""
    lower = specify_step.lower()
    assert "if " in lower and "exist" in lower
    assert "as before" in lower


def test_plan_uses_tech_stack_for_technical_context(plan_step: str) -> None:
    """sc3: Technical context is filled from tech-stack.md when it exists."""
    assert "specs/_product/tech-stack.md" in plan_step
    assert "Technical context" in plan_step


def test_plan_deviation_becomes_adr(plan_step: str) -> None:
    """sc3: a new language/framework/dependency becomes an Architecture decision."""
    assert "Architecture decisions" in plan_step


def test_plan_lists_tech_stack_auto_stack_divergence(plan_step: str) -> None:
    """sc4: divergence with the auto-stack block is listed, not resolved."""
    lower = plan_step.lower()
    assert "auto-stack" in lower
    assert "AGENTS.md" in plan_step
    assert "divergence" in lower
    assert "without choosing" in lower or "human decides" in lower


def test_plan_product_reading_is_conditional(plan_step: str) -> None:
    """sc5: absent tech-stack.md leaves the skill's behaviour unchanged."""
    lower = plan_step.lower()
    assert "if " in lower and "exist" in lower
    assert "as before" in lower
