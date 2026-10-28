"""T004 (spec 0032 Story 4 sc1): Art. VII credit for find-skills, without naming it in the skill."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_REPO = "vercel-labs/skills"


def _entry() -> str:
    body = (ROOT / "CREDITS.md").read_text(encoding="utf-8")
    blocks = re.split(r"(?m)^### ", body)
    matches = [b for b in blocks if SOURCE_REPO in b.split("\n", 1)[0]]
    assert matches, f"CREDITS.md has no ### entry whose heading names {SOURCE_REPO}"
    return matches[0]


def test_credits_entry_names_repo_material_and_license():
    entry = _entry()
    assert f"https://github.com/{SOURCE_REPO}" in entry.split("\n", 1)[0]
    assert "find-skills" in entry
    assert "MIT" in entry


def test_credits_entry_says_what_was_adapted_and_not_bundled():
    entry = _entry().lower()
    assert "adapt" in entry
    assert "not bundled" in entry or "never bundled" in entry or "do not bundle" in entry


def test_skill_text_does_not_name_the_source():
    skill = (ROOT / "skills" / "find-skills" / "SKILL.md").read_text(encoding="utf-8").lower()
    for needle in ("vercel", SOURCE_REPO, "vercel-labs"):
        assert needle not in skill
