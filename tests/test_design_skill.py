"""design skill (spec 0033 T004): rules pinned by key phrases."""
from __future__ import annotations

import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = (ROOT / "skills" / "design" / "SKILL.md").read_text(encoding="utf-8")
_, FRONT, BODY = RAW.split("---\n", 2)
DESC = re.search(r"^description:\s*(.+)$", FRONT, re.M).group(1).strip()  # type: ignore[union-attr]
LOW = BODY.lower()


def test_name_and_handoffs() -> None:
    assert re.search(r"^name: design$", FRONT, re.M)
    assert "- tasks" in FRONT and "- implement" in FRONT
    assert "specs/<branch>/design.md" in FRONT


def test_description_within_30_tokens() -> None:
    assert math.ceil(len(DESC) / 4) <= 30


def test_body_within_budget() -> None:
    assert math.ceil(len(BODY) / 4) <= 700


def test_no_announce_at_start() -> None:
    assert "announce at start" not in LOW


def test_no_fixed_url_or_vendor() -> None:
    assert "claude.ai/artifact" not in RAW.lower()
    assert "http" not in LOW
    for word in ("anthropic", "vercel", "figma", "claude design"):
        assert word not in RAW.lower(), word


def test_preflight_command() -> None:
    assert "`aiadev preflight design --feature <slug>`" in BODY


def test_ui_yes_warn_and_ask() -> None:
    assert "lacks `**ui:** yes`" in LOW
    assert "warn that the feature declares no ui and ask whether to continue" in LOW


def test_task_list_confirmed_before_continuing() -> None:
    assert "read `spec.md`, `plan.md` and `tasks.md`" in LOW
    assert "continue only after the user confirms or adjusts it" in LOW


def test_brief_content_whitelist() -> None:
    assert "screens, given/when/then scenarios" in LOW
    assert "states (empty, error, loading)" in LOW
    assert "texts defined in the spec" in LOW


def test_brief_forbidden_content() -> None:
    assert "never include file paths, commit hashes, task ids or internal module names" in LOW
    assert "only scenarios and texts present in the spec" in LOW


def test_confirm_before_publishing() -> None:
    assert "show exactly what will be sent" in LOW
    assert "only after explicit user confirmation" in LOW


def test_private_canvas_one_artboard_per_screen() -> None:
    assert "canvas is private, one artboard per screen" in LOW


def test_artifact_quickstart_design_intent() -> None:
    assert "`artifact` tool" in LOW
    assert "`action: quickstart` with `intent: design`" in LOW
    assert "follow its result" in LOW


def test_subagent_description_and_return() -> None:
    assert "`description` `design: <slug>`" in LOW
    assert "returns only the link and the screen map" in LOW


def test_no_design_system_setup() -> None:
    assert "do not configure or ask for a design system" in LOW


def test_design_md_from_template() -> None:
    assert "`specs/<feature>/design.md`" in LOW
    assert "`templates/design-template.md`" in LOW
    assert "screen to scenario to task map" in LOW


def test_gaps_cite_scenario_or_say_none() -> None:
    assert "cites the spec scenario that motivates it, or says there is none" in LOW


def test_amendment_after_approval_via_tasks() -> None:
    assert "only after approval, through the `tasks` skill" in LOW


def test_no_artifact_tool_fallback() -> None:
    assert re.search(r"no `artifact` tool[^\n]*could not create the prototype[^\n]*markdown wireframes", LOW)


def test_creation_failure_fallback() -> None:
    assert re.search(r"creation fails[^\n]*record no link[^\n]*give the reason[^\n]*offer wireframes", LOW)


def test_handoff_implement() -> None:
    assert "hand off to `implement`" in LOW
