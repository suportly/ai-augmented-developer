"""T027 — E2E: specify → fake LLM → spec.md satisfies template.

Story 1 sc2: the caller follows the prompt and the resulting artifact
contains all mandatory sections from templates/spec-template.md.
"""
from __future__ import annotations

import pathlib
import re


def _extract_h2_headers(text: str) -> set[str]:
    return {m.group(1).strip() for m in re.finditer(r"^## (.+)$", text, re.MULTILINE)}


def test_specify_e2e_produces_template_compliant_spec(
    framework_root: pathlib.Path, tmp_path: pathlib.Path
) -> None:
    from aiadev.tools import specify
    from tests._fakes.llm import execute_payload

    payload = specify(demand="test feature for E2E", workspace_path=str(tmp_path))
    target = execute_payload(payload)

    assert target.exists(), f"Artifact not created at {target}"

    template_path = framework_root / "templates" / "spec-template.md"
    template_headers = _extract_h2_headers(template_path.read_text(encoding="utf-8"))
    artifact_headers = _extract_h2_headers(target.read_text(encoding="utf-8"))

    missing = template_headers - artifact_headers
    assert not missing, (
        f"spec.md is missing sections from the template: {missing}. "
        f"Template has: {sorted(template_headers)}. "
        f"Artifact has: {sorted(artifact_headers)}."
    )


def test_specify_e2e_contains_user_story_with_scenarios(
    framework_root: pathlib.Path, tmp_path: pathlib.Path
) -> None:
    from aiadev.tools import specify
    from tests._fakes.llm import execute_payload

    payload = specify(demand="test feature", workspace_path=str(tmp_path))
    target = execute_payload(payload)
    content = target.read_text(encoding="utf-8")

    assert "### Story 1" in content or "### Story" in content, (
        "spec.md must contain at least one user story"
    )
    scenario_count = len(re.findall(r"^\d+\.\s+Given", content, re.MULTILINE))
    assert scenario_count >= 3, (
        f"User story must have >= 3 Given/When/Then scenarios, found {scenario_count}"
    )
