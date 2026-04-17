"""Deterministic fake LLM that follows a ToolPayload prompt to create artifacts.

This fake does NOT validate content quality (user stories, acceptance
scenarios, etc.) — it only produces structurally-valid artifacts by
copying the template and filling placeholders. Quality validation
requires a real LLM and is covered by manual smoke tests.
"""
from __future__ import annotations

import pathlib
import re
from datetime import date
from typing import Any


def execute_payload(payload: dict[str, Any]) -> pathlib.Path:
    """Follow a ToolPayload's instructions: create the target artifact.

    Returns the path to the created file.
    """
    target = pathlib.Path(payload["target_path"])
    target.parent.mkdir(parents=True, exist_ok=True)

    template_content = payload["context"]["template"]["content"]
    skill = payload["skill"]

    content = _fill_template(template_content, payload)

    if skill == "specify":
        content = _add_fake_spec_content(content, payload)
    elif skill == "plan":
        content = _add_fake_plan_content(content)
    elif skill == "tasks":
        content = _add_fake_tasks_content(content)

    target.write_text(content, encoding="utf-8")
    return target


def _fill_template(template: str, payload: dict[str, Any]) -> str:
    slug = pathlib.Path(payload["target_path"]).parent.name
    spec_id = re.match(r"(\d+)-", slug)
    replacements = {
        "{{FEATURE_NAME}}": payload.get("context", {}).get("demand", "Test Feature"),
        "{{BRANCH}}": f"feature/{slug}",
        "{{DATE}}": str(date.today()),
        "{{SPEC_ID}}": spec_id.group(1) if spec_id else "0001",
        "{{DOC_LANGUAGE}}": "en",
        "{{PRESET_NAME}}": "lean",
        "{{LANGUAGE}}": "Python 3.11+",
        "{{DEPS}}": "click, pyyaml, jsonschema, rich",
        "{{STORAGE}}": "N/A",
        "{{TEST_FRAMEWORK}}": "pytest",
        "{{TARGETS}}": "Linux/macOS",
        "{{PERF_BUDGET_OR_NA}}": "N/A",
        "{{SECURITY_NOTES}}": "N/A",
        "{{SHORT_TITLE}}": "Test story",
        "{{ROLE}}": "developer",
        "{{ACTION}}": "use the tool",
        "{{OUTCOME}}": "artifacts are generated",
        "{{ISSUE_URL}}": "N/A",
        "{{LIST_OR_NONE}}": "None",
        "{{PHASE_1_NAME}}": "Phase 1",
        "{{PHASE_2_NAME}}": "Phase 2",
        "{{RISK}}": "None identified",
        "{{MITIGATION}}": "N/A",
        "{{AREA}}": "test",
        "{{TEST_COMMAND}}": "pytest -ra",
    }
    result = template
    for key, value in replacements.items():
        result = result.replace(key, value)
    return result


def _add_fake_spec_content(content: str, payload: dict[str, Any]) -> str:
    content = content.replace(
        "<!-- 2-3 sentences. What is broken",
        "Test problem description.\n\n<!-- 2-3 sentences. What is broken",
    )
    next_id = payload.get("marker_format", {}).get("next_id", 1)
    marker = f"[NEEDS CLARIFICATION:cl-{next_id} Is this a test marker?]"

    if "## User stories" in content:
        story = (
            "\n### Story 1 — Test story (P1)\n\n"
            "As a developer, I want to test so that tests pass.\n\n"
            "**Acceptance scenarios** (Given / When / Then):\n\n"
            "1. Given a test, When it runs, Then it passes.\n"
            "2. Given an edge case, When it runs, Then it handles it.\n"
            "3. Given an error, When it runs, Then it reports it.\n"
        )
        content = content.replace("### Story 1 —", story + "\n### Story 1 —")

    content = content.replace(
        f"- [NEEDS CLARIFICATION:cl-1 example",
        f"- {marker}\n- [NEEDS CLARIFICATION:cl-1 example",
    )
    return content


def _add_fake_plan_content(content: str) -> str:
    if "| I. Spec-first" in content:
        content = content.replace("PASS / FAIL / N/A | `spec.md` approved", "PASS | spec.md approved on 2026-01-01")
    return content


def _add_fake_tasks_content(content: str) -> str:
    if "### T001 —" in content:
        content = content.replace("pending", "pending")
    return content
