"""T028 — E2E: specify → clarify → plan → tasks via Python lib + fake LLM.

Covers Story 2 sc1, sc2, sc3.
"""
from __future__ import annotations

import pathlib
import re


def _extract_h2_headers(text: str) -> set[str]:
    return {m.group(1).strip() for m in re.finditer(r"^## (.+)$", text, re.MULTILINE)}


def test_full_pipeline_e2e(
    framework_root: pathlib.Path, tmp_path: pathlib.Path
) -> None:
    from aiadev.tools import clarify, plan, specify, tasks
    from tests._fakes.llm import execute_payload

    # Step 1: specify
    spec_payload = specify(demand="E2E pipeline test", workspace_path=str(tmp_path))
    spec_path = execute_payload(spec_payload)
    assert spec_path.exists()
    spec_content = spec_path.read_text(encoding="utf-8")

    # Step 2: clarify (if markers exist)
    markers = spec_payload.get("existing_markers", [])
    if markers:
        cl_markers = [m for m in markers if m["id"] is not None]
        if cl_markers:
            answers = [{"id": m["id"], "answer": "Resolved by E2E test."} for m in cl_markers]
            clarify_payload = clarify(
                spec_path=str(spec_path),
                workspace_path=str(tmp_path),
                answers=answers,
            )
            assert clarify_payload["skill"] == "clarify"

    # Step 3: plan
    plan_payload = plan(spec_path=str(spec_path), workspace_path=str(tmp_path))
    plan_path = execute_payload(plan_payload)
    assert plan_path.exists()
    plan_content = plan_path.read_text(encoding="utf-8")

    plan_template = framework_root / "templates" / "plan-template.md"
    plan_headers = _extract_h2_headers(plan_template.read_text(encoding="utf-8"))
    actual_headers = _extract_h2_headers(plan_content)
    missing = plan_headers - actual_headers
    assert not missing, f"plan.md missing sections: {missing}"

    # Step 4: tasks
    tasks_payload = tasks(plan_path=str(plan_path), workspace_path=str(tmp_path))
    tasks_path = execute_payload(tasks_payload)
    assert tasks_path.exists()
    tasks_content = tasks_path.read_text(encoding="utf-8")

    tasks_template = framework_root / "templates" / "tasks-template.md"
    tasks_headers = _extract_h2_headers(tasks_template.read_text(encoding="utf-8"))
    actual_tasks_headers = _extract_h2_headers(tasks_content)
    missing_tasks = tasks_headers - actual_tasks_headers
    assert not missing_tasks, f"tasks.md missing sections: {missing_tasks}"
