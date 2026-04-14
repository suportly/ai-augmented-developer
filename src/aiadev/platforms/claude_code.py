"""Claude Code platform handler.

Claude Code discovers skills by walking ``.claude/skills/<name>/SKILL.md``
in the current working directory, so the consumer layout is:

* ``CLAUDE.md`` at the project root — the agent file.
* ``constitution.md`` at the project root — the project-level
  constitution, extended by preset articles when the active preset
  ships one.
* ``.claude/skills/<skill-name>/SKILL.md`` — one directory per skill,
  the contents copied verbatim from the preset after placeholder
  substitution.

Plugin manifest (``.claude-plugin/plugin.json``) management is out of
scope in v0.3. If the consumer wants to publish the project as a
plugin themselves, they author that file; the installer does not
touch it.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterator, Literal, Tuple

ArtifactRole = Literal["agent_file", "constitution", "skill"]
ArtifactTuple = Tuple[ArtifactRole, str, Path]


def resolve_target(role: ArtifactRole, name: str, project_root: Path) -> Path:
    """Return the absolute destination path for an artifact.

    ``name`` is only used for ``skill`` artifacts (it becomes the
    directory name under ``.claude/skills/``). For ``agent_file`` and
    ``constitution`` it is ignored and may be an empty string.
    """
    if role == "agent_file":
        return project_root / "CLAUDE.md"
    if role == "constitution":
        return project_root / "constitution.md"
    if role == "skill":
        if not name:
            raise ValueError("skill artifact requires a non-empty name")
        return project_root / ".claude" / "skills" / name / "SKILL.md"
    raise ValueError(f"unknown artifact role: {role!r}")


def iter_preset_artifacts(preset_root: Path) -> Iterator[ArtifactTuple]:
    """Yield ``(role, name, source_path)`` for everything to install.

    The scan is deterministic: root-level artifacts first (in role
    order agent_file → constitution), then skills sorted by directory
    name. This keeps install reports stable between runs.
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
