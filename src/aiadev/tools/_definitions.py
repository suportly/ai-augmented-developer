"""Build the tool catalog from SKILL.md frontmatter."""
from __future__ import annotations

import pathlib
from typing import Any

import yaml

from aiadev._tooling.skill_loader import PIPELINE_SKILLS

_BASE_INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["workspace_path"],
    "properties": {
        "workspace_path": {
            "type": "string",
            "description": "Absolute path to the consumer's workspace directory.",
        },
    },
}

_EXTRA_PROPERTIES: dict[str, dict[str, Any]] = {
    "specify": {
        "demand": {"type": "string", "description": "Feature request in free-form natural language."},
        "language": {"type": "string", "description": "BCP-47 language tag.", "default": "en"},
    },
    "clarify": {
        "spec_path": {"type": "string", "description": "Path to the spec.md file."},
        "answers": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "answer"],
                "properties": {
                    "id": {"type": "string", "pattern": "^cl-[1-9][0-9]*$"},
                    "answer": {"type": "string"},
                },
            },
        },
    },
    "plan": {
        "spec_path": {"type": "string", "description": "Path to the approved spec.md."},
    },
    "tasks": {
        "plan_path": {"type": "string", "description": "Path to the approved plan.md."},
    },
    "implement": {
        "plan_path": {"type": "string", "description": "Path to plan.md."},
        "tasks_path": {"type": "string", "description": "Path to tasks.md."},
    },
    "analyze": {
        "spec_path": {"type": "string"},
        "plan_path": {"type": "string"},
    },
    "checklist": {
        "spec_path": {"type": "string"},
        "category": {"type": "string", "description": "security | performance | a11y | i18n | privacy | observability"},
    },
    "constitution": {
        "article": {"type": "string", "description": "Article to amend (optional)."},
    },
}


def _extract_description(skill_path: pathlib.Path) -> str:
    text = skill_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return ""
    body: list[str] = []
    for line in lines[1:]:
        if line.strip() == "---":
            break
        body.append(line)
    parsed = yaml.safe_load("\n".join(body))
    return parsed.get("description", "") if isinstance(parsed, dict) else ""


def list_definitions(framework_root: pathlib.Path) -> list[dict[str, Any]]:
    """Return tool definitions for the 8 pipeline skills."""
    result: list[dict[str, Any]] = []
    for name in sorted(PIPELINE_SKILLS):
        skill_file = framework_root / "skills" / name / "SKILL.md"
        if not skill_file.is_file():
            continue
        description = _extract_description(skill_file)
        schema = dict(_BASE_INPUT_SCHEMA)
        schema["properties"] = dict(schema["properties"])
        extras = _EXTRA_PROPERTIES.get(name, {})
        schema["properties"].update(extras)
        result.append({
            "name": name,
            "description": description,
            "input_schema": schema,
        })
    return result
