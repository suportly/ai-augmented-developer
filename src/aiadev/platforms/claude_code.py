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
    """Return whether an artifact role makes sense under ``--scope user``.

    Agent files and constitutions carry project-specific variables and
    cannot migrate to a user-level install. Skills, commands, agents,
    and rules are shareable and install into the user's home under the
    same layout.
    """
    return role in ("skill", "command", "agent", "rule", "mcp")


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
    if role == "command":
        if not name:
            raise ValueError("command artifact requires a non-empty name")
        return install_root / ".claude" / "commands" / "aia" / f"{name}.md"
    if role == "agent":
        if not name:
            raise ValueError("agent artifact requires a non-empty name")
        return install_root / ".claude" / "agents" / f"{name}.md"
    if role == "rule":
        if not name:
            raise ValueError("rule artifact requires a non-empty name")
        return install_root / ".claude" / "rules" / f"{name}.md"
    if role == "mcp":
        if not name:
            raise ValueError("mcp artifact requires a non-empty name")
        # Claude Code reads ``.mcp.json`` at the project root (or under
        # $HOME for user scope). The ``name`` is ignored because there is
        # a single MCP config file; it only matters to the manifest.
        return install_root / ".mcp.json"
    raise ValueError(f"unknown artifact role: {role!r}")


def iter_preset_artifacts(preset_root: Path) -> Iterator[ArtifactTuple]:
    """Yield ``(role, name, source_path)`` for everything to install.

    The scan is deterministic: root-level artifacts first (in role
    order agent_file → constitution), then commands, agents, and
    finally skills — each sorted alphabetically. Keeps install reports
    stable between runs and matches the engine's role priority.
    """
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
    """Convert canonical ``mcps.yaml`` into Claude Code's ``.mcp.json``.

    ``rule`` artifacts get a narrower transform (Story 2 sc1 of
    specs/0016-agent-skills-interop, ADR-6): when the rule's frontmatter
    declares ``paths:``, Claude Code supports conditional rules natively,
    so the key is kept intact — but ``alwaysApply: true`` is dropped
    because a paths-scoped rule is conditional, not universal, on this
    platform. Rules without ``paths:`` pass through byte-identical
    (opt-in feature).

    Other roles pass through unchanged — the engine feeds the rendered
    text straight to disk.
    """
    if role == "mcp":
        servers = load_servers_from_text(source_text, label=f".mcp.json[{name}]")
        payload = {
            "mcpServers": {
                s.name: _claude_entry(s) for s in servers
            }
        }
        return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    if role == "rule":
        return _render_rule_frontmatter(source_text, drop_always_apply_if_scoped=True)
    return source_text


def _render_rule_frontmatter(source_text: str, *, drop_always_apply_if_scoped: bool) -> str:
    """Rewrite a rule's frontmatter when it declares ``paths:``.

    Rules without a ``paths:`` key are returned unchanged (opt-in
    feature — no glob evaluation happens here or anywhere in aiadev,
    this is pure declaration transport per ADR-6).
    """
    frontmatter, body, has_trailing_newline = _split_rule_frontmatter(source_text)
    if frontmatter is None or "paths" not in frontmatter:
        return source_text
    updated = dict(frontmatter)
    if drop_always_apply_if_scoped:
        updated.pop("alwaysApply", None)
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


def _claude_entry(server) -> dict:
    entry: dict = {"command": server.command}
    if server.args:
        entry["args"] = list(server.args)
    if server.env:
        entry["env"] = dict(server.env)
    return entry
