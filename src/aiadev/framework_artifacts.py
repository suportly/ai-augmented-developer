"""Scan the framework root for artifacts that install into **every** project.

The install engine walks two sources: this module (framework-generic
commands, agents, and skills that ship with ``aiadev`` itself) and the
per-preset handler in :mod:`aiadev.platforms`. Framework artifacts always
install; preset artifacts of the same ``(role, name)`` take precedence
(presets may tighten, never weaken).

The returned tuples match the per-platform handler shape:
``(role, name, source_path)`` so the engine can reuse the same write
path for both sources.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterator, Literal, Tuple

from .mcp import MCP_ARTIFACT_NAME, MCP_SOURCE_FILENAME

ArtifactRole = Literal["command", "agent", "skill", "rule", "mcp"]
ArtifactTuple = Tuple[ArtifactRole, str, Path]


def _has_name_frontmatter(path: Path) -> bool:
    """Return True if ``path`` starts with a YAML frontmatter block declaring ``name:``.

    Cheap filter that lets us drop README.md and stray docs out of
    ``agents/`` without maintaining an allow-list.
    """
    try:
        with path.open("r", encoding="utf-8") as fh:
            first = fh.readline()
            if first.strip() != "---":
                return False
            for line in fh:
                stripped = line.strip()
                if stripped == "---":
                    return False
                if stripped.startswith("name:"):
                    return True
        return False
    except OSError:
        return False


def iter_framework_artifacts(framework_root: Path) -> Iterator[ArtifactTuple]:
    """Yield ``(role, name, source_path)`` for every framework-generic artifact.

    Scan order is stable (role-wise: command → agent → skill; within each,
    alphabetical by name) so install reports are deterministic.
    """
    rules_dir = framework_root / "rules"
    if rules_dir.is_dir():
        for entry in sorted(rules_dir.iterdir()):
            if entry.is_file() and entry.suffix == ".md":
                yield ("rule", entry.stem, entry)

    commands_dir = framework_root / "commands"
    if commands_dir.is_dir():
        for entry in sorted(commands_dir.iterdir()):
            if entry.is_file() and entry.suffix == ".md":
                yield ("command", entry.stem, entry)

    agents_dir = framework_root / "agents"
    if agents_dir.is_dir():
        for entry in sorted(agents_dir.iterdir()):
            if not entry.is_file() or entry.suffix != ".md":
                continue
            if not _has_name_frontmatter(entry):
                continue
            yield ("agent", entry.stem, entry)

    skills_dir = framework_root / "skills"
    if skills_dir.is_dir():
        for entry in sorted(skills_dir.iterdir()):
            if not entry.is_dir():
                continue
            skill_file = entry / "SKILL.md"
            if skill_file.is_file():
                yield ("skill", entry.name, skill_file)

    mcps_file = framework_root / MCP_SOURCE_FILENAME
    if mcps_file.is_file():
        yield ("mcp", MCP_ARTIFACT_NAME, mcps_file)
