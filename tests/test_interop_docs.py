"""Documentation drift tests for the Agent Skills interop feature.

Spec: ``specs/0016-agent-skills-interop/spec.md``.

These tests assert that the documentation surfaces describing the four
stories (frontmatter conformance under ``metadata.aiadev``, rule
``paths:`` propagation, the canonical ``AGENTS.md``, and generated
plugin manifests) exist and reference the canonical artefacts. They
are intentionally shape checks, not snapshots — the docs may be
reworded without breaking the assertions, but the key terms must
remain documented somewhere.
"""

from __future__ import annotations

import pathlib
import re


REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent


def test_credits_mentions_agent_skills_source() -> None:
    credits = (REPO_ROOT / "CREDITS.md").read_text(encoding="utf-8")
    assert "agentskills.io" in credits


def test_changelog_records_all_four_stories() -> None:
    """Anchor on the block that mentions spec 0016 — not on "[Unreleased]"
    or a hardcoded version boundary — so the test keeps working after the
    release-flip moves the record into a ``## [X.Y.Z]`` block (same
    lesson as tests/test_attribution_and_changelog.py's helper)."""
    changelog = (REPO_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "## [Unreleased]" in changelog, "CHANGELOG missing [Unreleased] header"

    headings = [m.start() for m in re.finditer(r"^## \[", changelog, re.MULTILINE)]
    blocks = [
        changelog[start:end]
        for start, end in zip(headings, headings[1:] + [len(changelog)])
    ]
    matching = [b for b in blocks if "0016" in b or "agent-skills-interop" in b]
    assert matching, "no CHANGELOG block records spec 0016"
    unreleased_block = "\n".join(matching)

    # One keyword per story (1: frontmatter migration, 2: rule paths,
    # 3: AGENTS.md canonical, 4: generated manifests).
    assert "metadata.aiadev" in unreleased_block
    assert "paths:" in unreleased_block
    assert "AGENTS.md" in unreleased_block
    assert "manifests" in unreleased_block.lower()


def test_agent_skills_interop_doc_exists_and_covers_key_topics() -> None:
    doc = (REPO_ROOT / "docs" / "agent-skills-interop.md").read_text(encoding="utf-8")
    assert "aiadev manifests" in doc
    assert "metadata.aiadev" in doc


def test_readme_mentions_agents_md() -> None:
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    assert "AGENTS.md" in readme
