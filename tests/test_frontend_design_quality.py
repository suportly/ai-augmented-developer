"""frontend-design quality (spec 0034)."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "presets" / "django-drf-react" / "skills" / "frontend-design" / "SKILL.md"
RAW = SKILL.read_text(encoding="utf-8")
_, FRONT, BODY = RAW.split("---\n", 2)
LOW = BODY.lower()
DESC = re.search(r"^description:\s*(.+)$", FRONT, re.M).group(1).strip()  # type: ignore[union-attr]

CURRENT_DESC = (
    "Create distinctive, production-grade frontend interfaces with high design quality. "
    "Use when building web components, pages, or React Native screens. "
    "Generates creative, polished code that avoids generic AI aesthetics."
)


def _has(*phrases: str) -> bool:
    return all(p in LOW for p in phrases)


def test_description_unchanged() -> None:
    assert DESC == CURRENT_DESC


def test_direction_recorded_before_any_component() -> None:
    assert _has("direction record", "before generating any component file")


def test_direction_record_is_short_and_complete() -> None:
    assert _has("at most 6 lines", "style, typography, palette", "reason for each")


def test_starts_from_existing_theme_tokens() -> None:
    assert _has("start from the existing theme tokens", "where it diverges")


def test_given_direction_only_maps_to_tokens() -> None:
    assert _has("already carries a direction", "brand or approved prototype", "only the mapping to tokens")


def test_no_tokens_proposes_minimal_set() -> None:
    assert _has("no theme tokens", "minimal tokens", "colors and fonts")
