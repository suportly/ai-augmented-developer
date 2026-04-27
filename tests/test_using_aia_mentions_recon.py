"""Regression test pinning the Reconnaissance callout in the orientation skill (issue #26)."""
from __future__ import annotations

import pathlib
import re


def test_orientation_mentions_reconnaissance(framework_root: pathlib.Path) -> None:
    """Story 3 scenarios 1 & 2: a fresh agent reading the orientation
    skill must learn the Reconnaissance contract before its first
    `specify` call. The callout must include a Markdown link whose
    target ends with `skills/specify/SKILL.md`."""
    text = (
        framework_root
        / "skills"
        / "using-ai-augmented-developer"
        / "SKILL.md"
    ).read_text(encoding="utf-8")

    assert "Reconnaissance" in text

    link_re = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
    targets = [m.group(1) for m in link_re.finditer(text)]
    assert any(target.endswith("specify/SKILL.md") for target in targets), (
        f"orientation must link to the specify skill; found {targets!r}"
    )
