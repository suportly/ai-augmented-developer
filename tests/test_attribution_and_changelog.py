"""T022 — verify CREDITS.md attributes BMAD-METHOD and CHANGELOG records the 4 stories.

Closes Article VII (Attribution) for spec 0014-bmad-inspired-evolutions and
records the four user stories in the changelog. The story content lives
under [Unreleased] until the release-flip happens; afterwards it lives in
the most recent ``## [<version>]`` block. Both shapes are accepted so the
tests don't break on the natural Keep-a-Changelog flow.
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CREDITS = REPO_ROOT / "CREDITS.md"
CHANGELOG = REPO_ROOT / "CHANGELOG.md"

_VERSION_HEADING_RE = re.compile(r"^## \[", re.MULTILINE)


def _most_recent_changes_block(body: str) -> str:
    """Return [Unreleased] (if non-empty) plus the latest released version block.

    Keeps the changelog tests resilient across two scenarios:

    * **Freshly cut release** — content was moved from [Unreleased] into
      ``## [<version>]`` and [Unreleased] is empty. We return the
      released block.
    * **Unreleased + still-relevant prior release** — a new feature
      added content to [Unreleased] while the most recent released
      block still describes the changes a drift test wants to verify.
      We return both concatenated so the assertions still find their
      markers wherever the maintainer placed them.
    """
    headings = list(_VERSION_HEADING_RE.finditer(body))
    if not headings:
        return body

    blocks: list[str] = []
    for i, match in enumerate(headings):
        start = match.start()
        end = headings[i + 1].start() if i + 1 < len(headings) else len(body)
        block = body[start:end]
        heading_line = block.split("\n", 1)[0]
        content = block.split("\n", 1)[1] if "\n" in block else ""
        is_unreleased = "[Unreleased]" in heading_line
        if not content.strip():
            continue
        blocks.append(block)
        # Stop after we've collected the first non-empty *released*
        # block — anything older is not "most recent".
        if not is_unreleased:
            break

    if not blocks:
        return body[headings[0].start():]
    return "\n".join(blocks)


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


def test_changelog_most_recent_block_mentions_all_four_stories():
    body = CHANGELOG.read_text(encoding="utf-8")
    assert "## [Unreleased]" in body, (
        "CHANGELOG.md must keep an [Unreleased] section per Keep-a-Changelog"
    )

    block = _most_recent_changes_block(body)
    lower = block.lower()

    # Story 1 — task-context
    assert "task-context" in lower or "compose" in lower, (
        "Most recent changelog block must mention the task-context skill "
        "(spec 0014 Story 1) — found in [Unreleased] or in the most recent "
        "released version block"
    )

    # Story 2 — 3-tier customization resolver
    assert "3-tier customization" in lower or "_aiadev/team.toml" in lower, (
        "Most recent changelog block must mention the 3-tier customization "
        "resolver (spec 0014 Story 2)"
    )

    # Story 3 — zero-findings-halt review pattern
    assert "zero-findings-halt" in lower or "why no issues" in lower, (
        "Most recent changelog block must mention the zero-findings-halt "
        "review pattern (spec 0014 Story 3)"
    )

    # Story 4 — state-aware help skill via pipeline_state
    assert "pipeline_state" in lower or "help skill" in lower or "state-aware" in lower, (
        "Most recent changelog block must mention the state-aware help skill "
        "(spec 0014 Story 4)"
    )


def test_changelog_most_recent_block_references_spec_0014():
    body = CHANGELOG.read_text(encoding="utf-8")
    block = _most_recent_changes_block(body)

    assert "0014" in block, (
        "Most recent changelog block must reference spec id 0014 for "
        "traceability — accepted under [Unreleased] or under the most "
        "recent released version"
    )
