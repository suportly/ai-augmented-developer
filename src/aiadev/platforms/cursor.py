"""Cursor platform handler.

Drops an ``AGENTS.md`` at the project root (so Cursor and Claude Code can
coexist in the same repo without clobbering each other's agent files),
places skills under ``.cursor/skills/<skill-name>/SKILL.md``, and shares
the project-level ``constitution.md`` with Claude Code when both are
installed.
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
    """Skills, commands, agents, and rules install at user scope; see claude_code.py."""
    return role in ("skill", "command", "agent", "rule", "mcp")


def resolve_target(
    role: ArtifactRole,
    name: str,
    install_root: Path,
    *,
    scope: str = "project",
) -> Path:
    """Return the absolute destination path for an artifact under Cursor."""
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
        return install_root / ".cursor" / "skills" / name / "SKILL.md"
    if role == "command":
        if not name:
            raise ValueError("command artifact requires a non-empty name")
        return install_root / ".cursor" / "commands" / "aia" / f"{name}.md"
    if role == "agent":
        if not name:
            raise ValueError("agent artifact requires a non-empty name")
        return install_root / ".cursor" / "agents" / f"{name}.md"
    if role == "rule":
        if not name:
            raise ValueError("rule artifact requires a non-empty name")
        # Cursor native rules use the .mdc extension.
        return install_root / ".cursor" / "rules" / f"{name}.mdc"
    if role == "mcp":
        if not name:
            raise ValueError("mcp artifact requires a non-empty name")
        return install_root / ".cursor" / "mcp.json"
    raise ValueError(f"unknown artifact role: {role!r}")


def iter_preset_artifacts(preset_root: Path) -> Iterator[ArtifactTuple]:
    """Yield ``(role, name, source_path)`` for everything Cursor installs."""
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
    """Convert canonical ``mcps.yaml`` into Cursor's ``.cursor/mcp.json``.

    ``rule`` artifacts get a narrower transform (Story 2 sc4 of
    specs/0016-agent-skills-interop, ADR-6): Cursor's native ``.mdc``
    rule format is conditional on ``globs``, not ``paths:``, so when the
    rule's frontmatter declares ``paths:`` it is translated into
    Cursor's own vocabulary (``globs`` + ``alwaysApply: false``). Rules
    without ``paths:`` pass through byte-identical (opt-in feature; no
    glob evaluation happens here or anywhere in aiadev).
    """
    if role == "mcp":
        servers = load_servers_from_text(source_text, label=f".cursor/mcp.json[{name}]")
        payload = {
            "mcpServers": {
                s.name: _cursor_entry(s) for s in servers
            }
        }
        return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    if role == "rule":
        return _render_rule_frontmatter(source_text)
    return source_text


def _render_rule_frontmatter(source_text: str) -> str:
    """Translate a rule's ``paths:`` key into Cursor's ``.mdc`` vocabulary.

    Cursor's documented ``.mdc`` frontmatter is ``description`` /
    ``globs`` / ``alwaysApply``. Its frontmatter parser is not strict
    YAML, and the convention seen across Cursor's own docs and rules in
    the wild is a comma-separated, unquoted string for ``globs`` (e.g.
    ``globs: *.ts,src/**``) rather than a YAML list — that form is
    chosen here deliberately, over a list, to stay compatible with that
    non-standard parser. Known limitation of that convention: a glob
    that itself contains a comma (e.g. brace expansion ``*.{ts,tsx}``)
    becomes ambiguous in the joined string — same trade-off a
    hand-authored ``.mdc`` faces; prefer comma-free globs in ``paths:``.

    Rules without a ``paths:`` key are returned unchanged (opt-in
    feature — no glob evaluation happens here or anywhere in aiadev,
    this is pure declaration transport per ADR-6).
    """
    frontmatter, body, has_trailing_newline = _split_rule_frontmatter(source_text)
    if frontmatter is None or "paths" not in frontmatter:
        return source_text
    updated = dict(frontmatter)
    paths = updated.pop("paths")
    updated["globs"] = ",".join(str(p) for p in paths)
    updated["alwaysApply"] = False
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


def _cursor_entry(server) -> dict:
    entry: dict = {"command": server.command}
    if server.args:
        entry["args"] = list(server.args)
    if server.env:
        entry["env"] = dict(server.env)
    return entry
