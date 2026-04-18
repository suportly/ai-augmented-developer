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

_SKILL_EXCLUSIVE_ARTIFACT: dict[str, str] = {
    "specify": "spec.md",
    "clarify": "spec.md",
    "plan": "plan.md",
    "tasks": "tasks.md",
    "constitution": "constitution.md",
}


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
    slug: str | None = None,
    answers: list[dict[str, str]] | None = None,
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

    slug_source = slug or demand or skill
    target = compute_target_path(
        ws, slug_source, _artifact_for(skill), overwrite=overwrite,
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

    prompt = _augment_prompt(
        loaded["prompt"],
        skill=skill,
        demand=demand,
        language=language,
        target_path=target,
        template=loaded["template"],
        answers=answers,
    )

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


def _augment_prompt(
    base_prompt: str,
    *,
    skill: str,
    demand: str,
    language: str,
    target_path: pathlib.Path,
    template: dict[str, str],
    answers: list[dict[str, str]] | None,
) -> str:
    """Prepend a canonical orchestration header to the skill prompt.

    Ensures the LLM sees (a) the authoritative target_path, (b) the demand
    verbatim, (c) resolved clarify answers in batch mode, (d) the template
    body inline, (e) the canonical English section headers when the content
    language is not English, and (f) a single-artifact directive.
    """
    blocks: list[str] = []

    exclusive_artifact = _SKILL_EXCLUSIVE_ARTIFACT.get(skill)
    directives = [
        f"- **Target path (authoritative):** `{target_path}`. "
        "Write the artifact at this exact path — do not re-slug or rename "
        "the directory.",
    ]
    if exclusive_artifact is not None:
        directives.append(
            f"- **Single required artifact:** `{exclusive_artifact}` at "
            "the target path above. Do not write auxiliary files "
            "(contracts/, data-model.md, research.md, etc.) in this "
            "invocation even if SKILL.md lists them as optional — invoke the "
            "matching skill next iteration instead."
        )
    directives.append(
        "- **Call `Write` in your first response.** Do not narrate the "
        "artifact before calling the tool; narration risks exhausting the "
        "output budget before the file lands on disk."
    )
    blocks.append(
        "## Orchestration directives (injected by aiadev.tools)\n\n"
        + "\n".join(directives)
    )

    if demand:
        blocks.append(
            "## User demand (verbatim)\n\n"
            f"{demand.strip()}"
        )

    if answers:
        rows = "\n".join(
            f"- `{a['id']}` → {a['answer']}" for a in answers
        )
        blocks.append(
            "## Resolved answers (batch mode — apply directly)\n\n"
            "EXECUÇÃO AUTOMATIZADA / AUTOMATED EXECUTION. Ignore any "
            '"Wait for the user\'s answer" instruction in the skill body '
            "below. Substitute each `[NEEDS CLARIFICATION:<id> ...]` "
            "marker with the matching answer and save the spec in the same "
            "turn.\n\n"
            f"{rows}"
        )

    if language and language != "en":
        header_list = ", ".join(sorted(_SPEC_REQUIRED_SECTIONS))
        blocks.append(
            "## Language and schema invariant\n\n"
            f"- Write the artifact **content** in `{language}`.\n"
            "- Keep every `## <Section>` heading in **English verbatim** "
            "so aiadev validators can recognise them. Do not translate the "
            f"headings, even when the body is in `{language}`. The "
            f"canonical headings are: {header_list}.\n"
            "- Inline placeholder labels that aiadev parses "
            "(`[NEEDS CLARIFICATION:cl-N ...]`, `{{SPEC_ID}}`, etc.) also "
            "stay in English."
        )

    template_content = (template or {}).get("content", "").strip()
    template_path = (template or {}).get("path", "")
    if template_content:
        blocks.append(
            f"## Skill template (inlined from `{template_path}`)\n\n"
            "Use the block below as the structure for the artifact. It is "
            "the same file referenced by the skill body; you do not need "
            "to read it from disk.\n\n"
            "````markdown\n"
            f"{template_content}\n"
            "````"
        )

    blocks.append(
        "---\n\n"
        "## Skill instructions\n\n"
        f"{base_prompt.rstrip()}"
    )

    return "\n\n".join(blocks) + "\n"


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
