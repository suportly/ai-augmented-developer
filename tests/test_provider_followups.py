"""0021 — provider + token-economy fast-follows (polish)."""
from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLAN = ROOT / "skills" / "plan" / "SKILL.md"
REVIEW = ROOT / "skills" / "requesting-code-review" / "SKILL.md"
MCPS = ROOT / "presets" / "knowledge-graph" / "mcps.yaml"
DOC = ROOT / "docs" / "token-economy.md"


# --- T001: blast-radius in plan --------------------------------------------


def test_plan_has_optional_blast_radius() -> None:
    body = PLAN.read_text(encoding="utf-8")
    assert "blast-radius" in body.lower()
    assert "`impact`" in body
    assert "graceful degradation" in body.lower() or "degradação graciosa" in body.lower()
