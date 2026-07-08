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


def _blocks_mentioning(body: str, marker: str) -> str:
    """Return every ``## [...]`` block whose content mentions ``marker``.

    A feature's changelog record starts under [Unreleased] and moves
    into a ``## [<version>]`` block when the release is cut — and stays
    there forever. Anchoring on the marker (the spec id) instead of on
    "the most recent block" keeps these drift tests stable across
    later releases: spec 0014's record lives in the 0.19.0 block no
    matter how many versions ship after it.
    """
    headings = list(_VERSION_HEADING_RE.finditer(body))
    if not headings:
        return body

    blocks: list[str] = []
    for i, match in enumerate(headings):
        start = match.start()
        end = headings[i + 1].start() if i + 1 < len(headings) else len(body)
        block = body[start:end]
        if marker in block:
            blocks.append(block)
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


def test_changelog_0014_block_mentions_all_four_stories():
    body = CHANGELOG.read_text(encoding="utf-8")
    assert "## [Unreleased]" in body, (
        "CHANGELOG.md must keep an [Unreleased] section per Keep-a-Changelog"
    )

    block = _blocks_mentioning(body, "0014")
    lower = block.lower()

    # Story 1 — task-context
    assert "task-context" in lower or "compose" in lower, (
        "The changelog block recording spec 0014 must mention the "
        "task-context skill (Story 1)"
    )

    # Story 2 — 3-tier customization resolver
    assert "3-tier customization" in lower or "_aiadev/team.toml" in lower, (
        "The changelog block recording spec 0014 must mention the 3-tier "
        "customization resolver (Story 2)"
    )

    # Story 3 — zero-findings-halt review pattern
    assert "zero-findings-halt" in lower or "why no issues" in lower, (
        "The changelog block recording spec 0014 must mention the "
        "zero-findings-halt review pattern (Story 3)"
    )

    # Story 4 — state-aware help skill via pipeline_state
    assert "pipeline_state" in lower or "help skill" in lower or "state-aware" in lower, (
        "The changelog block recording spec 0014 must mention the "
        "state-aware help skill (Story 4)"
    )


def test_changelog_references_spec_0014():
    body = CHANGELOG.read_text(encoding="utf-8")

    assert _blocks_mentioning(body, "0014"), (
        "CHANGELOG.md must reference spec id 0014 for traceability — "
        "under [Unreleased] or under a released version block"
    )
