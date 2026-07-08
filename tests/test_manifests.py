"""Tests for pure plugin-manifest derivation (T013).

Spec: specs/0016-agent-skills-interop/spec.md, Story 4 (sc2, sc3), ADR-7.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from aiadev.manifests import (
    ManifestDerivationError,
    derive_cursor_plugin,
    derive_marketplace,
    derive_plugin_manifest,
    read_sources,
    render_json,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def pyproject() -> dict:
    return {
        "project": {
            "name": "aiadev",
            "description": "CLI for the AI-Augmented Developer framework.",
            "authors": [{"name": "alairjt", "email": "alairjt@gmail.com"}],
            "license": {"text": "MIT"},
            "keywords": ["ai", "agents", "claude", "spec-driven", "skills"],
            "urls": {
                "Homepage": "https://github.com/suportly/ai-augmented-developer",
                "Issues": "https://github.com/suportly/ai-augmented-developer/issues",
            },
        }
    }


@pytest.fixture
def catalog() -> dict:
    return {
        "version": "1",
        "presets": [
            {
                "name": "lean",
                "path": "presets/lean",
                "summary": "Framework-only preset.",
                "stability": "stable",
            },
            {
                "name": "django-drf-react",
                "path": "presets/django-drf-react",
                "summary": "Django + DRF + React.",
                "stability": "stable",
            },
            {
                "name": "mobile-ops",
                "path": "presets/mobile-ops",
                "summary": "Mobile ops runbooks.",
                "stability": "beta",
            },
        ],
    }


# ---------------------------------------------------------------------------
# (a) plugin.json carries VERSION + pyproject-derived fields
# ---------------------------------------------------------------------------


def test_derive_plugin_manifest_carries_version(pyproject):
    manifest = derive_plugin_manifest("0.21.0", pyproject)
    assert manifest["version"] == "0.21.0"


def test_derive_plugin_manifest_carries_pyproject_fields(pyproject):
    manifest = derive_plugin_manifest("0.21.0", pyproject)
    assert manifest["author"] == {"name": "alairjt", "email": "alairjt@gmail.com"}
    assert manifest["homepage"] == "https://github.com/suportly/ai-augmented-developer"
    assert manifest["repository"] == "https://github.com/suportly/ai-augmented-developer"
    assert manifest["license"] == "MIT"
    assert manifest["keywords"] == ["ai", "agents", "claude", "spec-driven", "skills"]
    assert manifest["description"] == "CLI for the AI-Augmented Developer framework."


def test_derive_plugin_manifest_preserves_existing_shape(pyproject):
    manifest = derive_plugin_manifest("0.21.0", pyproject)
    assert set(manifest.keys()) == {
        "name",
        "description",
        "version",
        "author",
        "homepage",
        "repository",
        "license",
        "keywords",
        "skills",
        "agents",
    }
    assert manifest["skills"] == "./skills/"
    assert manifest["agents"] == "./agents/"


def test_derive_cursor_plugin_is_plugin_manifest_plus_display_name(pyproject):
    plugin = derive_plugin_manifest("0.21.0", pyproject)
    cursor = derive_cursor_plugin("0.21.0", pyproject)
    assert cursor["displayName"] == "AI-Augmented Developer"
    without_display_name = {k: v for k, v in cursor.items() if k != "displayName"}
    assert without_display_name == plugin
    # displayName sits right after name, matching the committed file's order.
    assert list(cursor.keys())[:2] == ["name", "displayName"]


# ---------------------------------------------------------------------------
# Key-set parity with the COMMITTED manifest files: catches future dropped
# or invented keys against the real artifacts, not just generator-vs-generator
# ---------------------------------------------------------------------------


def test_derived_plugin_keys_match_committed_plugin_json():
    committed = json.loads((REPO_ROOT / ".claude-plugin" / "plugin.json").read_text())
    derived = derive_plugin_manifest("0.21.0", _load_real_pyproject())
    assert set(derived.keys()) == set(committed.keys())


def test_derived_cursor_keys_match_committed_cursor_plugin_json():
    committed = json.loads((REPO_ROOT / ".cursor-plugin" / "plugin.json").read_text())
    derived = derive_cursor_plugin("0.21.0", _load_real_pyproject())
    assert set(derived.keys()) == set(committed.keys())


def test_derived_marketplace_keys_match_committed_marketplace_json():
    committed = json.loads(
        (REPO_ROOT / ".claude-plugin" / "marketplace.json").read_text()
    )
    real_catalog = json.loads((REPO_ROOT / "presets" / "catalog.json").read_text())
    derived = derive_marketplace("0.21.0", _load_real_pyproject(), real_catalog)
    assert set(derived.keys()) == set(committed.keys())
    # Core plugin entry (index 0 in both) carries the same key set; preset
    # entries drop `author` deliberately, so only the core row is compared.
    assert set(derived["plugins"][0].keys()) == set(committed["plugins"][0].keys())


# ---------------------------------------------------------------------------
# (b) marketplace: core + exactly the stable presets, source exists on disk
# ---------------------------------------------------------------------------


def test_derive_marketplace_lists_core_and_stable_presets_only(pyproject, catalog):
    marketplace = derive_marketplace("0.21.0", pyproject, catalog)
    names = [p["name"] for p in marketplace["plugins"]]
    assert names == ["ai-augmented-developer", "lean", "django-drf-react"]
    assert "mobile-ops" not in names


def test_derive_marketplace_preset_plugins_have_source_and_version(pyproject, catalog):
    marketplace = derive_marketplace("0.21.0", pyproject, catalog)
    by_name = {p["name"]: p for p in marketplace["plugins"]}
    assert by_name["lean"]["source"] == "./presets/lean"
    assert by_name["lean"]["version"] == "0.21.0"
    assert by_name["django-drf-react"]["source"] == "./presets/django-drf-react"
    assert by_name["django-drf-react"]["version"] == "0.21.0"


def test_derive_marketplace_preset_sources_exist_on_disk_for_real_catalog():
    real_catalog = json.loads((REPO_ROOT / "presets" / "catalog.json").read_text())
    real_pyproject = _load_real_pyproject()
    marketplace = derive_marketplace("0.21.0", real_pyproject, real_catalog)
    for plugin in marketplace["plugins"]:
        if plugin["name"] == "ai-augmented-developer":
            continue
        source_path = REPO_ROOT / plugin["source"]
        assert source_path.is_dir(), f"{plugin['source']} does not exist on disk"


def test_derive_marketplace_omits_beta_and_experimental_by_default(pyproject, catalog):
    marketplace = derive_marketplace("0.21.0", pyproject, catalog)
    names = {p["name"] for p in marketplace["plugins"]}
    assert "mobile-ops" not in names


def test_derive_marketplace_core_plugin_shape(pyproject, catalog):
    marketplace = derive_marketplace("0.21.0", pyproject, catalog)
    core = marketplace["plugins"][0]
    assert set(core.keys()) == {"name", "description", "version", "source", "author"}
    assert core["source"] == "./"
    assert core["author"] == {"name": "alairjt", "email": "alairjt@gmail.com"}


def test_derive_marketplace_top_level_shape(pyproject, catalog):
    marketplace = derive_marketplace("0.21.0", pyproject, catalog)
    assert set(marketplace.keys()) == {"name", "description", "owner", "plugins"}
    assert marketplace["owner"] == {"name": "alairjt", "email": "alairjt@gmail.com"}


# ---------------------------------------------------------------------------
# (c) determinism: derive twice -> identical strings
# ---------------------------------------------------------------------------


def test_derive_plugin_manifest_is_deterministic(pyproject):
    first = render_json(derive_plugin_manifest("0.21.0", pyproject))
    second = render_json(derive_plugin_manifest("0.21.0", pyproject))
    assert first == second


def test_derive_marketplace_is_deterministic(pyproject, catalog):
    first = render_json(derive_marketplace("0.21.0", pyproject, catalog))
    second = render_json(derive_marketplace("0.21.0", pyproject, catalog))
    assert first == second


def test_derive_cursor_plugin_is_deterministic(pyproject):
    first = render_json(derive_cursor_plugin("0.21.0", pyproject))
    second = render_json(derive_cursor_plugin("0.21.0", pyproject))
    assert first == second


# ---------------------------------------------------------------------------
# (d) render_json byte-stability for unchanged inputs (file-level idempotence
# is T015's concern; this only checks the pure rendering step is stable)
# ---------------------------------------------------------------------------


def test_render_json_is_byte_stable_across_calls(pyproject, catalog):
    manifest = derive_plugin_manifest("0.21.0", pyproject)
    marketplace = derive_marketplace("0.21.0", pyproject, catalog)

    assert render_json(manifest) == render_json(derive_plugin_manifest("0.21.0", pyproject))
    assert render_json(marketplace) == render_json(
        derive_marketplace("0.21.0", pyproject, catalog)
    )


def test_render_json_format_matches_existing_manifest_style(pyproject):
    manifest = derive_plugin_manifest("0.21.0", pyproject)
    rendered = render_json(manifest)
    assert rendered.endswith("}\n")
    assert not rendered.endswith("}\n\n")
    # 2-space indent, matching the hand-authored manifests.
    assert '\n  "name"' in rendered


# ---------------------------------------------------------------------------
# (e) a synthetic NEW stable preset yields a new marketplace plugin with
# zero code changes ("zero-toque" claim, cl-4)
# ---------------------------------------------------------------------------


def test_new_stable_preset_in_catalog_yields_new_marketplace_plugin_with_no_code_change(
    pyproject, catalog
):
    catalog_with_new_preset = {
        "version": "1",
        "presets": [
            *catalog["presets"],
            {
                "name": "rails-api",
                "path": "presets/rails-api",
                "summary": "Rails API preset.",
                "stability": "stable",
            },
        ],
    }
    marketplace = derive_marketplace("0.21.0", pyproject, catalog_with_new_preset)
    names = [p["name"] for p in marketplace["plugins"]]
    assert names == ["ai-augmented-developer", "lean", "django-drf-react", "rails-api"]
    by_name = {p["name"]: p for p in marketplace["plugins"]}
    assert by_name["rails-api"]["source"] == "./presets/rails-api"
    assert by_name["rails-api"]["description"] == "Rails API preset."


# ---------------------------------------------------------------------------
# (f) stability values outside the schema enum are rejected with a clear error
# ---------------------------------------------------------------------------


def test_invalid_stability_value_is_rejected_with_clear_error(pyproject, catalog):
    bad_catalog = {
        "version": "1",
        "presets": [
            {
                "name": "broken",
                "path": "presets/broken",
                "summary": "Broken preset.",
                "stability": "not-a-real-stability",
            }
        ],
    }
    with pytest.raises(ManifestDerivationError) as exc_info:
        derive_marketplace("0.21.0", pyproject, bad_catalog)
    message = str(exc_info.value)
    assert "broken" in message
    assert "not-a-real-stability" in message


# ---------------------------------------------------------------------------
# read_sources: loads VERSION / pyproject.toml / presets/catalog.json from disk
# ---------------------------------------------------------------------------


def _load_real_pyproject() -> dict:
    import tomllib

    with (REPO_ROOT / "pyproject.toml").open("rb") as fh:
        return tomllib.load(fh)


def test_read_sources_loads_real_repo_files():
    sources = read_sources(REPO_ROOT)
    assert sources.version == (REPO_ROOT / "VERSION").read_text().strip()
    assert sources.pyproject["project"]["name"] == "aiadev"
    assert isinstance(sources.catalog["presets"], list)
    assert any(p["name"] == "lean" for p in sources.catalog["presets"])


def test_read_sources_output_feeds_derive_functions_without_error():
    sources = read_sources(REPO_ROOT)
    manifest = derive_plugin_manifest(sources.version, sources.pyproject)
    marketplace = derive_marketplace(sources.version, sources.pyproject, sources.catalog)
    cursor = derive_cursor_plugin(sources.version, sources.pyproject)
    assert manifest["version"] == sources.version
    assert marketplace["plugins"][0]["version"] == sources.version
    assert cursor["version"] == sources.version
