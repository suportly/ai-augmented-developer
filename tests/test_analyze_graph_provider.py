"""T004–T007 — the analyze skill's optional graph-provider integration.

Spec 0017, Story 1 (grounded drift) and Story 3 (confidence). The `analyze`
skill gains an *additive, conditional* provider step: when a knowledge-graph
provider is configured it grounds the gap classes in cited facts; when none
is configured it behaves exactly as before. These tests assert the SKILL.md
instructions are present and unambiguous.
"""
from __future__ import annotations

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
SKILL = REPO_ROOT / "skills" / "analyze" / "SKILL.md"


def _body() -> str:
    return SKILL.read_text(encoding="utf-8")


def test_has_optional_graph_provider_section() -> None:
    body = _body()
    assert "Graph provider (optional)" in body


def test_analyze_declares_task_without_code_provider_step() -> None:
    body = _body()
    assert "Task without code (provider-grounded)" in body
    assert "`drift`" in body and "`missing`" in body
    assert "expected-and-absent `path:symbol`" in body
