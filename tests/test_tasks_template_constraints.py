"""T021: the tasks template and skill carry the canonical coverage notation."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = (ROOT / "templates" / "tasks-template.md").read_text(encoding="utf-8")
SKILL = (ROOT / "skills" / "tasks" / "SKILL.md").read_text(encoding="utf-8")


def test_template_documents_canonical_notation() -> None:
    assert "Success criterion #N" in TEMPLATE
    assert "Story N scenario M" in TEMPLATE
    assert "`;`" in TEMPLATE


def test_skill_runs_coverage_preflight_instead_of_grep() -> None:
    assert "grep to verify" not in SKILL.lower()
    assert "aiadev preflight implement" in SKILL


def test_skill_quotes_data_model_constraints() -> None:
    lowered = SKILL.lower()
    assert "data-model" in lowered
    assert "enum" in lowered and "nullab" in lowered
