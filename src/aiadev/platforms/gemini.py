"""Gemini CLI platform handler.

Writes ``GEMINI.md`` at the project root (Gemini-specific convention;
does not collide with Cursor/Codex/OpenCode's ``AGENTS.md``) and places
skills under ``.gemini/skills/<skill-name>/SKILL.md``. ``constitution.md``
at the root is shared across every platform.

Commands are special-cased: Gemini CLI reads custom commands from
``.gemini/commands/aia/<name>.toml`` (not markdown; the ``aia/``
subdirectory namespaces them as ``/aia:<name>``), so the handler provides
a :func:`render_target` hook that converts the framework's markdown
source into TOML before the engine writes it. Markdown agents and
skills are passed through unchanged.
"""
from __future__ import annotations

import json
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
        return install_root / "GEMINI.md"
    if role == "constitution":
        return install_root / "constitution.md"
    if role == "skill":
        if not name:
            raise ValueError("skill artifact requires a non-empty name")
        return install_root / ".gemini" / "skills" / name / "SKILL.md"
    if role == "command":
        if not name:
            raise ValueError("command artifact requires a non-empty name")
        return install_root / ".gemini" / "commands" / "aia" / f"{name}.toml"
    if role == "agent":
        if not name:
            raise ValueError("agent artifact requires a non-empty name")
        return install_root / ".gemini" / "agents" / f"{name}.md"
    if role == "rule":
        if not name:
            raise ValueError("rule artifact requires a non-empty name")
        return install_root / ".gemini" / "rules" / f"{name}.md"
    if role == "mcp":
        if not name:
            raise ValueError("mcp artifact requires a non-empty name")
        # Gemini CLI reads MCP servers from ``.gemini/settings.json``
        # under the ``mcpServers`` key, alongside other runtime settings.
        # aiadev owns this file on install; users who already have
        # hand-written settings should copy them into mcps.yaml or
        # accept the install conflict and merge manually.
        return install_root / ".gemini" / "settings.json"
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
    """Hook called by the engine after variable substitution.

    ``command`` → TOML (Gemini CLI consumes TOML, not markdown).
    ``mcp``     → JSON with the ``mcpServers`` key (Gemini's
                  ``.gemini/settings.json`` shape).
    Other roles pass through unchanged.
    """
    if role == "command":
        return _md_command_to_toml(source_text)
    if role == "mcp":
        servers = load_servers_from_text(source_text, label=f".gemini/settings.json[{name}]")
        payload = {
            "mcpServers": {s.name: _gemini_mcp_entry(s) for s in servers}
        }
        return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    if role == "rule":
        return _strip_rule_paths(source_text)
    return source_text


def _strip_rule_paths(source_text: str) -> str:
    """Remove the ``paths:`` key from a rule's frontmatter, if present.

    Story 2 sc2 of specs/0016-agent-skills-interop (ADR-6): Gemini CLI's
    runtime does not support conditional/paths-scoped rules, so the
    ``paths:`` key is stripped from the installed frontmatter. Rules
    without ``paths:`` pass through byte-identical (opt-in feature; no
    glob evaluation happens here or anywhere in aiadev).
    """
    frontmatter, body, has_trailing_newline = _split_rule_frontmatter(source_text)
    if frontmatter is None or "paths" not in frontmatter:
        return source_text
    updated = {k: v for k, v in frontmatter.items() if k != "paths"}
    return _join_rule_frontmatter(updated, body, has_trailing_newline)


def _split_rule_frontmatter(text: str) -> tuple[dict | None, str, bool]:
    """Split ``text`` into (frontmatter, body, had_trailing_newline).

    Returns ``(None, text, False)`` when there is no well-formed YAML
    frontmatter block, so callers can fall back to a pass-through.
    Distinct from :func:`_split_frontmatter` (used by the command->TOML
    transform) because that helper silently returns ``{}`` on a missing
    block, which would be indistinguishable from an empty-but-present
    frontmatter here.
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


def _gemini_mcp_entry(server) -> dict:
    entry: dict = {"command": server.command}
    if server.args:
        entry["args"] = list(server.args)
    if server.env:
        entry["env"] = dict(server.env)
    return entry


def _md_command_to_toml(source_text: str) -> str:
    """Convert a markdown command with YAML frontmatter to Gemini TOML.

    Input format (framework convention):

        ---
        description: Short one-liner.
        allowed-tools: Read, Write
        argument-hint: "<demand>"
        ---
        Prompt body referring to $ARGUMENTS.

    Output format (Gemini CLI convention):

        description = "Short one-liner."
        prompt = \"\"\"Prompt body referring to {{args}}.\"\"\"

    Frontmatter keys not meaningful to Gemini are dropped. ``$ARGUMENTS``
    is rewritten to Gemini's ``{{args}}`` placeholder.
    """
    frontmatter, body = _split_frontmatter(source_text)
    description = str(frontmatter.get("description", "")).strip()
    prompt = body.strip().replace("$ARGUMENTS", "{{args}}")
    lines: list[str] = []
    if description:
        lines.append(f"description = {_toml_str(description)}")
    lines.append(f"prompt = {_toml_triple(prompt)}")
    return "\n".join(lines) + "\n"


def _split_frontmatter(text: str) -> tuple[dict, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text
    collected: list[str] = []
    end_idx: int | None = None
    for idx, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_idx = idx
            break
        collected.append(line)
    if end_idx is None:
        return {}, text
    try:
        parsed = yaml.safe_load("\n".join(collected)) or {}
    except yaml.YAMLError:
        return {}, text
    if not isinstance(parsed, dict):
        return {}, text
    body = "\n".join(lines[end_idx + 1 :])
    return parsed, body


def _toml_str(value: str) -> str:
    """Quote ``value`` as a TOML basic string."""
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _toml_triple(value: str) -> str:
    """Quote ``value`` as a TOML multi-line basic string."""
    # Neutralise any sequence of three double quotes.
    safe = value.replace('"""', '""\\"')
    return f'"""\n{safe}\n"""'
