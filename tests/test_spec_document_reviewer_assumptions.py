"""T046: spec-document-reviewer verifica o critério de premissas (Story 5, scenario 2)."""

from __future__ import annotations

import re
from pathlib import Path

AGENT = Path(__file__).resolve().parent.parent / "agents" / "spec-document-reviewer.md"


def _assumption_item() -> str:
    """Return the single checklist item that talks about `## Assumptions`."""
    items = [
        ln for ln in AGENT.read_text(encoding="utf-8").splitlines()
        if ln.startswith("- [ ]") and "Assumptions" in ln
    ]
    assert len(items) == 1, items
    return items[0].lower()


def test_item_requires_low_impact_and_reversible() -> None:
    item = _assumption_item()
    assert "low" in item and "impact" in item
    assert "reversible" in item


def test_item_rejects_scope_security_privacy() -> None:
    item = _assumption_item()
    for word in ("scope", "security", "privacy"):
        assert word in item, word
    assert "needs clarification" in item


def test_item_is_conditional_on_section_presence() -> None:
    assert re.search(r"if .*assumptions", _assumption_item())
