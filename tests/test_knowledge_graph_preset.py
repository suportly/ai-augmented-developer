"""T008/T009 — the optional `knowledge-graph` preset (spec 0017, cl-5).

The graph provider ships as an opt-in preset the consumer enables on demand;
no existing preset gains a dependency. The preset declares the provider MCP
in its own mcps.yaml, and the catalog registers it as experimental (so it
never leaks into the stable marketplace manifest).
"""
from __future__ import annotations

import json
import pathlib

import yaml
from jsonschema import Draft202012Validator

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
PRESET = REPO_ROOT / "presets" / "knowledge-graph"
MCPS = PRESET / "mcps.yaml"
README = PRESET / "README.md"
MCPS_SCHEMA = REPO_ROOT / "schemas" / "mcps.schema.json"
CATALOG = REPO_ROOT / "presets" / "catalog.json"


def test_preset_declares_graph_provider() -> None:
    assert MCPS.exists(), f"expected {MCPS}"
    data = yaml.safe_load(MCPS.read_text(encoding="utf-8"))
    Draft202012Validator(
        json.loads(MCPS_SCHEMA.read_text(encoding="utf-8"))
    ).validate(data)
    servers = data["servers"]
    assert servers, "the preset must declare at least one MCP server"
    # graphify is the reference implementation behind the contract
    assert any("graph" in name for name in servers), (
        "expected a graph provider server (graphify reference impl)"
    )


def test_readme_documents_optin_and_privacy() -> None:
    assert README.exists(), f"expected {README}"
    body = README.read_text(encoding="utf-8").lower()
    assert "opt-in" in body or "opt in" in body or "sob demanda" in body
    assert "privac" in body  # privacy / privacidade
    assert "local" in body  # code stays local by default


def test_catalog_registers_optin_preset() -> None:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    entry = next(
        (p for p in catalog["presets"] if p["name"] == "knowledge-graph"), None
    )
    assert entry is not None, "catalog must register the knowledge-graph preset"
    assert entry["path"] == "presets/knowledge-graph"
    assert entry["stability"] == "experimental", (
        "opt-in graph preset must be experimental so it stays out of the "
        "stable marketplace manifest"
    )
