"""T004 / T006 — the optional `token-economy` preset (spec 0022).

The compressor ships as a separate npm package; the preset only declares the
MCP server and carries the Claude Code PreToolUse hook snippet. The catalog
registers it as experimental so it stays out of the stable marketplace
manifest, and the review skill gains an optional, degrading step.
"""
from __future__ import annotations

import json
import pathlib

import yaml
from jsonschema import Draft202012Validator

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
PRESET = REPO_ROOT / "presets" / "token-economy"
MCPS = PRESET / "mcps.yaml"
SNIPPET = PRESET / "hooks" / "claude-code-settings.snippet.json"
README = PRESET / "README.md"
MCPS_SCHEMA = REPO_ROOT / "schemas" / "mcps.schema.json"
CATALOG = REPO_ROOT / "presets" / "catalog.json"
REVIEW_SKILL = REPO_ROOT / "skills" / "requesting-code-review" / "SKILL.md"
TOKEN_DOC = REPO_ROOT / "docs" / "token-economy.md"


def test_preset_declares_smart_bash_server() -> None:
    assert MCPS.exists(), f"expected {MCPS}"
    data = yaml.safe_load(MCPS.read_text(encoding="utf-8"))
    Draft202012Validator(json.loads(MCPS_SCHEMA.read_text(encoding="utf-8"))).validate(data)
    assert "smart-bash" in data["servers"]
    assert data["servers"]["smart-bash"]["command"] == "smart-mcp-proxy"


def test_hook_snippet_is_a_valid_pretooluse_hook_on_bash() -> None:
    data = json.loads(SNIPPET.read_text(encoding="utf-8"))
    pre = data["hooks"]["PreToolUse"]
    assert pre[0]["matcher"] == "Bash"
    hook = pre[0]["hooks"][0]
    assert hook["type"] == "command"
    assert "smart-bash-hook" in hook["command"]


CODEX_SNIPPET = PRESET / "hooks" / "codex-hooks.snippet.json"


def test_codex_hook_snippet_passes_allow_and_matches_bash() -> None:
    """Codex applies updatedInput only with permissionDecision allow (hence --allow)."""
    data = json.loads(CODEX_SNIPPET.read_text(encoding="utf-8"))
    pre = data["hooks"]["PreToolUse"]
    assert pre[0]["matcher"] == "^Bash$"
    assert pre[0]["hooks"][0]["command"] == "smart-bash-hook --allow"
    # The Claude Code snippet must NOT carry --allow: it would skip the permission prompt.
    claude = json.loads(SNIPPET.read_text(encoding="utf-8"))
    assert "--allow" not in claude["hooks"]["PreToolUse"][0]["hooks"][0]["command"]


def test_readme_documents_optin_hook_off_switch_and_privacy() -> None:
    body = README.read_text(encoding="utf-8").lower()
    assert "opt-in" in body
    assert "settings.json" in body and "pretooluse" in body
    assert "turning it off" in body
    assert "privac" in body and "local" in body
    assert "metrics --tokens" in body
    assert "codex" in body and "--allow" in body


def test_catalog_registers_optin_preset() -> None:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    entry = next((p for p in catalog["presets"] if p["name"] == "token-economy"), None)
    assert entry is not None, "catalog must register the token-economy preset"
    assert entry["path"] == "presets/token-economy"
    assert entry["stability"] == "experimental"


def test_review_skill_has_optional_diff_summary_step() -> None:
    body = REVIEW_SKILL.read_text(encoding="utf-8")
    assert "smart_git_diff" in body
    lowered = body.lower()
    assert "optional" in lowered
    assert "degrad" in lowered  # graceful degradation clause


def test_token_economy_doc_cites_the_package_and_keeps_non_goal() -> None:
    body = TOKEN_DOC.read_text(encoding="utf-8")
    assert "smart-mcp-proxy" in body
    assert "smart-bash-hook" in body
    assert "does **not** implement a token" in body  # Non-goal preserved
