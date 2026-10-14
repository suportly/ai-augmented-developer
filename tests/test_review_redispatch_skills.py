"""Reviewer re-dispatch gate is reachable from the orchestrator skills.

Story 3 sc2/sc3 of ``specs/0014-bmad-inspired-evolutions/spec.md``.
Rewritten by spec 0030 (T030) to assert behaviour instead of a section
header at a fixed position: the gate may live in the SKILL.md itself or
in a ``references/*.md`` file the skill cites (e.g.
``skills/requesting-code-review/references/review-gate.md``). The
"effective text" of a skill is its SKILL.md plus the reference files it
names. Set ``AIADEV_PROSE_ROOT`` to point at a copy of the repo text.

Contract pieces asserted (on the effective text of BOTH skills):

    1. detection of APPROVED without the ``### Why no issues`` block
    2. non-trivial-change definition (cl-5 anchor or preflight pointer)
    3. re-dispatch with reinforced adversarial framing
    4. hard limit of 2 re-dispatches per reviewer
    5. trivial-change exception
    6. write-through to ``.review-log.jsonl`` with the canonical shape
    7. a correction -> re-review iteration limit exists (both loop bounds:
       this plus #4)
"""
from __future__ import annotations

import os
import re
from pathlib import Path

import pytest

ROOT = Path(
    os.environ.get("AIADEV_PROSE_ROOT") or Path(__file__).resolve().parents[1]
)

ORCHESTRATOR_SKILLS = (
    "skills/implement/SKILL.md",
    "skills/requesting-code-review/SKILL.md",
)

_REF = re.compile(r"(?:skills/[\w-]+/)?references/[\w.-]+\.md")


def effective_text(skill_path: str) -> str:
    """SKILL.md plus every ``references/*.md`` file it cites (one level).

    A cited path is resolved relative to the skill directory first, then
    to the repo root (cross-skill references use ``skills/<x>/references``).
    Uncited or missing references are ignored.
    """
    skill = ROOT / skill_path
    body = skill.read_text(encoding="utf-8")
    parts = [body]
    seen: set[Path] = set()
    for ref in _REF.findall(body):
        for base in (skill.parent, ROOT):
            candidate = (base / ref).resolve()
            if candidate.is_file() and candidate not in seen:
                seen.add(candidate)
                parts.append(candidate.read_text(encoding="utf-8"))
                break
    return "\n".join(parts)


@pytest.mark.parametrize("skill_path", ORCHESTRATOR_SKILLS)
def test_gate_is_reachable_and_detects_missing_block(skill_path: str) -> None:
    text = effective_text(skill_path)
    assert re.search(r"re-?dispatch", text, re.I), f"{skill_path}: no re-dispatch gate reachable"
    assert "APPROVED" in text
    assert "### Why no issues" in text, (
        f"{skill_path}: gate must reference the '### Why no issues' block by name"
    )
    # APPROVED and the block must be discussed together (detection rule).
    assert re.search(
        r"APPROVED[\s\S]{0,800}### Why no issues|### Why no issues[\s\S]{0,800}APPROVED", text
    ), f"{skill_path}: APPROVED-without-block detection not described"


@pytest.mark.parametrize("skill_path", ORCHESTRATOR_SKILLS)
def test_gate_anchors_non_trivial_definition(skill_path: str) -> None:
    text = effective_text(skill_path)
    assert "non-trivial" in text.lower()
    assert any(
        anchor in text
        for anchor in (
            "aiadev.review_log",
            "is_non_trivial_change",
            "aiadev preflight requesting-code-review",
            "cl-5",
        )
    ), f"{skill_path}: gate must point at the canonical non-trivial definition"


@pytest.mark.parametrize("skill_path", ORCHESTRATOR_SKILLS)
def test_gate_uses_reinforced_adversarial_framing(skill_path: str) -> None:
    lowered = effective_text(skill_path).lower()
    assert re.search(r"re-?dispatch[\s\S]{0,1500}adversarial|adversarial[\s\S]{0,1500}re-?dispatch", lowered)
    assert "at least one bug" in lowered, (
        f"{skill_path}: gate must reproduce the 'assume at least one bug' escalation"
    )


@pytest.mark.parametrize("skill_path", ORCHESTRATOR_SKILLS)
def test_redispatch_limit_is_two_per_reviewer(skill_path: str) -> None:
    lowered = effective_text(skill_path).lower()
    assert re.search(r"\b(?:2|two) re-?dispatch", lowered), (
        f"{skill_path}: must state the 2 re-dispatches hard limit"
    )
    assert re.search(r"per reviewer|per (?:task|review pass)", lowered)


@pytest.mark.parametrize("skill_path", ORCHESTRATOR_SKILLS)
def test_gate_excepts_trivial_changes(skill_path: str) -> None:
    lowered = effective_text(skill_path).lower()
    exception = r"does not apply|do not re-?dispatch|not re-?dispatch|no re-?dispatch|silently|accept[^.]{0,30}approved"
    assert re.search(
        rf"\b(?<!non-)trivial[^.]{{0,200}}(?:{exception})|(?:{exception})[^.]{{0,200}}\b(?<!non-)trivial",
        lowered,
    ), f"{skill_path}: trivial-change carve-out must be explicit"


@pytest.mark.parametrize("skill_path", ORCHESTRATOR_SKILLS)
def test_gate_writes_review_log_entry(skill_path: str) -> None:
    text = effective_text(skill_path)
    assert ".review-log.jsonl" in text
    for field in ("timestamp", "reviewer", "verdict", "has_why_no_issues_block", "task_id"):
        assert field in text, f"{skill_path}: review-log entry field {field!r} missing"


def test_correction_rereview_limit_exists() -> None:
    number = r"(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten)"
    noun = r"(?:iterations?|rounds?|attempts?|cycles?|loops?|passes|review (?:rounds|passes))"
    pattern = re.compile(
        rf"(?:after|exceeds?|more than|up to|at most|max\w*|limit\w*)[^.\n]{{0,40}}?\b{number}\b[^.\n]{{0,30}}?\b{noun}\b",
        re.I,
    )
    assert any(
        pattern.search(effective_text(s)) for s in ORCHESTRATOR_SKILLS
    ), "no correction -> re-review iteration limit stated in implement or requesting-code-review"


def _implement_prompt() -> str:
    text = effective_text("skills/implement/SKILL.md")
    start = text.index("## Reviewer prompt")
    return text[start: text.index("## Reviewer re-dispatch gate")]


def test_single_reviewer_prompt_runs_conformance_then_quality_and_stops() -> None:
    prompt = _implement_prompt()
    low = prompt.lower()
    assert low.index("conformance") < low.index("quality")
    assert re.search(r"stop[^.\n]{0,80}(skip|without|no)[^.\n]{0,40}quality|skip[^.\n]{0,20}quality", low)
    assert "CHANGES_REQUESTED" in prompt
    assert re.search(r"diff", low) and re.search(r"test output", low)
    assert re.search(r"not (?:paste|whole files)|no whole files|excerpt", low)


def test_implement_keeps_both_iteration_limits_and_log_names_code_reviewer() -> None:
    text = effective_text("skills/implement/SKILL.md")
    assert re.search(r"\b2 re-dispatches per reviewer", text)
    assert re.search(r"exceeds?\s+\d+\s+iterations|after\s+\d+\s+(?:fix|correction)", text, re.I)
    assert '"reviewer": "code-reviewer"' in text


def test_code_reviewer_agent_absorbs_conformance_checklist() -> None:
    agent = (ROOT / "agents/code-reviewer.md").read_text(encoding="utf-8")
    assert "### Why no issues" in agent
    assert re.search(
        r"stop:[^\n]{0,40}CHANGES_REQUESTED with only those[^\n]{0,40}skip", agent
    ), "per-task stop rule missing"
    assert re.search(r"branch[^\n]{0,160}stop rule does not apply", agent, re.I)
    assert re.search(r"Scope under review: a task or the branch", agent)
    assert re.search(r"each acceptance", agent, re.I)
    assert "architectural refactors beyond the scope" in agent
    assert "weren't in the spec" in agent


GATE = "skills/requesting-code-review/references/review-gate.md"
# Regexes run on whitespace-collapsed lowercase text (tolerant to reflow).
GATE_MARKERS = (
    r"assume there is at least one bug",
    r"2 re-dispatches per reviewer",
    r"reviewer exhausted re-dispatch budget",
    r"has_why_no_issues_block",
    r"> 10 loc",
    r"\"task_id\": <tid>",
    r"branch-review",
    r"≥ 3",
    r"always non-trivial",
    r"same reviewer",
    r"and proceed",
    r"<base>\.\.\.head",
)
# Separate group: T050 removes terse-mode; drop only this tuple then.
TERSE_MARKERS = (r"🟢 file:line",)
# Agents legitimately keep this part of their own output rule.
AGENT_KEEPS = (r"always non-trivial",)
REFERENCING = (
    "skills/implement/SKILL.md",
    "skills/requesting-code-review/SKILL.md",
    "agents/code-reviewer.md",
    "agents/spec-document-reviewer.md",
    "agents/plan-document-reviewer.md",
)


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower())


def test_gate_text_lives_only_in_canonical_file() -> None:
    gate = _norm((ROOT / GATE).read_text(encoding="utf-8"))
    for marker in GATE_MARKERS + TERSE_MARKERS:
        assert re.search(marker, gate), f"gate file lacks {marker!r}"
    for path in REFERENCING:
        raw = (ROOT / path).read_text(encoding="utf-8")
        assert "references/review-gate.md" in raw, f"{path} does not cite the gate"
        norm = _norm(raw)
        for marker in GATE_MARKERS:
            if path.startswith("agents/") and marker in AGENT_KEEPS:
                continue
            assert not re.search(marker, norm), f"{path} duplicates gate text {marker!r}"
