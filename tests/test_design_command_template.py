"""T005: /aia:design command and design.md template."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CMD = (ROOT / "commands" / "design.md").read_text(encoding="utf-8")
TPL = (ROOT / "templates" / "design-template.md").read_text(encoding="utf-8")
TASKS_CMD = (ROOT / "commands" / "tasks.md").read_text(encoding="utf-8")


def _front(text: str) -> dict[str, str]:
    block = text.split("---")[1]
    return dict(re.findall(r"^([\w-]+):\s*(.*)$", block, re.M))


def test_command_has_same_mold_as_tasks() -> None:
    front, ref = _front(CMD), _front(TASKS_CMD)
    assert set(front) == set(ref)
    assert front["description"]
    assert "$ARGUMENTS" in CMD


def test_command_invokes_design_skill_and_declares_tools() -> None:
    assert "`design` skill" in CMD
    tools = {t.strip() for t in _front(CMD)["allowed-tools"].split(",")}
    assert {"Read", "Write", "Edit", "Glob", "Grep", "Bash", "Task", "Artifact"} <= tools


def test_template_has_blocks() -> None:
    for heading in ("## Prototype", "## Screen map", "## Gaps", "## Wireframes"):
        assert heading in TPL
    assert "| Screen | Scenario | Task |" in TPL
    assert "scenario" in TPL.split("## Gaps")[1].split("## Wireframes")[0]
    wire = TPL.split("## Wireframes")[1].lower()
    assert "alternative" in wire and "no prototype" in wire
    for ph in ("{{FEATURE_NAME}}", "{{BRANCH}}", "{{DOC_LANGUAGE}}", "{{DATE}}"):
        assert ph in TPL


def test_template_asks_no_path_or_commit() -> None:
    low = TPL.lower()
    assert "commit" not in low and "hash" not in low and "sha" not in low
    assert not re.search(r"\b\w+/\w+\.\w+|\bpath\b|file path", low)


def test_design_not_in_pipeline_path() -> None:
    text = (ROOT / "docs" / "pipeline-path.yaml").read_text(encoding="utf-8")
    assert not re.search(r"\bdesign\b", text)
