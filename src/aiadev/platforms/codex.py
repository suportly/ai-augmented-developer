"""Codex platform handler.

Writes ``AGENTS.md`` at the project root (shared with Cursor and OpenCode
— all three IDEs follow the same agent-file convention) and places
skills under ``.codex/skills/<skill-name>/SKILL.md``. ``constitution.md``
at the root is shared across every platform.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterator, Literal, Tuple

ArtifactRole = Literal["agent_file", "constitution", "skill"]
ArtifactTuple = Tuple[ArtifactRole, str, Path]


def resolve_target(role: ArtifactRole, name: str, project_root: Path) -> Path:
    if role == "agent_file":
        return project_root / "AGENTS.md"
    if role == "constitution":
        return project_root / "constitution.md"
    if role == "skill":
        if not name:
            raise ValueError("skill artifact requires a non-empty name")
        return project_root / ".codex" / "skills" / name / "SKILL.md"
    raise ValueError(f"unknown artifact role: {role!r}")


def iter_preset_artifacts(preset_root: Path) -> Iterator[ArtifactTuple]:
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
