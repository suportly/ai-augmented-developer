"""T015 — the three committed plugin manifests must stay in sync with the
derivation, and CI must gate on it.

Spec: specs/0016-agent-skills-interop/spec.md, Story 4 (sc1, sc3, sc4).

``src/aiadev/manifests.py`` (T013) derives ``.claude-plugin/plugin.json``,
``.claude-plugin/marketplace.json``, and ``.cursor-plugin/plugin.json``
from ``VERSION`` + ``pyproject.toml`` + ``presets/catalog.json``.
``aiadev manifests --write`` (T014) regenerates them in place. This test
is the repo-level tripwire: it derives the three manifests straight from
the real repo sources (via the pure ``aiadev.manifests`` functions, not
a subprocess) and asserts each committed file byte-matches
``render_json(derive_*(...))``. If someone hand-edits a manifest, bumps
``VERSION`` without running ``--write``, or adds a stable preset without
regenerating ``marketplace.json``, this test goes red.
"""

from __future__ import annotations

import json
from pathlib import Path

from aiadev.manifests import (
    derive_cursor_plugin,
    derive_marketplace,
    derive_plugin_manifest,
    read_sources,
    render_json,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_claude_plugin_manifest_matches_derivation():
    sources = read_sources(REPO_ROOT)
    expected = render_json(derive_plugin_manifest(sources.version, sources.pyproject))
    actual = (REPO_ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
    assert actual == expected, (
        ".claude-plugin/plugin.json is out of sync with the derivation; "
        "run `aiadev manifests --write`."
    )


def test_marketplace_manifest_matches_derivation():
    sources = read_sources(REPO_ROOT)
    expected = render_json(
        derive_marketplace(sources.version, sources.pyproject, sources.catalog)
    )
    actual = (REPO_ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8")
    assert actual == expected, (
        ".claude-plugin/marketplace.json is out of sync with the derivation; "
        "run `aiadev manifests --write`."
    )


def test_cursor_plugin_manifest_matches_derivation():
    sources = read_sources(REPO_ROOT)
    expected = render_json(derive_cursor_plugin(sources.version, sources.pyproject))
    actual = (REPO_ROOT / ".cursor-plugin" / "plugin.json").read_text(encoding="utf-8")
    assert actual == expected, (
        ".cursor-plugin/plugin.json is out of sync with the derivation; "
        "run `aiadev manifests --write`."
    )


# ---------------------------------------------------------------------------
# sc4 sanity: the packaged skills/agents paths the manifests advertise must
# actually exist on disk. This is a narrow existence check only — full
# frontmatter/shape conformance of every SKILL.md (including the ones
# migrated in T004) is already covered by tests/test_skills_conformance.py,
# so it is not re-tested here.
# ---------------------------------------------------------------------------


def test_plugin_manifest_skills_and_agents_paths_exist():
    manifest = json.loads(
        (REPO_ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
    )
    skills_dir = REPO_ROOT / manifest["skills"]
    agents_dir = REPO_ROOT / manifest["agents"]
    assert skills_dir.is_dir(), f"{manifest['skills']} does not exist on disk"
    assert agents_dir.is_dir(), f"{manifest['agents']} does not exist on disk"
