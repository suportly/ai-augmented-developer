"""Behavioural content tests for ``skills/implement/SKILL.md``.

Spec: ``specs/0013-implement-task-status-tracking/spec.md`` (Story 3 sc1);
rewritten by spec 0030 (T030) to assert behaviour, not position or
literal prose, so rewrites of the loop section do not break it.

The single tracked source of truth is ``skills/implement/SKILL.md``
(``.claude/skills/`` and ``src/aiadev/_assets/skills/`` are ignored
build artefacts). Set ``AIADEV_PROSE_ROOT`` to point the test at a copy
of the repo text (used to prove the assertions catch regressions).
"""
from __future__ import annotations

import os
import pathlib
import re

ROOT = pathlib.Path(
    os.environ.get("AIADEV_PROSE_ROOT")
    or pathlib.Path(__file__).resolve().parent.parent
)
BARE_SKILL = ROOT / "skills" / "implement" / "SKILL.md"

# Status flip: manual edit of the row marker OR the CLI helper.
_FLIP = re.compile(
    r"\*\*Status:\*\*\s*pending[\s\S]{0,400}?\*\*Status:\*\*\s*done"
    r"|aiadev tasks done",
)
# The flip rides in the same commit as the task's code.
_ATOMIC = re.compile(
    r"atomic|same commit|one (?:git )?commit|(?:code|test)[^.\n]{0,80}together|together[^.\n]{0,60}tasks\.md",
    re.I,
)
# Rollback of the marker when the commit fails.
_ROLLBACK = re.compile(
    r"git restore --staged tasks\.md"
    r"|git checkout -- tasks\.md"
    r"|roll(?:ing)?[ -]?back[^.\n]{0,80}(?:marker|status|tasks\.md)"
    r"|(?:marker|status)[^.\n]{0,80}(?:rolled back|reverted)",
    re.I,
)
_COMMIT_FAILS = re.compile(r"commit (?:fail|is rejected|rejected)|hook (?:reject|fail)|signing error", re.I)


def _text() -> str:
    return BARE_SKILL.read_text(encoding="utf-8")


def test_loop_flips_status_atomically_with_the_commit() -> None:
    """The loop describes flipping the task status to done (manual
    ``**Status:**`` rewrite or ``aiadev tasks done``) inside the same
    commit as the task's files."""
    text = _text()
    assert _FLIP.search(text), "implement skill must describe the pending->done status flip"
    assert _ATOMIC.search(text), "status flip must ride in the same commit as the task code"


def test_loop_rolls_back_the_marker_when_commit_fails() -> None:
    """On commit failure the done marker is rolled back (never --no-verify)."""
    text = _text()
    match = _ROLLBACK.search(text)
    assert match, "implement skill must describe rolling back the status marker"
    window = text[max(0, match.start() - 500): match.end() + 500]
    assert _COMMIT_FAILS.search(window), "rollback must be tied to a failing commit"


def test_orchestrator_owns_tasks_md_not_the_implementer() -> None:
    text = _text()
    assert re.search(
        r"orchestrator[\s\S]{0,300}tasks\.md|tasks\.md[\s\S]{0,300}orchestrator", text, re.I
    ), "the orchestrator must be named as the owner of tasks.md"


def test_loop_emits_preflight_json_and_parallel_reads() -> None:
    """First loop call: preflight as JSON plus the doc reads, in parallel."""
    text = _text()
    assert re.search(r"preflight implement[^\n]*--format json", text)
    assert re.search(r"parallel", text, re.I), "reads must be issued in parallel"
    assert "test_command" in text and "docs" in text, "JSON fields replace rediscovery"


def test_loop_closes_task_with_tasks_done_and_manual_fallback() -> None:
    text = _text()
    assert re.search(r"aiadev tasks done \S+[^\n]*--commit", text)
    assert re.search(r"fallback", text, re.I)
    assert "git restore --staged tasks.md" in text, "manual path stays as fallback"


def test_one_reviewer_per_task_and_no_full_branch_review() -> None:
    text = _text()
    assert re.search(r"single reviewer|one reviewer|reviewer único", text, re.I)
    assert not re.search(r"full-branch review", text, re.I)
    front = text.split("---", 2)[1]
    handoffs = front.split("handoffs:")[1]
    assert handoffs.index("- analyze") < handoffs.index("- requesting-code-review")
    assert re.search(r"hand off to `analyze`[^.\n]*`requesting-code-review`", text)
    assert "CHANGES_REQUESTED" in text and "ISSUES_FOUND" not in text


def test_prose_only_tasks_self_verify_without_reviewer() -> None:
    """Prose tier: lint + validator, no reviewer dispatch, explicit exclusions."""
    text = _text()
    match = re.search(r"^.*[Pp]rose.*$", text, re.M)
    assert match, "prose self-verification tier missing"
    para = text[match.start(): match.start() + 900]
    assert "npx markdownlint-cli2" in para and "scripts/validate_skills.py" in para
    assert re.search(r"do(?:es)? not dispatch a reviewer|without (?:a )?reviewer", para, re.I)
    for excluded in ("docs/instruction-budget.json", "docs/pipeline-path.yaml"):
        assert excluded in para, f"{excluded} must be named as outside the tier"
    for root in ("skills/", "agents/", "rules/", "templates/", "commands/", "src/", "tests/"):
        assert root in para, f"{root} must be named as not prose"


AGENT = ROOT / "agents" / "implementer.md"
_STATUSES = ("DONE", "DONE_WITH_CONCERNS", "NEEDS_CONTEXT", "BLOCKED")


def _effective() -> str:
    """Skill plus the agent it dispatches (rules moved there by spec 0031 T013)."""
    return _text() + "\n" + AGENT.read_text(encoding="utf-8")


def _implementer_prompt() -> str:
    text = _text()
    start = text.index("## Implementer prompt")
    return text[start: text.index("## Status handling")]


def test_step_4_dispatches_the_implementer_agent() -> None:
    step = re.search(r"^4\..*$", _text(), re.M)
    assert step, "step 4 missing"
    assert re.search(r"`implementer` agent", step.group(0))
    assert re.search(r"`implement: <TID> <title>`", step.group(0))


def test_effective_text_keeps_test_first_flow_and_four_statuses() -> None:
    text = _effective()
    assert re.search(r"failing test[\s\S]{0,80}right reason", text)
    assert "Run only the tests that exercise the changed code" in text
    for status in _STATUSES:
        assert f"- {status} " in text, f"{status} status lost"


def test_skill_prompt_carries_only_per_task_context() -> None:
    prompt = _implementer_prompt()
    for needed in ("Task:", "Spec context", "Plan context", "Files to create or modify"):
        assert needed in prompt
    assert "Workflow: test-first" not in prompt
    assert "Return exactly one status" not in prompt
    assert "failing test" not in _text()
    assert "- DONE — complete" not in _text()


def test_status_handling_stays_in_the_skill() -> None:
    text = _text()
    section = text[text.index("## Status handling"): text.index("## Reviewer prompt")]
    for status in _STATUSES:
        assert f"**{status}**" in section


def test_path_lists_the_implementer_agent_at_implement_stage() -> None:
    import yaml

    stages = yaml.safe_load((ROOT / "docs" / "pipeline-path.yaml").read_text(encoding="utf-8"))["stages"]
    files = next(s["files"] for s in stages if s["name"] == "implement")
    assert "agents/implementer.md" in files
