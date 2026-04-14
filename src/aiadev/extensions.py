"""Third-party preset extensions.

Each extension is a git repo whose root contains an ``extension.yaml``
manifest plus a ``presets/`` directory laid out the same way the
framework's built-in presets are. Users add an extension once via
``aiadev extension add <url>``; the engine then falls back to extension
presets when the user passes ``--preset <name>`` and no built-in matches.

Storage layout::

    ~/.aiadev/extensions/
        registry.yaml            # one entry per installed extension
        <ext-name>/              # clone of the upstream repo
            extension.yaml
            presets/
                <preset-name>/
                    preset.yaml
                    CLAUDE.md
                    skills/...

Registry entries::

    aiadev_version: "0.7.0"
    extensions:
      - name: rails-preset
        source: https://github.com/example/rails-preset.git
        version: "v1.0.0-3-gabc123"
        installed_at: "2026-04-14T20:00:00Z"
        presets:
          - rails
          - rails-api
"""
from __future__ import annotations

import datetime as dt
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

from . import __version__
from .paths import schemas_dir

DEFAULT_REGISTRY_FILENAME = "registry.yaml"


class ExtensionError(RuntimeError):
    """Raised when an extension cannot be added, removed, or loaded."""


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------


def default_extensions_root() -> Path:
    """Where the registry and extension clones live (under the user's home)."""
    return Path.home() / ".aiadev" / "extensions"


def _registry_path(root: Path) -> Path:
    return root / DEFAULT_REGISTRY_FILENAME


def _extension_dir(root: Path, name: str) -> Path:
    return root / name


# ---------------------------------------------------------------------------
# Schema validation
# ---------------------------------------------------------------------------


def _manifest_schema() -> Draft202012Validator:
    schema_path = schemas_dir() / "extension-manifest.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    return Draft202012Validator(schema)


def _validate_manifest(data: dict) -> None:
    errors = sorted(_manifest_schema().iter_errors(data), key=lambda e: list(e.path))
    if errors:
        detail = "; ".join(
            f"{'/'.join(str(p) for p in err.path) or '<root>'}: {err.message}"
            for err in errors
        )
        raise ExtensionError(f"extension.yaml schema violation: {detail}")


def load_extension_manifest(extension_dir: Path) -> dict:
    """Read and schema-validate ``<extension-dir>/extension.yaml``."""
    manifest = extension_dir / "extension.yaml"
    if not manifest.is_file():
        raise ExtensionError(f"extension.yaml not found at {manifest}")
    raw = yaml.safe_load(manifest.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise ExtensionError(f"{manifest}: expected a mapping at the root")
    _validate_manifest(raw)
    return raw


# ---------------------------------------------------------------------------
# Registry IO (mirrors install_manifest.py's atomic-write pattern)
# ---------------------------------------------------------------------------


def _empty_registry() -> dict[str, Any]:
    return {"aiadev_version": __version__, "extensions": []}


def _load_registry(root: Path) -> dict[str, Any]:
    path = _registry_path(root)
    if not path.is_file():
        return _empty_registry()
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ExtensionError(f"{path}: YAML parse error: {exc}") from exc
    if not isinstance(raw, dict) or not isinstance(raw.get("extensions"), list):
        raise ExtensionError(f"{path}: malformed registry — expected mapping with `extensions:` list")
    raw.setdefault("aiadev_version", __version__)
    return raw


def _save_registry(root: Path, data: dict[str, Any]) -> None:
    path = _registry_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=".registry-", suffix=".yaml.tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            yaml.safe_dump(data, handle, sort_keys=False, default_flow_style=False)
        os.replace(tmp_name, path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except FileNotFoundError:
            pass
        raise


# ---------------------------------------------------------------------------
# Git operations
# ---------------------------------------------------------------------------


def _git(*args: str, cwd: Path | None = None) -> str:
    """Run a git subcommand and return stdout. Raises ExtensionError on failure."""
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=str(cwd) if cwd else None,
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise ExtensionError("git is not installed or not on PATH") from exc
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.strip() if exc.stderr else "(no stderr)"
        raise ExtensionError(f"git {' '.join(args)} failed: {stderr}") from exc
    return result.stdout.strip()


def _clone(url: str, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    _git("clone", "--depth", "1", url, str(target))


def _describe(repo: Path) -> str:
    try:
        return _git("describe", "--tags", "--always", cwd=repo)
    except ExtensionError:
        # Fall back to the short SHA if no tags.
        return _git("rev-parse", "--short", "HEAD", cwd=repo)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def _utc_now_iso() -> str:
    return (
        dt.datetime.now(dt.timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def add(url: str, *, registry_root: Path | None = None) -> dict[str, Any]:
    """Clone the extension at ``url``, validate, register. Returns the registry entry.

    Raises :class:`ExtensionError` on any failure; on validation failure
    the partial clone is removed so the registry stays consistent.
    """
    root = registry_root or default_extensions_root()

    # Clone into a tempdir first so we can read the manifest before we
    # decide on the final destination (the registered name comes from
    # the manifest, not from the URL).
    with tempfile.TemporaryDirectory(prefix="aiadev-ext-", dir=str(_safe_tmp_root(root))) as tmp:
        staging = Path(tmp) / "clone"
        _clone(url, staging)
        manifest = load_extension_manifest(staging)
        name = manifest["name"]

        registry = _load_registry(root)
        if any(e["name"] == name for e in registry["extensions"]):
            raise ExtensionError(
                f"extension {name!r} already installed; remove it first to update"
            )

        target = _extension_dir(root, name)
        if target.exists():
            raise ExtensionError(
                f"directory {target} already exists; remove it before adding"
            )
        shutil.move(str(staging), str(target))

    version = _describe(target)
    entry = {
        "name": name,
        "source": url,
        "version": version,
        "installed_at": _utc_now_iso(),
        "presets": list(manifest.get("presets", [])),
    }
    registry["extensions"].append(entry)
    _save_registry(root, registry)
    return entry


def list_all(*, registry_root: Path | None = None) -> list[dict[str, Any]]:
    """Return every registered extension."""
    root = registry_root or default_extensions_root()
    return list(_load_registry(root)["extensions"])


def remove(name: str, *, registry_root: Path | None = None) -> bool:
    """Remove an extension's clone and registry entry. Returns ``True`` if removed."""
    root = registry_root or default_extensions_root()
    registry = _load_registry(root)
    remaining = [e for e in registry["extensions"] if e["name"] != name]
    if len(remaining) == len(registry["extensions"]):
        return False
    target = _extension_dir(root, name)
    if target.is_dir():
        shutil.rmtree(target)
    registry["extensions"] = remaining
    if remaining:
        _save_registry(root, registry)
    else:
        # Last extension gone — delete the registry file (and the
        # extensions root if empty) so a clean uninstall leaves no
        # trace.
        registry_path = _registry_path(root)
        if registry_path.is_file():
            registry_path.unlink()
        if root.is_dir() and not any(root.iterdir()):
            root.rmdir()
    return True


def find_preset(
    preset_name: str, *, registry_root: Path | None = None
) -> tuple[str, Path] | None:
    """Look for ``preset_name`` across registered extensions.

    Returns ``(extension_name, preset_path)`` of the first match (registry
    iteration order), or ``None`` if no extension provides that preset.
    """
    root = registry_root or default_extensions_root()
    if not _registry_path(root).is_file():
        return None
    for entry in _load_registry(root)["extensions"]:
        if preset_name in entry.get("presets", []):
            preset_path = _extension_dir(root, entry["name"]) / "presets" / preset_name
            if preset_path.is_dir():
                return entry["name"], preset_path
    return None


def _safe_tmp_root(root: Path) -> Path:
    """Return a directory the tempdir can live next to the registry root.

    Falls back to the system tempdir if the requested root is not yet
    writable (e.g. fresh user with no ~/.aiadev/).
    """
    try:
        root.mkdir(parents=True, exist_ok=True)
        return root
    except OSError:
        return Path(tempfile.gettempdir())
