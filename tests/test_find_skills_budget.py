"""T003 (spec 0032 Story 3 sc2/sc3): the ceilings rise by the cost of find-skills, with a reason."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
BUDGET = json.loads((ROOT / "docs" / "instruction-budget.json").read_text(encoding="utf-8"))["entries"]
PRESETS = ("lean", "django-drf-react")
PATH_TOTAL_BEFORE_0032 = 12624


@pytest.fixture(scope="module")
def budget():
    spec = importlib.util.spec_from_file_location("instruction_budget", ROOT / "scripts" / "instruction_budget.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def measured(budget):
    return budget.measure_all()


@pytest.fixture(scope="module")
def listing_cost(budget):
    return budget._listing_tokens(ROOT / "skills" / "find-skills" / "SKILL.md")


@pytest.mark.parametrize("preset", PRESETS)
def test_skills_teto_rises_by_at_least_the_listing_cost(preset, listing_cost):
    # Later specs (0033) add their own listing cost on top; the exact figure is pinned there.
    entry = BUDGET[f"preset:{preset}:skills"]
    assert entry["teto"] - entry["baseline"] >= listing_cost
    assert entry["reason"].strip()


@pytest.mark.parametrize("preset", PRESETS)
def test_total_teto_covers_the_measurement_and_carries_a_reason(preset, measured):
    entry = BUDGET[f"preset:{preset}:total"]
    assert measured[f"preset:{preset}:total"] <= entry["teto"]
    assert entry["teto"] > entry["baseline"] and entry["reason"].strip()
    assert "0032" in entry["reason"]


def test_find_skills_entry_is_manual_with_baseline_equal_to_teto(measured):
    entry = BUDGET["skill:find-skills"]
    assert entry["baseline"] == entry["teto"] == measured["skill:find-skills"]


def test_pipeline_path_total_only_grew_by_the_0033_template_line(measured):
    # 0032 left the path at 12624; spec 0033 adds the 16-token `**UI:**` line to the spec template.
    assert 0 <= measured["path:total"] - PATH_TOTAL_BEFORE_0032 <= 16


def test_every_teto_above_baseline_has_a_reason():
    for key, entry in BUDGET.items():
        if entry["teto"] > entry["baseline"]:
            assert str(entry.get("reason", "")).strip(), key
