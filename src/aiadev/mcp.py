"""Canonical MCP declaration loader.

``mcps.yaml`` is the single source of truth for every MCP server the
install engine ships into a consumer project. Each platform handler
reads the parsed dict via :func:`load_servers` and renders it into the
platform's native format (JSON for Claude Code / Cursor / Gemini /
OpenCode, TOML for Codex).

The canonical shape:

    servers:
      <name>:
        command: "<exe>"
        args: [...]
        env:
          KEY: "value"

Empty and missing files are both legal — they yield an empty ``servers``
dict so platforms can skip writing a config when nothing is declared.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping

import yaml

MCP_SOURCE_FILENAME = "mcps.yaml"
# Name used for the single ``mcp`` artifact in the install manifest.
# Keeping it non-empty satisfies existing name validation across handlers.
MCP_ARTIFACT_NAME = "servers"


@dataclass(frozen=True)
class Server:
    """One MCP server entry in its canonical form."""

    name: str
    command: str
    args: tuple[str, ...] = field(default_factory=tuple)
    env: Mapping[str, str] = field(default_factory=dict)


def load_servers(source_path: Path) -> list[Server]:
    """Parse ``mcps.yaml`` at ``source_path`` into a list of :class:`Server`.

    Missing file → empty list. Empty ``servers:`` map → empty list.
    Raises ``ValueError`` on malformed entries so the install engine
    surfaces the problem instead of silently dropping servers.
    """
    if not source_path.is_file():
        return []
    data = yaml.safe_load(source_path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{source_path}: top-level YAML must be a mapping")
    raw = data.get("servers") or {}
    if not isinstance(raw, dict):
        raise ValueError(f"{source_path}: 'servers' must be a mapping")
    servers: list[Server] = []
    for name in sorted(raw):
        entry = raw[name]
        if not isinstance(entry, dict):
            raise ValueError(f"{source_path}: server '{name}' must be a mapping")
        command = entry.get("command")
        if not isinstance(command, str) or not command:
            raise ValueError(f"{source_path}: server '{name}' requires a non-empty 'command'")
        args_raw = entry.get("args", []) or []
        if not isinstance(args_raw, list) or not all(isinstance(a, str) for a in args_raw):
            raise ValueError(f"{source_path}: server '{name}' args must be a list of strings")
        env_raw = entry.get("env", {}) or {}
        if not isinstance(env_raw, dict) or not all(
            isinstance(k, str) and isinstance(v, str) for k, v in env_raw.items()
        ):
            raise ValueError(f"{source_path}: server '{name}' env must be a map of string→string")
        servers.append(
            Server(
                name=name,
                command=command,
                args=tuple(args_raw),
                env=dict(env_raw),
            )
        )
    return servers


def load_servers_from_text(text: str, *, label: str = "<memory>") -> list[Server]:
    """Same as :func:`load_servers` but takes raw YAML text.

    Used by platform ``render_target`` hooks, which receive the rendered
    file content (not the source path) from the install engine.
    """
    data = yaml.safe_load(text) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{label}: top-level YAML must be a mapping")
    raw = data.get("servers") or {}
    if not isinstance(raw, dict):
        raise ValueError(f"{label}: 'servers' must be a mapping")
    servers: list[Server] = []
    for name in sorted(raw):
        entry = raw[name]
        if not isinstance(entry, dict):
            raise ValueError(f"{label}: server '{name}' must be a mapping")
        command = entry.get("command")
        if not isinstance(command, str) or not command:
            raise ValueError(f"{label}: server '{name}' requires a non-empty 'command'")
        args_raw = entry.get("args", []) or []
        if not isinstance(args_raw, list) or not all(isinstance(a, str) for a in args_raw):
            raise ValueError(f"{label}: server '{name}' args must be a list of strings")
        env_raw = entry.get("env", {}) or {}
        if not isinstance(env_raw, dict) or not all(
            isinstance(k, str) and isinstance(v, str) for k, v in env_raw.items()
        ):
            raise ValueError(f"{label}: server '{name}' env must be a map of string→string")
        servers.append(
            Server(
                name=name,
                command=command,
                args=tuple(args_raw),
                env=dict(env_raw),
            )
        )
    return servers
