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


def user_scope_supported(role: ArtifactRole) -> bool:
    """Return whether an artifact role makes sense under ``--scope user``.

    Agent files and constitutions carry project-specific variables and
    cannot migrate to a user-level install. Skills are the only
    shareable role; everything else is skipped with a note when the
    user requests ``--scope user``.
    """
    return role == "skill"


def resolve_target(
    role: ArtifactRole,
    name: str,
    install_root: Path,
    *,
    scope: str = "project",
) -> Path:
    """Return the absolute destination path for an artifact.

    ``install_root`` is the project directory under ``--scope project``
    (the default) or ``Path.home()`` under ``--scope user``. The caller
    (engine) is responsible for computing it from the scope; the
    handler only applies the per-platform layout beneath it.
    """
    if scope == "user" and not user_scope_supported(role):
        raise ValueError(
            f"role {role!r} is not installable at user scope; engine should filter first"
        )
    if role == "agent_file":
        return install_root / "CLAUDE.md"
    if role == "constitution":
        return install_root / "constitution.md"
    if role == "skill":
        if not name:
            raise ValueError("skill artifact requires a non-empty name")
        return install_root / ".claude" / "skills" / name / "SKILL.md"
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
