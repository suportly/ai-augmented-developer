"""T004 (Story 3) — reviewer agents carry an APPROVED-evidence rule.

When a reviewer emits ``APPROVED`` on a non-trivial change, it must
append a ``### Why no issues`` block listing at least 3 specific
verifications (file:line + verification). The rule is documented inside
each of the three reviewer agent files.

This test verifies the documentation contract — not the runtime output
of the reviewers themselves. Runtime enforcement happens via the
orchestrator (T011) which is outside this task's scope.
"""

import os
from pathlib import Path

import pytest

# AIADEV_PROSE_ROOT lets the mutation proof point at a copy of the text.
ROOT = Path(os.environ.get("AIADEV_PROSE_ROOT") or Path(__file__).resolve().parents[1])
WHY_NO_ISSUES_BLOCK = "### Why no issues"
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


def _evidence_rule(body: str) -> str:
    """Text from the first mention of the Why-no-issues block onward.

    Position/heading independent: the rule is wherever the block is
    first required, not under a fixed header."""
    idx = body.find("Why no issues")
    assert idx != -1, "agent must carry the '### Why no issues' APPROVED-evidence rule"
    return body[idx:]


@pytest.mark.parametrize("agent_path", ALL_REVIEWERS)
def test_agent_has_approved_evidence_rule(agent_path: str):
    body = (ROOT / agent_path).read_text(encoding="utf-8")

    assert WHY_NO_ISSUES_BLOCK in body
    assert "APPROVED" in _evidence_rule(body) or "APPROVED" in body[: body.find("Why no issues")]
    assert "MUST" in body[max(0, body.find("Why no issues") - 300): body.find("Why no issues") + 300], (
        f"{agent_path}: the evidence block must be mandatory (MUST) on APPROVED"
    )


@pytest.mark.parametrize("agent_path", ALL_REVIEWERS)
def test_agent_defines_non_trivial_via_shortstat(agent_path: str):
    body = (ROOT / agent_path).read_text(encoding="utf-8")

    assert NON_TRIVIAL_KEYWORD in body.lower()
    start = body.find(SHORTSTAT_KEYWORD)
    assert start != -1, f"{agent_path}: non-trivial must reference `{SHORTSTAT_KEYWORD}`"
    window = body[start: start + 600]
    assert LOC_THRESHOLD in window, f"{agent_path}: {LOC_THRESHOLD}-LOC threshold missing"
    for ext in EXCLUSIONS:
        assert ext in window, f"{agent_path}: non-trivial definition must exclude '{ext}' (cl-5)"


@pytest.mark.parametrize("agent_path", ALL_REVIEWERS)
def test_agent_requires_why_no_issues_block_with_three_verifications(agent_path: str):
    body = (ROOT / agent_path).read_text(encoding="utf-8")

    rule = _evidence_rule(body)
    lowered = rule.lower()
    assert any(
        marker in lowered
        for marker in ("at least 3", "3-5", "3 verifications", "three verifications")
    ), f"{agent_path}: must require at least 3 verifications in the block"
    assert "file:line" in rule, f"{agent_path}: verifications must use the file:line shape"


@pytest.mark.parametrize("agent_path", GOVERNANCE_REVIEWERS)
def test_governance_reviewers_mark_creation_as_always_non_trivial(agent_path: str):
    body = (ROOT / agent_path).read_text(encoding="utf-8")
    lowered = body.lower()

    assert "always non-trivial" in lowered or "always be non-trivial" in lowered, (
        f"{agent_path}: spec/plan creation must be stated ALWAYS non-trivial (Story 3 AC-4)"
    )
