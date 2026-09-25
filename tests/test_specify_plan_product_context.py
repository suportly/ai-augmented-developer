"""Regression tests for T012: `specify` reads product context when it exists.

Story 3 (specs/0023-product-context/spec.md): sc1, sc2, sc5.
"""
from __future__ import annotations

import pathlib
import re


def _read_specify_skill(framework_root: pathlib.Path) -> str:
    return (framework_root / "skills" / "specify" / "SKILL.md").read_text(
        encoding="utf-8"
    )


def test_specify_reads_mission_and_roadmap_when_present(
    framework_root: pathlib.Path,
) -> None:
    """The skill prose must name the fixed product-context paths it reads
    (sc5: absent by default, but the read path must exist in prose)."""
    text = _read_specify_skill(framework_root)
    assert "specs/_product/mission.md" in text
    assert "specs/_product/roadmap.md" in text


def test_specify_cites_roadmap_entry_in_traceability(
    framework_root: pathlib.Path,
) -> None:
    """sc1: a matching roadmap entry must be cited by its R<NNN> id in the
    spec's Traceability section."""
    text = _read_specify_skill(framework_root)
    assert re.search(r"R<?NNN>?", text), "expected an R<NNN>-style id in the prose"
    assert "Traceability" in text
    # The R<NNN> mention and "Traceability" must appear close together
    # (same step/paragraph), not just anywhere in the file.
    idx_r = text.find("R<NNN>")
    if idx_r == -1:
        idx_r = re.search(r"R<?NNN>?", text).start()
    idx_trace = text.find("Traceability")
    assert idx_trace != -1
    assert abs(idx_r - idx_trace) < 600, (
        "R<NNN> and Traceability should be mentioned in the same step/paragraph"
    )


def test_specify_pauses_on_mission_out_of_scope_conflict(
    framework_root: pathlib.Path,
) -> None:
    """sc2: a demand that conflicts with mission's Out of scope must pause
    and surface the conflict, same treatment as the premise-mismatch rule."""
    text = _read_specify_skill(framework_root)
    assert "Out of scope" in text
    idx_scope = text.find("Out of scope")
    idx_pause = text.find("pause", idx_scope)
    assert idx_pause != -1 and idx_pause - idx_scope < 400, (
        "'pause' must appear near 'Out of scope' in the same paragraph"
    )


def test_specify_product_reading_is_conditional(
    framework_root: pathlib.Path,
) -> None:
    """sc5: product-context reading must be conditional on the files'
    existence, and the prose must say to proceed as before when absent."""
    text = _read_specify_skill(framework_root)
    idx = text.find("specs/_product/")
    assert idx != -1
    # Locate the enclosing paragraph (bounded by blank lines).
    start = text.rfind("\n\n", 0, idx)
    end = text.find("\n\n", idx)
    paragraph = text[start if start != -1 else 0 : end if end != -1 else len(text)]
    lower = paragraph.lower()
    assert "if" in lower and "exist" in lower, (
        "paragraph mentioning specs/_product/ must contain a conditional "
        "('if ... exist' / 'when ... exist')"
    )
    assert "as before" in lower or "as today" in lower or "proceed" in lower
