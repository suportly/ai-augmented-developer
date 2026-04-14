"""Cursor platform handler.

Drops an ``AGENTS.md`` at the project root (so Cursor and Claude Code can
coexist in the same repo without clobbering each other's agent files),
places skills under ``.cursor/skills/<skill-name>/SKILL.md``, and shares
the project-level ``constitution.md`` with Claude Code when both are
installed.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterator, Literal, Tuple

ArtifactRole = Literal["agent_file", "constitution", "skill"]
ArtifactTuple = Tuple[ArtifactRole, str, Path]


def resolve_target(role: ArtifactRole, name: str, project_root: Path) -> Path:
    """Return the absolute destination path for an artifact under Cursor."""
    if role == "agent_file":
        return project_root / "AGENTS.md"
    if role == "constitution":
        return project_root / "constitution.md"
    if role == "skill":
        if not name:
            raise ValueError("skill artifact requires a non-empty name")
        return project_root / ".cursor" / "skills" / name / "SKILL.md"
    raise ValueError(f"unknown artifact role: {role!r}")


def iter_preset_artifacts(preset_root: Path) -> Iterator[ArtifactTuple]:
    """Yield ``(role, name, source_path)`` for everything Cursor installs.

    Identical traversal to :mod:`aiadev.platforms.claude_code`, kept local
    so Cursor can evolve its own policy without touching the Claude Code
    handler.
    """
    agent = preset_root / "CLAUDE.md"
    if agent.is_file():
        yield ("agent_file", "", agent)

    constitution = preset_root / "constitution.md"
    if constitution.is_file():
        yield ("constitution", "", constitution)

    skills_dir = preset_root / "skills"
    if skills_dir.is_dir():
        for entry in sorted(skills_dir.iterdir()):
            if not entry.is_dir():
                continue
            skill_file = entry / "SKILL.md"
            if skill_file.is_file():
                yield ("skill", entry.name, skill_file)
