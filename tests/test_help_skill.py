"""T009 — the help skill exists, validates, and points at the generated reference."""

import json
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "help" / "SKILL.md"
SCHEMA = ROOT / "schemas" / "skill-frontmatter.schema.json"


def _read_frontmatter():
    text = SKILL.read_text(encoding="utf-8")
    assert text.startswith("---"), "SKILL.md must open with YAML frontmatter"
    _, _, rest = text.partition("---\n")
    payload, _, body = rest.partition("\n---")
    return yaml.safe_load(payload), body


def test_help_skill_exists():
    assert SKILL.exists(), f"expected {SKILL} to exist"


@pytest.mark.xfail(
    reason="T004 migrates the 22 SKILL.md files to metadata.aiadev; "
    "skills/help/SKILL.md still has proprietary fields at the top level "
    "(spec 0016 Story 1, T002 rewrites the schema first).",
    strict=False,
)
def test_help_skill_frontmatter_validates_against_schema():
    fm, _ = _read_frontmatter()
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(fm)
    assert fm["name"] == "help"


def test_help_skill_instructs_verbatim_return():
    _, body = _read_frontmatter()
    assert "docs/pipeline-reference.md" in body, (
        "help skill must name the generated reference file"
    )
    assert "verbatim" in body.lower(), (
        "help skill must instruct verbatim return (no paraphrasing)"
    )


def test_help_skill_follows_house_announcement_style():
    _, body = _read_frontmatter()
    assert "**Announce at start:**" in body, (
        "every aiadev SKILL.md opens with an Announce-at-start line"
    )
