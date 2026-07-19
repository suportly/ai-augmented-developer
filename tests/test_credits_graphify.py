"""T010 — CREDITS.md attributes Graphify-Labs/graphify per Article VII.

Spec 0017 adapts ideas from graphify (the provider contract, EXTRACTED/
INFERRED/AMBIGUOUS confidence tags, blast-radius). Article VII requires
naming the source with a link.
"""
from pathlib import Path

CREDITS = Path(__file__).resolve().parents[1] / "CREDITS.md"


def test_credits_has_graphify_entry() -> None:
    body = CREDITS.read_text(encoding="utf-8")
    lower = body.lower()
    assert "graphify-labs/graphify" in lower, (
        "CREDITS.md must name the graphify repo (Article VII)"
    )
    assert "https://github.com/Graphify-Labs/graphify" in body, (
        "CREDITS.md must link to the graphify repo"
    )
    assert "confidence" in lower or "blast-radius" in lower or "knowledge graph" in lower, (
        "credit block must name the adapted concept"
    )
