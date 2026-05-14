"""T009 — Reviewer re-dispatch gate is documented in orchestrator skills.

Story 3 sc2/sc3 of ``specs/0014-bmad-inspired-evolutions/spec.md`` makes
the orchestrator (``skills/implement/SKILL.md`` and
``skills/requesting-code-review/SKILL.md``) responsible for detecting
APPROVED-without-``### Why no issues``-block on a non-trivial change and
re-dispatching the reviewer with reinforced adversarial framing.

The agent-side rule lives in ``agents/<reviewer>.md`` (T004). This test
asserts the orchestrator-side counterpart is documented in BOTH
orchestrator skills as a dedicated section, and that section names the
six load-bearing pieces of the contract:

    1. detection of APPROVED without the ``### Why no issues`` block
    2. non-trivial-change definition (cl-5 anchor or preflight pointer)
    3. re-dispatch with reinforced adversarial framing
    4. hard limit of 2 re-dispatches per reviewer per task
    5. trivial-change exception (no re-dispatch on noise)
    6. write-through to ``specs/<branch>/.review-log.jsonl`` with the
       canonical entry shape

Pure content assertions; no shell-out, no git operations, no fixtures.
"""
from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

ORCHESTRATOR_SKILLS = (
    "skills/implement/SKILL.md",
    "skills/requesting-code-review/SKILL.md",
)

# A unique heading that announces the gate in both skills. Either an H2
# or H3 is acceptable so the section can nest under the reviewer prompt
# subsections in skills/implement/SKILL.md if the author prefers.
SECTION_HEADERS = (
    "## Reviewer re-dispatch gate",
    "### Reviewer re-dispatch gate",
    "## Re-dispatch gate",
    "### Re-dispatch gate",
)


def _section_text(body: str) -> str:
    """Return the section starting at the first matching header up to the
    next H2 (``\\n## ``) or end-of-file. Fail loudly if no header found."""
    for header in SECTION_HEADERS:
        idx = body.find(header)
        if idx != -1:
            # Find the next H2 boundary AFTER the header (allow nested H3
            # within the section).
            after = body.find("\n## ", idx + len(header))
            return body[idx:] if after == -1 else body[idx:after]
    raise AssertionError(
        "no re-dispatch gate section header found; expected one of: "
        + ", ".join(repr(h) for h in SECTION_HEADERS)
    )


@pytest.mark.parametrize("skill_path", ORCHESTRATOR_SKILLS)
def test_skill_declares_redispatch_gate_section(skill_path: str) -> None:
    body = (ROOT / skill_path).read_text(encoding="utf-8")

    found = any(header in body for header in SECTION_HEADERS)
    assert found, (
        f"{skill_path} must declare a re-dispatch gate section "
        f"(one of: {SECTION_HEADERS})"
    )


@pytest.mark.parametrize("skill_path", ORCHESTRATOR_SKILLS)
def test_redispatch_gate_describes_block_detection(skill_path: str) -> None:
    body = (ROOT / skill_path).read_text(encoding="utf-8")
    section = _section_text(body)

    assert "APPROVED" in section, (
        f"{skill_path} re-dispatch gate must describe detecting an "
        f"APPROVED verdict"
    )
    assert "### Why no issues" in section, (
        f"{skill_path} re-dispatch gate must reference the "
        f"'### Why no issues' block by name"
    )


@pytest.mark.parametrize("skill_path", ORCHESTRATOR_SKILLS)
def test_redispatch_gate_anchors_non_trivial_definition(skill_path: str) -> None:
    body = (ROOT / skill_path).read_text(encoding="utf-8")
    section = _section_text(body)
    lowered = section.lower()

    assert "non-trivial" in lowered, (
        f"{skill_path} re-dispatch gate must define when the rule applies "
        f"using the term 'non-trivial'"
    )
    # Must point at the canonical cl-5 anchor: either the helper module
    # name OR the preflight subcommand. Either reference resolves the
    # definition for the reader.
    has_anchor = (
        "aiadev.review_log" in section
        or "is_non_trivial_change" in section
        or "aiadev preflight requesting-code-review" in section
        or "cl-5" in section
    )
    assert has_anchor, (
        f"{skill_path} re-dispatch gate must point at the canonical "
        f"non-trivial definition (cl-5 / aiadev.review_log / preflight)"
    )


@pytest.mark.parametrize("skill_path", ORCHESTRATOR_SKILLS)
def test_redispatch_gate_uses_reinforced_adversarial_framing(skill_path: str) -> None:
    body = (ROOT / skill_path).read_text(encoding="utf-8")
    section = _section_text(body)
    lowered = section.lower()

    assert "re-dispatch" in lowered, (
        f"{skill_path} gate must instruct the orchestrator to re-dispatch"
    )
    assert "adversarial" in lowered, (
        f"{skill_path} gate must call the second prompt 'adversarial' "
        f"(reinforced framing per spec Story 3 sc2)"
    )
    # Spec sc2 quotes the reinforcement: "assume there is at least one bug"
    # — the orchestrator must echo that wording (or close to it) so the
    # reviewer sees the framing escalation, not a polite "please retry".
    assert "at least one bug" in lowered, (
        f"{skill_path} gate must reproduce the 'assume at least one bug' "
        f"reinforcement from spec Story 3 sc2"
    )


@pytest.mark.parametrize("skill_path", ORCHESTRATOR_SKILLS)
def test_redispatch_gate_states_two_redispatch_hard_limit(skill_path: str) -> None:
    body = (ROOT / skill_path).read_text(encoding="utf-8")
    section = _section_text(body)
    lowered = section.lower()

    # Plan ADR-4 risk mitigation: max 2 re-dispatches per reviewer per task.
    assert "2 re-dispatches" in lowered or "two re-dispatches" in lowered, (
        f"{skill_path} gate must state the '2 re-dispatches' hard limit "
        f"(plan ADR-4 risk mitigation)"
    )
    # Scope: per reviewer per task (or per reviewer per review pass for
    # the branch-level skill).
    assert "per reviewer" in lowered, (
        f"{skill_path} gate must scope the limit 'per reviewer'"
    )


@pytest.mark.parametrize("skill_path", ORCHESTRATOR_SKILLS)
def test_redispatch_gate_excepts_trivial_changes(skill_path: str) -> None:
    body = (ROOT / skill_path).read_text(encoding="utf-8")
    section = _section_text(body)
    lowered = section.lower()

    # Story 3 sc3: trivial diff with APPROVED-without-block must NOT
    # trigger re-dispatch. The exception must be explicit.
    assert "trivial" in lowered, (
        f"{skill_path} gate must call out the 'trivial' exception"
    )
    has_exception_phrasing = (
        "does not apply" in lowered
        or "do not re-dispatch" in lowered
        or "not re-dispatch" in lowered
        or "no re-dispatch" in lowered
        or "accept approved" in lowered
        or "silently" in lowered
    )
    assert has_exception_phrasing, (
        f"{skill_path} gate must phrase the trivial-change carve-out "
        f"explicitly (e.g. 'does not apply', 'do not re-dispatch')"
    )


@pytest.mark.parametrize("skill_path", ORCHESTRATOR_SKILLS)
def test_redispatch_gate_writes_review_log_entry(skill_path: str) -> None:
    body = (ROOT / skill_path).read_text(encoding="utf-8")
    section = _section_text(body)

    assert ".review-log.jsonl" in section, (
        f"{skill_path} gate must instruct the orchestrator to append a "
        f"row to specs/<branch>/.review-log.jsonl"
    )
    # The five entry-shape fields pinned by tests/test_review_log.py.
    for field in (
        "timestamp",
        "reviewer",
        "verdict",
        "has_why_no_issues_block",
        "task_id",
    ):
        assert field in section, (
            f"{skill_path} gate must mention review-log entry field "
            f"{field!r}"
        )
