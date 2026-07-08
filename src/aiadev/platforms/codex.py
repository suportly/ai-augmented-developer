"""Codex platform handler.

Writes ``AGENTS.md`` at the project root (shared with Cursor and OpenCode
— all three IDEs follow the same agent-file convention) and places
skills under ``.codex/skills/<skill-name>/SKILL.md``. ``constitution.md``
at the root is shared across every platform.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterator, Literal, Tuple

import yaml

from ..mcp import MCP_ARTIFACT_NAME, MCP_SOURCE_FILENAME, load_servers_from_text

ArtifactRole = Literal[
    "agent_file", "constitution", "skill", "command", "agent", "rule", "mcp"
]
ArtifactTuple = Tuple[ArtifactRole, str, Path]


def user_scope_supported(role: ArtifactRole) -> bool:
    return role in ("skill", "command", "agent", "rule", "mcp")


def resolve_target(
    role: ArtifactRole,
    name: str,
    install_root: Path,
    *,
    scope: str = "project",
) -> Path:
    if scope == "user" and not user_scope_supported(role):
        raise ValueError(
            f"role {role!r} is not installable at user scope; engine should filter first"
        )
    if role == "agent_file":
        return install_root / "AGENTS.md"
    if role == "constitution":
        return install_root / "constitution.md"
    if role == "skill":
        if not name:
            raise ValueError("skill artifact requires a non-empty name")
        return install_root / ".codex" / "skills" / name / "SKILL.md"
    if role == "command":
        if not name:
            raise ValueError("command artifact requires a non-empty name")
        return install_root / ".codex" / "commands" / "aia" / f"{name}.md"
    if role == "agent":
        if not name:
            raise ValueError("agent artifact requires a non-empty name")
        return install_root / ".codex" / "agents" / f"{name}.md"
    if role == "rule":
        if not name:
            raise ValueError("rule artifact requires a non-empty name")
        return install_root / ".codex" / "rules" / f"{name}.md"
    if role == "mcp":
        if not name:
            raise ValueError("mcp artifact requires a non-empty name")
        # Codex CLI reads MCP config from ``~/.codex/config.toml``; the
        # project-scope install writes ``.codex/config.toml`` so teams
        # can version the declaration. Users can symlink or merge the
        # table manually until Codex supports project-scope MCPs.
        return install_root / ".codex" / "config.toml"
    raise ValueError(f"unknown artifact role: {role!r}")


def iter_preset_artifacts(preset_root: Path) -> Iterator[ArtifactTuple]:
    agent = preset_root / "CLAUDE.md"
    if agent.is_file():
        yield ("agent_file", "", agent)

    constitution = preset_root / "constitution.md"
    if constitution.is_file():
        yield ("constitution", "", constitution)

    rules_dir = preset_root / "rules"
    if rules_dir.is_dir():
        for entry in sorted(rules_dir.iterdir()):
            if entry.is_file() and entry.suffix == ".md":
                yield ("rule", entry.stem, entry)

    commands_dir = preset_root / "commands"
    if commands_dir.is_dir():
        for entry in sorted(commands_dir.iterdir()):
            if entry.is_file() and entry.suffix == ".md":
                yield ("command", entry.stem, entry)

    agents_dir = preset_root / "agents"
    if agents_dir.is_dir():
        for entry in sorted(agents_dir.iterdir()):
            if entry.is_file() and entry.suffix == ".md":
                yield ("agent", entry.stem, entry)

    skills_dir = preset_root / "skills"
    if skills_dir.is_dir():
        for entry in sorted(skills_dir.iterdir()):
            if not entry.is_dir():
                continue
            skill_file = entry / "SKILL.md"
            if skill_file.is_file():
                yield ("skill", entry.name, skill_file)

    mcps_file = preset_root / MCP_SOURCE_FILENAME
    if mcps_file.is_file():
        yield ("mcp", MCP_ARTIFACT_NAME, mcps_file)


def render_target(role: ArtifactRole, name: str, source_text: str) -> str:
    """Convert canonical ``mcps.yaml`` into Codex's ``.codex/config.toml``.

    ``rule`` artifacts get a narrower transform (Story 2 sc2 of
    specs/0016-agent-skills-interop, ADR-6): Codex's runtime does not
    support conditional/paths-scoped rules, so the ``paths:`` key is
    stripped from the installed frontmatter. Rules without ``paths:``
    pass through byte-identical (opt-in feature; no glob evaluation
    happens here or anywhere in aiadev).
    """
    if role == "mcp":
        servers = load_servers_from_text(source_text, label=f".codex/config.toml[{name}]")
        return _servers_to_toml(servers)
    if role == "rule":
        return _strip_rule_paths(source_text)
    return source_text


def _strip_rule_paths(source_text: str) -> str:
    """Remove the ``paths:`` key from a rule's frontmatter, if present."""
    frontmatter, body, has_trailing_newline = _split_rule_frontmatter(source_text)
    if frontmatter is None or "paths" not in frontmatter:
        return source_text
    updated = {k: v for k, v in frontmatter.items() if k != "paths"}
    return _join_rule_frontmatter(updated, body, has_trailing_newline)


def _split_rule_frontmatter(text: str) -> tuple[dict | None, str, bool]:
    """Split ``text`` into (frontmatter, body, had_trailing_newline).

    Returns ``(None, text, False)`` when there is no well-formed YAML
    frontmatter block, so callers can fall back to a pass-through.
    """
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return None, text, False
    end_idx: int | None = None
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            end_idx = idx
            break
    if end_idx is None:
        return None, text, False
    fm_text = "".join(lines[1:end_idx])
    try:
        parsed = yaml.safe_load(fm_text) or {}
    except yaml.YAMLError:
        return None, text, False
    if not isinstance(parsed, dict):
        return None, text, False
    body = "".join(lines[end_idx + 1 :])
    return parsed, body, text.endswith("\n")


def _join_rule_frontmatter(frontmatter: dict, body: str, has_trailing_newline: bool) -> str:
    dumped = yaml.safe_dump(frontmatter, sort_keys=False, default_flow_style=False)
    rendered = f"---\n{dumped}---\n{body}"
    if has_trailing_newline and not rendered.endswith("\n"):
        rendered += "\n"
    return rendered


def _servers_to_toml(servers) -> str:
    """Render the ``[mcp_servers.<name>]`` tables Codex expects.

    We emit TOML by hand to keep the dependency footprint minimal and to
    avoid surprises with tomllib's dict-roundtrip (Python 3.11+ ships a
    reader only; writers are third-party). The format is deliberately
    narrow: one table per server with ``command``, ``args``, and ``env``
    sub-table when present.
    """
    if not servers:
        # Empty servers map → still emit the section header so users
        # know where to add entries by hand if they choose.
        return "# Managed by aiadev. Add MCP servers to mcps.yaml and re-run `aiadev install`.\n"
    parts: list[str] = []
    for server in servers:
        parts.append(f"[mcp_servers.{_toml_key(server.name)}]")
        parts.append(f"command = {_toml_str(server.command)}")
        if server.args:
            rendered_args = ", ".join(_toml_str(a) for a in server.args)
            parts.append(f"args = [{rendered_args}]")
        if server.env:
            env_items = ", ".join(
                f"{_toml_key(k)} = {_toml_str(v)}" for k, v in server.env.items()
            )
            parts.append("env = { " + env_items + " }")
        parts.append("")
    return "\n".join(parts) + "\n"


def _toml_str(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _toml_key(value: str) -> str:
    # Bare keys only contain ASCII letters, digits, _, -. Quote otherwise.
    if value and all(c.isalnum() or c in "_-" for c in value):
        return value
    return _toml_str(value)
