"""Assemble ToolPayload for aiadev.tools and aiadev.mcp_server."""
from __future__ import annotations

import pathlib
import re
from typing import Any

import aiadev

from . import SpecInvalidError
from .markers import enumerate_markers, needs_renumbering, next_id
from .skill_loader import load_skill
from .workspace import assert_within, compute_target_path, validate_workspace

_SPEC_REQUIRED_SECTIONS = {
    "Problem", "Users and stakeholders", "Success criteria", "Non-goals",
    "User stories", "Clarifications", "Data touched", "Out-of-band effects",
    "Open risks", "Traceability",
}

_CL_N_REGEX_PCRE = (
    r"\[NEEDS CLARIFICATION:cl-(?P<id>[1-9][0-9]*)\s+(?P<question>[^\]]+)\]"
)


def build(
    skill: str,
    framework_root: pathlib.Path,
    workspace_path: str | pathlib.Path,
    *,
    demand: str = "",
    spec_path: str | None = None,
    plan_path: str | None = None,
    language: str = "en",
    overwrite: bool = False,
    **kwargs: Any,
) -> dict[str, Any]:
    """Build a ToolPayload dict ready for JSON serialisation.

    The payload contains: the skill prompt, template, constitution excerpt,
    computed target_path, marker_format metadata, and existing_markers.
    """
    ws = validate_workspace(workspace_path)
    loaded = load_skill(
        skill, framework_root,
        spec_path=pathlib.Path(spec_path) if spec_path else None,
    )

    prompt = loaded["prompt"]
    if language != "en":
        prompt += f"\n\n**Language override:** write all artifact content in `{language}`."

    target = compute_target_path(
        ws, demand or skill, _artifact_for(skill), overwrite=overwrite,
    )

    assert_within(ws, target)

    extra_files: list[dict[str, str]] = []
    spec_text = ""
    if spec_path:
        sp = pathlib.Path(spec_path)
        if sp.is_file():
            content = sp.read_text(encoding="utf-8")
            extra_files.append({"path": str(sp), "content": content})
            spec_text = content
            if skill in ("plan", "tasks", "clarify"):
                _validate_spec_sections(content, str(sp))
    if plan_path:
        pp = pathlib.Path(plan_path)
        if pp.is_file():
            extra_files.append({"path": str(pp), "content": pp.read_text(encoding="utf-8")})

    markers = enumerate_markers(spec_text)
    marker_entries = [
        {
            "id": m["id"],
            "question": m["question"],
            "location": {"path": spec_path or "", "line": 0},
        }
        for m in markers
    ]

    return {
        "skill": skill,
        "version": getattr(aiadev, "__version__", "0.0.0"),
        "prompt": prompt,
        "context": {
            "template": loaded["template"],
            "constitution_excerpt": loaded["constitution_excerpt"],
            "extra_files": extra_files if extra_files else [],
        },
        "target_path": str(target),
        "marker_format": {
            "regex": _CL_N_REGEX_PCRE,
            "next_id": next_id(spec_text),
        },
        "existing_markers": marker_entries if marker_entries else [],
        "needs_renumbering": needs_renumbering(spec_text) if spec_text else False,
    }


def _validate_spec_sections(content: str, path: str) -> None:
    """Raise SpecInvalidError if mandatory spec sections are missing."""
    headers = {m.group(1).strip() for m in re.finditer(r"^## (.+)$", content, re.MULTILINE)}
    missing = _SPEC_REQUIRED_SECTIONS - headers
    if missing:
        raise SpecInvalidError(
            f"Spec {path} is missing required sections: {sorted(missing)}"
        )


def _artifact_for(skill: str) -> str:
    return {
        "specify": "spec.md",
        "clarify": "spec.md",
        "plan": "plan.md",
        "tasks": "tasks.md",
        "implement": "tasks.md",
        "analyze": "spec.md",
        "checklist": "plan.md",
        "constitution": "constitution.md",
    }[skill]
