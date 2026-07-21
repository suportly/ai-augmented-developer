"""T006 — attribution + the 0017 Article III waiver is updated (spec 0019)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CREDITS = ROOT / "CREDITS.md"
PLAN_0017 = ROOT / "specs" / "0017-knowledge-graph-context-provider" / "plan.md"


def test_credits_lsps_and_0017_waiver_updated() -> None:
    credits = CREDITS.read_text(encoding="utf-8")
    assert "piebald-ai/claude-code-lsps" in credits.lower()
    assert "https://github.com/Piebald-AI/claude-code-lsps" in credits

    plan = PLAN_0017.read_text(encoding="utf-8")
    # the waiver now reflects a second reference implementation (spec 0019 / LSP)
    assert "0019" in plan
    assert "LSP" in plan
