"""T007 (spec 0033, success criterion #7): ceilings rise by the measured cost of /aia:design, with a reason."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
ENTRIES = json.loads((ROOT / "docs" / "instruction-budget.json").read_text(encoding="utf-8"))["entries"]
PRESETS = ("lean", "django-drf-react")
# Teto values in force before spec 0033 (after 0032).
BEFORE = {
    "lean": {"skills": 599, "commands": 429, "total": 2928},
    "django-drf-react": {"skills": 906, "commands": 460, "total": 3628},
}
PATH_BEFORE = {"path:total": 12637, "path:templates/spec-template.md": 549}
TEMPLATE_LINE_COST = 16  # `**UI:**` line in templates/spec-template.md


@pytest.fixture(scope="module")
def budget():
    spec = importlib.util.spec_from_file_location("instruction_budget", ROOT / "scripts" / "instruction_budget.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def measured(budget):
    return budget.measure_all()


@pytest.mark.parametrize("preset", PRESETS)
def test_listing_tetos_rise_by_exactly_the_listing_costs(preset, budget):
    skill = budget._listing_tokens(ROOT / "skills" / "design" / "SKILL.md")
    command = budget._listing_tokens(ROOT / "commands" / "design.md", default_name="aia:design")
    assert ENTRIES[f"preset:{preset}:skills"]["teto"] - BEFORE[preset]["skills"] == skill
    assert ENTRIES[f"preset:{preset}:commands"]["teto"] - BEFORE[preset]["commands"] == command
    assert ENTRIES[f"preset:{preset}:total"]["teto"] - BEFORE[preset]["total"] == skill + command


@pytest.mark.parametrize("preset", PRESETS)
def test_teto_covers_the_measurement_and_has_a_reason(preset, measured):
    for part in ("skills", "commands", "total"):
        entry = ENTRIES[f"preset:{preset}:{part}"]
        assert measured[f"preset:{preset}:{part}"] <= entry["teto"]
        assert entry["teto"] > entry["baseline"] and "0033" in entry["reason"]


def test_path_rises_only_by_the_template_line(measured):
    assert measured["path:templates/spec-template.md"] <= ENTRIES["path:templates/spec-template.md"]["teto"]
    assert ENTRIES["path:templates/spec-template.md"]["teto"] - PATH_BEFORE["path:templates/spec-template.md"] == TEMPLATE_LINE_COST
    assert measured["path:total"] <= ENTRIES["path:total"]["teto"]
    assert ENTRIES["path:total"]["teto"] - PATH_BEFORE["path:total"] <= TEMPLATE_LINE_COST
    for key in ("path:total", "path:templates/spec-template.md"):
        entry = ENTRIES[key]
        if entry["teto"] > entry["baseline"]:
            assert "0033" in entry["reason"]


def test_design_skill_entry_is_manual_with_baseline_equal_to_teto(measured):
    entry = ENTRIES["skill:design"]
    assert entry["baseline"] == entry["teto"] == measured["skill:design"]


def test_design_is_not_on_the_pipeline_path():
    text = (ROOT / "docs" / "pipeline-path.yaml").read_text(encoding="utf-8")
    assert "skills/design" not in text and "design-template" not in text


def test_every_teto_above_baseline_has_a_reason():
    for key, entry in ENTRIES.items():
        if entry["teto"] > entry["baseline"]:
            assert str(entry.get("reason", "")).strip(), key
