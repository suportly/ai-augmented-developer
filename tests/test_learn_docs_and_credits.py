"""T011 — aiadev learn is documented and credits headroom (spec 0018)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_learn_documented_and_credits_headroom() -> None:
    docs = (ROOT / "docs" / "learn.md").read_text(encoding="utf-8")
    assert "aiadev learn" in docs
    assert "specs/_learnings.md" in docs
    assert "--show-bodies" in docs

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "aiadev learn" in readme

    credits = (ROOT / "CREDITS.md").read_text(encoding="utf-8")
    lower = credits.lower()
    assert "headroomlabs-ai/headroom" in lower
    assert "https://github.com/headroomlabs-ai/headroom" in credits
    assert "learn" in lower
