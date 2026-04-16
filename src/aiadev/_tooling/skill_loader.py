"""Load SKILL.md content with associated template and constitution excerpt."""
from __future__ import annotations

import functools
import pathlib
from typing import Any

from . import SpecNotFoundError

PIPELINE_SKILLS = frozenset({
    "specify", "clarify", "plan", "tasks",
    "implement", "analyze", "checklist", "constitution",
})

SKILL_TEMPLATE_MAP: dict[str, str] = {
    "specify": "templates/spec-template.md",
    "clarify": "templates/spec-template.md",
    "plan": "templates/plan-template.md",
    "tasks": "templates/tasks-template.md",
    "implement": "templates/tasks-template.md",
    "analyze": "templates/plan-template.md",
    "checklist": "templates/plan-template.md",
    "constitution": "templates/constitution-template.md",
}


@functools.lru_cache(maxsize=16)
def _read_cached(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


def load_skill(
    name: str,
    framework_root: pathlib.Path,
    *,
    spec_path: pathlib.Path | None = None,
) -> dict[str, Any]:
    """Load a pipeline skill's SKILL.md, its template, and a constitution excerpt.

    Returns a dict with keys ``prompt``, ``template``, ``constitution_excerpt``.

    Raises :class:`KeyError` for unknown skill names.
    Raises :class:`SpecNotFoundError` when *spec_path* is required but missing.
    """
    skill_dir = framework_root / "skills" / name
    skill_file = skill_dir / "SKILL.md"
    if not skill_file.is_file():
        raise KeyError(f"Unknown skill: {name}")

    prompt = _read_cached(skill_file)

    template_rel = SKILL_TEMPLATE_MAP.get(name, "templates/spec-template.md")
    template_path = framework_root / template_rel
    template_content = _read_cached(template_path) if template_path.is_file() else ""

    constitution_path = framework_root / "constitution.md"
    constitution_text = _read_cached(constitution_path) if constitution_path.is_file() else ""
    constitution_excerpt = _extract_relevant_articles(constitution_text)

    if spec_path is not None and not pathlib.Path(spec_path).is_file():
        raise SpecNotFoundError(f"Spec not found: {spec_path}")

    return {
        "prompt": prompt,
        "template": {
            "path": template_rel,
            "content": template_content,
        },
        "constitution_excerpt": constitution_excerpt,
    }


def _extract_relevant_articles(constitution_text: str) -> str:
    """Return a relevant excerpt of the constitution (all articles)."""
    return constitution_text
