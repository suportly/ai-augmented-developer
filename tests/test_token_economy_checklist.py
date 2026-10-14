"""T001–T004 — the token-economy checklist category + integration doc (spec 0020)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "templates" / "checklist-template.md"
SKILL = ROOT / "skills" / "checklist" / "SKILL.md"
REFS = ROOT / "skills" / "checklist" / "references"


def _effective_skill() -> str:
    """Skill text plus the reference files it cites."""
    body = SKILL.read_text(encoding="utf-8")
    for ref in sorted(REFS.glob("*.md")):
        assert ref.stem in body and "references/<category>.md" in body, ref.name
        body += "\n" + ref.read_text(encoding="utf-8")
    return body
DOC = ROOT / "docs" / "token-economy.md"
CREDITS = ROOT / "CREDITS.md"


# --- T001 -------------------------------------------------------------------


def test_skill_has_token_economy_items() -> None:
    body = (REFS / "token-economy.md").read_text(encoding="utf-8")
    assert "Token economy" in body
    lower = body.lower()
    assert "truncat" in lower  # non-truncated logs
    assert "compress" in lower  # compression opportunities
    # the removed reviewer-output rule is no longer referenced (0030)
    assert "terse" not in lower


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
    assert "token-economy.md" in (REFS / "token-economy.md").read_text(encoding="utf-8")


# --- T004 -------------------------------------------------------------------


def test_credits_rtk_and_headroom() -> None:
    body = CREDITS.read_text(encoding="utf-8")
    lower = body.lower()
    assert "rtk-ai/rtk" in lower
    assert "headroomlabs-ai/headroom" in lower
    assert "https://github.com/rtk-ai/rtk" in body
    assert "https://github.com/headroomlabs-ai/headroom" in body


# --- T049 -------------------------------------------------------------------


def test_template_carries_single_category_and_owner_task() -> None:
    body = TEMPLATE.read_text(encoding="utf-8")
    assert body.count("{{CATEGORY}}") >= 1
    assert "(default items)" not in body
    for other in ("Security", "Performance", "Accessibility", "Internationalization", "Token economy"):
        assert f"### {other}" not in body
    assert "Owner task" in body


def test_skill_holds_items_per_category() -> None:
    assert {p.stem for p in REFS.glob("*.md")} == {
        "security", "performance", "accessibility", "i18n", "token-economy"
    }
    for ref in REFS.glob("*.md"):
        assert "../" not in ref.read_text(encoding="utf-8"), ref.name
    body = _effective_skill()
    for cat in ("Security", "Performance", "Accessibility", "Internationalization", "Token economy"):
        assert f"# Checklist items: {cat}" in body


def test_instantiated_template_is_parsed_by_gate(tmp_path: Path) -> None:
    from aiadev import preflight

    text = TEMPLATE.read_text(encoding="utf-8").replace("{{CATEGORY}}", "security")
    # a FAIL row on the first item; template placeholder row is not a FAIL
    assert "| 1 | ... | PASS / FAIL / N/A | link or note |" in text or "PASS / FAIL / N/A" in text
    items = text.replace("PASS / FAIL / N/A", "FAIL", 1)
    owned = items.replace("| | | | |", "| 1 | x | fix | T002 |")
    tasks = "### T001 — a\n\n- **Spec scenarios:** Story 1\n\n### T002 — b\n\n- **Spec scenarios:** Story 1\n"

    def run(content: str):
        run.n += 1
        feature = tmp_path / "specs" / f"0099-run{run.n}"
        feature.mkdir(parents=True)
        (feature / "spec.md").write_text("# Spec\n\n## User stories\n\n### Story 1 — A\n\n1. dado x\n", encoding="utf-8")
        (feature / "plan.md").write_text("# Plan\n", encoding="utf-8")
        (feature / "tasks.md").write_text(tasks, encoding="utf-8")
        (feature / "checklists").mkdir()
        (feature / "checklists" / "security.md").write_text(content, encoding="utf-8")
        return preflight.check(
            "implement", feature, env={}, current_branch=lambda: "", repo_root=tmp_path
        )

    run.n = 0
    assert run(text) == []
    assert any("FAIL without an owner" in i.message for i in run(items))
    assert run(owned) == []
