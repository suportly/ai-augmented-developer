"""T001–T004 — the token-economy checklist category + integration doc (spec 0020)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "templates" / "checklist-template.md"
SKILL = ROOT / "skills" / "checklist" / "SKILL.md"
DOC = ROOT / "docs" / "token-economy.md"
CREDITS = ROOT / "CREDITS.md"


# --- T001 -------------------------------------------------------------------


def test_template_has_token_economy_items() -> None:
    body = TEMPLATE.read_text(encoding="utf-8")
    assert "### Token economy (default items)" in body
    lower = body.lower()
    assert "truncat" in lower  # non-truncated logs
    assert "compress" in lower  # compression opportunities
    # references terse-mode instead of duplicating it
    assert "terse-mode" in lower or "terse mode" in lower


# --- T002 -------------------------------------------------------------------


def test_checklist_skill_registers_token_economy() -> None:
    body = SKILL.read_text(encoding="utf-8")
    assert "token-economy" in body


# --- T003 -------------------------------------------------------------------


def test_token_economy_doc_covers_external_and_nongoal() -> None:
    body = DOC.read_text(encoding="utf-8")
    lower = body.lower()
    assert "rtk" in lower and "headroom" in lower
    assert "pretooluse" in lower or "mcp" in lower  # integration mechanism
    assert "non-goal" in lower or "fora de escopo" in lower  # Article III
    # the checklist category links the doc
    assert "token-economy.md" in TEMPLATE.read_text(encoding="utf-8")


# --- T004 -------------------------------------------------------------------


def test_credits_rtk_and_headroom() -> None:
    body = CREDITS.read_text(encoding="utf-8")
    lower = body.lower()
    assert "rtk-ai/rtk" in lower
    assert "headroomlabs-ai/headroom" in lower
    assert "https://github.com/rtk-ai/rtk" in body
    assert "https://github.com/headroomlabs-ai/headroom" in body
