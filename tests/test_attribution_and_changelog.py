"""T022 — verify CREDITS.md attributes BMAD-METHOD and CHANGELOG records the 4 stories.

Closes Article VII (Attribution) for spec 0014-bmad-inspired-evolutions and
records the four user stories in the [Unreleased] section of CHANGELOG.md.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CREDITS = REPO_ROOT / "CREDITS.md"
CHANGELOG = REPO_ROOT / "CHANGELOG.md"


def test_credits_names_bmad_method_with_url_and_license():
    body = CREDITS.read_text(encoding="utf-8")

    assert "bmad-code-org/BMAD-METHOD" in body, (
        "CREDITS.md must name the BMAD-METHOD repo (Article VII)"
    )
    assert "https://github.com/bmad-code-org/BMAD-METHOD" in body, (
        "CREDITS.md must link to the BMAD-METHOD repo"
    )
    assert "MIT" in body, (
        "BMAD-METHOD credit block must mention the upstream MIT license"
    )


def test_credits_names_inspired_material_for_each_story():
    body = CREDITS.read_text(encoding="utf-8")
    lower = body.lower()

    # Story 1 — task-context skill
    assert "task-context" in lower, (
        "BMAD credit block must name the task-context skill (Story 1)"
    )

    # Story 2 — 3-tier customization resolver
    assert "3-tier customization" in lower, (
        "BMAD credit block must name the 3-tier customization resolver (Story 2)"
    )

    # Story 3 — zero-findings-halt review pattern
    assert "zero-findings-halt" in lower, (
        "BMAD credit block must name the zero-findings-halt review pattern (Story 3)"
    )


def test_changelog_unreleased_mentions_all_four_stories():
    body = CHANGELOG.read_text(encoding="utf-8")
    assert "## [Unreleased]" in body, (
        "CHANGELOG.md must keep an [Unreleased] section per Keep-a-Changelog"
    )

    # Slice from [Unreleased] up to the next ## [version] heading.
    section = body.split("## [Unreleased]", 1)[1].split("\n## [", 1)[0]
    lower = section.lower()

    # Story 1 — task-context
    assert "task-context" in lower or "compose" in lower, (
        "[Unreleased] must mention the task-context skill (spec 0014 Story 1)"
    )

    # Story 2 — 3-tier customization resolver
    assert "3-tier customization" in lower or "_aiadev/team.toml" in lower, (
        "[Unreleased] must mention the 3-tier customization resolver "
        "(spec 0014 Story 2)"
    )

    # Story 3 — zero-findings-halt review pattern
    assert "zero-findings-halt" in lower or "why no issues" in lower, (
        "[Unreleased] must mention the zero-findings-halt review pattern "
        "(spec 0014 Story 3)"
    )

    # Story 4 — state-aware help skill via pipeline_state
    assert "pipeline_state" in lower or "help skill" in lower or "state-aware" in lower, (
        "[Unreleased] must mention the state-aware help skill "
        "(spec 0014 Story 4)"
    )


def test_changelog_unreleased_references_spec_0014():
    body = CHANGELOG.read_text(encoding="utf-8")
    section = body.split("## [Unreleased]", 1)[1].split("\n## [", 1)[0]

    assert "0014" in section, (
        "[Unreleased] must reference spec id 0014 for traceability"
    )
