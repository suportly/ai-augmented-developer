"""T004 (Story 3) — reviewer agents carry an APPROVED-evidence rule.

When a reviewer emits ``APPROVED`` on a non-trivial change, it must
append a ``### Why no issues`` block listing at least 3 specific
verifications (file:line + verification). The rule is documented inside
each of the three reviewer agent files.

This test verifies the documentation contract — not the runtime output
of the reviewers themselves. Runtime enforcement happens via the
orchestrator (T011) which is outside this task's scope.
"""

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SECTION_HEADER = "## Output rule for APPROVED on non-trivial change"
WHY_NO_ISSUES_BLOCK = "### Why no issues"
TERSE_GLYPH_LINE = "🟢"
NON_TRIVIAL_KEYWORD = "non-trivial"
SHORTSTAT_KEYWORD = "git diff --shortstat"
LOC_THRESHOLD = "10"
EXCLUSIONS = (".md", ".json", ".lock", ".toml", "docs/")

GOVERNANCE_REVIEWERS = (
    "agents/spec-document-reviewer.md",
    "agents/plan-document-reviewer.md",
)

ALL_REVIEWERS = (
    "agents/code-reviewer.md",
    "agents/spec-document-reviewer.md",
    "agents/plan-document-reviewer.md",
)


@pytest.mark.parametrize("agent_path", ALL_REVIEWERS)
def test_agent_has_approved_evidence_section(agent_path: str):
    body = (ROOT / agent_path).read_text(encoding="utf-8")

    assert SECTION_HEADER in body, (
        f"{agent_path} must declare an APPROVED-evidence section headed "
        f"'{SECTION_HEADER}'"
    )


@pytest.mark.parametrize("agent_path", ALL_REVIEWERS)
def test_agent_defines_non_trivial_via_shortstat(agent_path: str):
    body = (ROOT / agent_path).read_text(encoding="utf-8")

    assert NON_TRIVIAL_KEYWORD in body.lower(), (
        f"{agent_path} must define the term 'non-trivial'"
    )
    assert SHORTSTAT_KEYWORD in body, (
        f"{agent_path} non-trivial definition must reference "
        f"`{SHORTSTAT_KEYWORD}`"
    )
    assert LOC_THRESHOLD in body, (
        f"{agent_path} non-trivial definition must mention the {LOC_THRESHOLD}-LOC threshold"
    )
    for ext in EXCLUSIONS:
        assert ext in body, (
            f"{agent_path} non-trivial definition must exclude '{ext}' "
            f"(per cl-5)"
        )


@pytest.mark.parametrize("agent_path", ALL_REVIEWERS)
def test_agent_requires_why_no_issues_block_with_three_verifications(
    agent_path: str,
):
    body = (ROOT / agent_path).read_text(encoding="utf-8")

    assert WHY_NO_ISSUES_BLOCK in body, (
        f"{agent_path} must reference the '{WHY_NO_ISSUES_BLOCK}' block"
    )
    # The contract demands "at least 3" verifications; the prose may say
    # "at least 3", "3-5", or "3 verifications". Accept any of those.
    lowered = body.lower()
    has_count = (
        "at least 3" in lowered
        or "3-5" in lowered
        or "3 verifications" in lowered
        or "three verifications" in lowered
    )
    assert has_count, (
        f"{agent_path} must require at least 3 verifications in the "
        f"'{WHY_NO_ISSUES_BLOCK}' block"
    )


@pytest.mark.parametrize("agent_path", ALL_REVIEWERS)
def test_agent_describes_terse_mode_variant(agent_path: str):
    body = (ROOT / agent_path).read_text(encoding="utf-8")

    section_start = body.find(SECTION_HEADER)
    assert section_start != -1, (
        f"{agent_path} must contain {SECTION_HEADER} (precondition)"
    )
    section = body[section_start:]

    assert TERSE_GLYPH_LINE in section, (
        f"{agent_path} APPROVED-evidence section must show the terse-mode "
        f"green glyph ({TERSE_GLYPH_LINE} file:line — verification)"
    )
    assert "file:line" in section, (
        f"{agent_path} APPROVED-evidence section must show the "
        f"'file:line' shape for verifications"
    )


@pytest.mark.parametrize("agent_path", GOVERNANCE_REVIEWERS)
def test_governance_reviewers_mark_creation_as_always_non_trivial(
    agent_path: str,
):
    body = (ROOT / agent_path).read_text(encoding="utf-8")

    section_start = body.find(SECTION_HEADER)
    assert section_start != -1, (
        f"{agent_path} must contain {SECTION_HEADER} (precondition)"
    )
    section = body[section_start:]
    lowered = section.lower()

    assert "always non-trivial" in lowered or "always be non-trivial" in lowered, (
        f"{agent_path} must state that spec/plan creation is ALWAYS "
        f"non-trivial (Story 3 AC-4)"
    )
