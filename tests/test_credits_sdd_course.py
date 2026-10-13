"""T014 — verify CREDITS.md attributes the SDD-with-coding-agents course and
CHANGELOG records spec 0023-product-context.

Feature 0023 adapts the *idea* of keeping product context (mission, tech
stack, roadmap) as durable artifacts from DeepLearning.AI's "Spec-Driven
Development with Coding Agents" course. This closes Article VII
(Attribution) for that adaptation, mirroring the pattern already used for
BMAD-METHOD, headroom, and the other entries in CREDITS.md.
"""

from pathlib import Path

from tests.test_attribution_and_changelog import _blocks_mentioning

REPO_ROOT = Path(__file__).resolve().parents[1]
CREDITS = REPO_ROOT / "CREDITS.md"
CHANGELOG = REPO_ROOT / "CHANGELOG.md"


def test_credits_names_sdd_course_as_idea_only():
    body = CREDITS.read_text(encoding="utf-8")

    entries = body.split("### ")
    course_entries = [
        entry
        for entry in entries
        if "Spec-Driven Development with Coding Agents" in entry
    ]
    assert course_entries, (
        "CREDITS.md must have an entry naming the course "
        '"Spec-Driven Development with Coding Agents"'
    )
    entry = course_entries[0]

    assert (
        "deeplearning.ai/courses/spec-driven-development-with-coding-agents"
        in entry
    ), "CREDITS.md course entry must link to the official course page"
    assert "JetBrains" in entry, (
        "CREDITS.md course entry must credit the JetBrains partnership"
    )
    lower = entry.lower()
    assert "idea" in lower, (
        "CREDITS.md course entry must state only the idea was adapted"
    )
    assert "from scratch" in lower or "no text" in lower, (
        "CREDITS.md course entry must state templates/skill were written "
        "from scratch, no text copied"
    )


def test_changelog_mentions_0023():
    body = CHANGELOG.read_text(encoding="utf-8")

    assert "## [Unreleased]" in body, (
        "CHANGELOG.md must keep an [Unreleased] section per Keep-a-Changelog"
    )

    block = _blocks_mentioning(body, "0023")
    assert block, (
        "CHANGELOG.md must reference spec id 0023 for traceability"
    )
    lower = block.lower()

    assert "product" in lower, (
        "The changelog block recording spec 0023 must mention the "
        "product skill"
    )
    assert "mission" in lower, (
        "The changelog block recording spec 0023 must mention mission.md"
    )
    assert "tech-stack" in lower, (
        "The changelog block recording spec 0023 must mention tech-stack.md"
    )
    assert "roadmap" in lower, (
        "The changelog block recording spec 0023 must mention roadmap.md"
    )
