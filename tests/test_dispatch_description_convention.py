"""Dispatch ``description`` convention (spec 0030 T035, Story 1 sc2).

``aiadev.token_metrics`` classifies a subagent only by the
``implement:`` / ``review:`` prefix of its ``description``; the skills
that dispatch must state it. Document reviewers (specify, plan) stay
unclassified on purpose.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

ROOT = Path(os.environ.get("AIADEV_PROSE_ROOT") or Path(__file__).resolve().parents[1])


def _skill(name: str) -> str:
    return (ROOT / "skills" / name / "SKILL.md").read_text(encoding="utf-8")


def test_implement_declares_task_dispatch_prefixes() -> None:
    text = _skill("implement")
    assert re.search(r"description[^\n]*`implement: <TID>", text)
    assert re.search(r"description[^\n]*`review: <TID>", text)


def test_implement_step_4_names_the_implementer_agent() -> None:
    assert re.search(r"4\.[^\n]*`implementer` agent[^\n]*`implement: <TID>", _skill("implement"))


def test_requesting_code_review_declares_branch_prefix() -> None:
    assert re.search(r"description[^\n]*`review: branch <slug>`", _skill("requesting-code-review"))


def test_document_reviewers_are_not_classified() -> None:
    for name in ("specify", "plan"):
        assert not re.search(r"description[^\n]*`(?:implement|review):", _skill(name))


def test_prefix_convention_matches_token_metrics(tmp_path: Path) -> None:
    from aiadev import token_metrics as tm

    cases = {
        "implement: T003 titulo": tm.ROLE_IMPLEMENT,
        "review: T003 titulo": tm.ROLE_REVIEW,
        "review: branch 0030-lean-pipeline": tm.ROLE_REVIEW,
        "Review spec document": tm.ROLE_UNCLASSIFIED,
    }
    for i, (desc, role) in enumerate(cases.items()):
        agent = tmp_path / f"agent-{i}.jsonl"
        (tmp_path / f"agent-{i}.meta.json").write_text(
            '{"description": %s}' % __import__("json").dumps(desc), encoding="utf-8"
        )
        assert tm._subagent_role(agent) == role


def test_implement_description_of_the_agent_dispatch_keeps_implement_role(tmp_path: Path) -> None:
    """The dispatch the skill now prescribes (agent ``implementer``) still lands
    in role ``implement``: the role comes from the description prefix, and the
    skill's own template must produce one."""
    import json

    from aiadev import token_metrics as tm

    template = re.search(r"`(implement: <TID> <title>)`", _skill("implement"))
    assert template
    desc = template.group(1).replace("<TID>", "T013").replace("<title>", "despacho")
    (tmp_path / "agent-x.meta.json").write_text(json.dumps({"description": desc}), encoding="utf-8")
    assert tm._subagent_role(tmp_path / "agent-x.jsonl") == tm.ROLE_IMPLEMENT
