"""Pure derivation of the framework's plugin manifests.

Spec: ``specs/0016-agent-skills-interop/spec.md`` (Story 4), ADR-7 (cl-4).

Three files in this repo are Claude Code / Cursor plugin manifests that
today are hand-authored and drift from ``VERSION``:

* ``.claude-plugin/plugin.json`` — the core plugin manifest.
* ``.claude-plugin/marketplace.json`` — the marketplace listing (core
  plugin + one entry per ``stable`` preset in ``presets/catalog.json``).
* ``.cursor-plugin/plugin.json`` — the Claude Code plugin manifest's
  shape plus ``displayName``, for the Cursor marketplace.

This module derives all three, byte-for-byte, from three sources:

* ``VERSION`` — a single line, the framework's release version.
* ``pyproject.toml`` — repo metadata (name, description, authors, URLs).
* ``presets/catalog.json`` — the preset registry; only presets with
  ``stability == "stable"`` become marketplace plugins (cl-4). Adding a
  new stable preset to the catalog therefore produces a new marketplace
  plugin with zero code changes here ("zero-toque").

Every ``derive_*`` function is a pure function: same inputs always
produce the same output dict, with no filesystem or network access.
``read_sources`` is the only I/O boundary, kept separate so the CLI
(T014) and tests can each call the pure functions directly with
in-memory fixtures.

No CLI here — see ``src/aiadev/commands/manifests.py`` (T014) for the
``aiadev manifests --check``/``--write`` subcommand that consumes this
module.
"""
from __future__ import annotations

import json
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_STABLE = "stable"
_VALID_STABILITIES = frozenset({"experimental", "beta", "stable", "deprecated"})

# Human-readable plugin title for manifests that carry a ``displayName``
# field (Cursor). pyproject.toml has no human-readable title to derive
# from — [project].name is the PyPI package (``aiadev``) and the plugin
# slug is ``ai-augmented-developer`` — so the display title is a
# canonical constant here, deterministic by construction. Its value
# matches the committed ``.cursor-plugin/plugin.json``.
_DISPLAY_NAME = "AI-Augmented Developer"


class ManifestDerivationError(ValueError):
    """Raised when a source document is missing a field derivation needs."""


@dataclass(frozen=True)
class Sources:
    """The three inputs every ``derive_*`` function reads from.

    Loaded once by :func:`read_sources`; passed around as plain data so
    the derivation functions themselves stay pure and dependency-free.
    """

    version: str
    pyproject: dict[str, Any]
    catalog: dict[str, Any]


# ---------------------------------------------------------------------------
# Loading (the only I/O boundary)
# ---------------------------------------------------------------------------


def read_sources(root: Path) -> Sources:
    """Read ``VERSION``, ``pyproject.toml``, and ``presets/catalog.json``.

    ``root`` is the framework repo root (the directory containing
    ``VERSION`` and ``pyproject.toml``). Raises ``FileNotFoundError`` if
    any of the three files is missing.
    """
    version = (root / "VERSION").read_text(encoding="utf-8").strip()

    with (root / "pyproject.toml").open("rb") as fh:
        pyproject = tomllib.load(fh)

    catalog_raw = (root / "presets" / "catalog.json").read_text(encoding="utf-8")
    catalog = json.loads(catalog_raw)

    return Sources(version=version, pyproject=pyproject, catalog=catalog)


# ---------------------------------------------------------------------------
# Shared metadata extraction
# ---------------------------------------------------------------------------


def _project_table(pyproject: dict[str, Any]) -> dict[str, Any]:
    project = pyproject.get("project")
    if not isinstance(project, dict):
        raise ManifestDerivationError("pyproject.toml is missing the [project] table")
    return project


def _primary_author(pyproject: dict[str, Any]) -> dict[str, str]:
    authors = _project_table(pyproject).get("authors") or []
    if not authors:
        raise ManifestDerivationError("pyproject.toml [project] is missing authors")
    first = authors[0]
    return {"name": first["name"], "email": first["email"]}


def _homepage(pyproject: dict[str, Any]) -> str:
    urls = _project_table(pyproject).get("urls") or {}
    homepage = urls.get("Homepage")
    if not homepage:
        raise ManifestDerivationError("pyproject.toml [project.urls] is missing Homepage")
    return homepage


def _repository(pyproject: dict[str, Any]) -> str:
    # The framework repo's Homepage IS the repository (a plain GitHub
    # URL); pyproject.toml has no separate "Repository" key today, so
    # both manifest fields point at the same URL.
    return _homepage(pyproject)


def _license(pyproject: dict[str, Any]) -> str:
    license_table = _project_table(pyproject).get("license") or {}
    text = license_table.get("text")
    if not text:
        raise ManifestDerivationError("pyproject.toml [project.license] is missing text")
    return text


# ---------------------------------------------------------------------------
# Derivation: Claude Code plugin.json / Cursor plugin.json (same shape)
# ---------------------------------------------------------------------------


def _base_plugin_manifest(version: str, pyproject: dict[str, Any]) -> dict[str, Any]:
    project = _project_table(pyproject)
    description = project.get("description")
    if not description:
        raise ManifestDerivationError("pyproject.toml [project] is missing description")
    keywords = project.get("keywords") or []

    return {
        "name": "ai-augmented-developer",
        "description": description,
        "version": version,
        "author": _primary_author(pyproject),
        "homepage": _homepage(pyproject),
        "repository": _repository(pyproject),
        "license": _license(pyproject),
        "keywords": list(keywords),
        "skills": "./skills/",
        "agents": "./agents/",
    }


def derive_plugin_manifest(version: str, pyproject: dict[str, Any]) -> dict[str, Any]:
    """Derive ``.claude-plugin/plugin.json``."""
    return _base_plugin_manifest(version, pyproject)


def derive_cursor_plugin(version: str, pyproject: dict[str, Any]) -> dict[str, Any]:
    """Derive ``.cursor-plugin/plugin.json``.

    Same shape as :func:`derive_plugin_manifest` plus ``displayName``,
    the human-readable title Cursor shows in its UI (inserted right
    after ``name``, matching the committed file's key order).
    """
    base = _base_plugin_manifest(version, pyproject)
    manifest: dict[str, Any] = {"name": base["name"], "displayName": _DISPLAY_NAME}
    manifest.update({key: value for key, value in base.items() if key != "name"})
    return manifest


# ---------------------------------------------------------------------------
# Derivation: marketplace.json (core + one plugin per stable preset)
# ---------------------------------------------------------------------------


def _preset_plugins(catalog: dict[str, Any]) -> list[dict[str, Any]]:
    plugins: list[dict[str, Any]] = []
    for preset in catalog.get("presets", []):
        stability = preset.get("stability")
        if stability not in _VALID_STABILITIES:
            raise ManifestDerivationError(
                f"preset {preset.get('name')!r} has invalid stability {stability!r}; "
                f"expected one of {sorted(_VALID_STABILITIES)}"
            )
        if stability != _STABLE:
            continue
        plugins.append(
            {
                "name": preset["name"],
                "description": preset["summary"],
                "version": None,  # filled in by caller with the framework version
                "source": f"./{preset['path']}",
            }
        )
    return plugins


def derive_marketplace(
    version: str, pyproject: dict[str, Any], catalog: dict[str, Any]
) -> dict[str, Any]:
    """Derive ``.claude-plugin/marketplace.json``.

    Lists the core plugin plus one entry per preset whose
    ``stability`` is ``"stable"`` in ``presets/catalog.json``; ``beta``
    and ``experimental`` presets are omitted (cl-4). A stability value
    outside the schema's enum raises :class:`ManifestDerivationError`.
    """
    project = _project_table(pyproject)
    description = project.get("description")
    if not description:
        raise ManifestDerivationError("pyproject.toml [project] is missing description")

    author = _primary_author(pyproject)

    core_plugin = {
        "name": "ai-augmented-developer",
        "description": description,
        "version": version,
        "source": "./",
        "author": author,
    }

    preset_plugins = _preset_plugins(catalog)
    for plugin in preset_plugins:
        plugin["version"] = version

    return {
        "name": "ai-augmented-developer-marketplace",
        "description": "Marketplace config for AI-Augmented Developer skill package",
        "owner": author,
        "plugins": [core_plugin, *preset_plugins],
    }


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


def render_json(obj: Any) -> str:
    """Render ``obj`` as canonical JSON: 2-space indent + trailing newline.

    The generator's format is canonical (ADR-7: the generator is the
    source, the committed files are artifacts). It is standard
    ``json.dumps(obj, indent=2)`` plus exactly one trailing newline —
    which expands arrays one-element-per-line, unlike the hand-authored
    manifests' inline arrays (e.g. ``keywords``). That difference is
    intentional: T015's ``aiadev manifests --write`` normalizes the
    committed files to this format, so expect a one-time formatting
    diff there. No custom inline-array serialization is implemented.

    Deterministic for identical input: dict key order is preserved, not
    sorted, because the ``derive_*`` functions already build dicts in
    the desired key order.
    """
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"
