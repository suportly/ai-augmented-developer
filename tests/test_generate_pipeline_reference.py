"""T008 — pipeline-reference generator emits terse table with hand-off links."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "generate_pipeline_reference.py"


def _render(target: Path) -> str:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--output", str(target)],
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.returncode == 0, result.stderr
    return target.read_text(encoding="utf-8")


def test_generator_exists():
    assert SCRIPT.exists(), f"expected {SCRIPT} to exist"


def test_generator_lists_pipeline_skills_with_handoffs(tmp_path):
    output = _render(tmp_path / "pipeline-reference.md")

    # Every pipeline skill appears.
    for skill in [
        "specify",
        "clarify",
        "plan",
        "tasks",
        "implement",
        "analyze",
        "checklist",
        "requesting-code-review",
        "finishing-a-branch",
    ]:
        assert skill in output, f"generator missed pipeline skill {skill}"

    # The arrow-link convention lands at least once, and a multi-handoff
    # skill (e.g. specify → clarify / plan) renders with a slash separator
    # (the pipe character would collide with Markdown table cells).
    assert "→" in output
    assert " / " in output, "multi-handoff rows must use '/' as separator"


def test_generator_is_deterministic(tmp_path):
    first = _render(tmp_path / "first.md")
    second = _render(tmp_path / "second.md")
    assert first == second, "generator output must be deterministic"


def test_generator_skips_non_pipeline_skills(tmp_path):
    """Frontend, constitution, and similar non-pipeline skills are out of scope.

    The help surface is the pipeline — any help skill entry covers itself
    but the generator must not dilute the output with frontend-design or
    other non-pipeline tooling.
    """
    output = _render(tmp_path / "out.md")
    # frontend-design and using-ai-augmented-developer are not pipeline steps.
    assert "frontend-design" not in output
    assert "using-ai-augmented-developer" not in output
