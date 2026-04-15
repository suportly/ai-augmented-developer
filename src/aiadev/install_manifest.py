"""Read, write, and validate ``.aiadev/installed.yaml``.

The install engine consults this manifest for three things:

* **Idempotent re-install.** Existing variable values become defaults
  when the user re-runs ``aiadev install`` for the same preset.
* **Drift detection.** Each installed file carries an sha256. On
  re-install, files whose current hash differs from the recorded one
  are reported as conflicts unless ``--force`` is passed.
* **Clean uninstall.** ``--uninstall`` walks the manifest and deletes
  only the files it originally wrote, leaving user code alone.

The manifest format is YAML and the schema lives at
``schemas/install-manifest.schema.json``. Writes are atomic — we
write to a sibling tempfile and ``os.replace`` it into place so a
crash cannot leave a half-written manifest on disk.
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable, Literal

import yaml
from jsonschema import Draft202012Validator

from .paths import find_framework_root, schemas_dir

FileRole = Literal[
    "agent_file",
    "constitution",
    "skill",
    "command",
    "agent",
    "rule",
    "plugin_manifest",
]


@dataclass(frozen=True)
class InstalledFile:
    """One file the install engine wrote into the project."""

    path: str  # Project-root-relative, forward slashes.
    sha256: str
    role: FileRole


@dataclass
class InstalledPreset:
    """One preset's install record inside a :class:`Manifest`."""

    name: str
    version: str
    installed_at: str  # ISO-8601 UTC, seconds precision.
    variables: dict[str, str] = field(default_factory=dict)
    files: list[InstalledFile] = field(default_factory=list)


@dataclass
class Manifest:
    """The top-level ``.aiadev/installed.yaml`` document."""

    aiadev_version: str
    installed_presets: list[InstalledPreset] = field(default_factory=list)

    def find_preset(self, name: str) -> InstalledPreset | None:
        """Return the install record for ``name`` if any."""
        for preset in self.installed_presets:
            if preset.name == name:
                return preset
        return None

    def upsert(self, preset: InstalledPreset) -> None:
        """Insert or replace the install record for ``preset.name``."""
        for idx, existing in enumerate(self.installed_presets):
            if existing.name == preset.name:
                self.installed_presets[idx] = preset
                return
        self.installed_presets.append(preset)

    def remove(self, name: str) -> InstalledPreset | None:
        """Remove and return the install record for ``name`` if any."""
        for idx, existing in enumerate(self.installed_presets):
            if existing.name == name:
                return self.installed_presets.pop(idx)
        return None


class ManifestError(RuntimeError):
    """Raised when a manifest fails to parse or validate."""


def compute_sha256(path: Path) -> str:
    """Hex sha256 of the file at ``path``."""
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _schema_path(framework_root: Path | None) -> Path:
    root = framework_root or find_framework_root()
    return schemas_dir(root) / "install-manifest.schema.json"


def _validator(framework_root: Path | None) -> Draft202012Validator:
    schema = json.loads(_schema_path(framework_root).read_text(encoding="utf-8"))
    return Draft202012Validator(schema)


def load(path: Path, *, framework_root: Path | None = None) -> Manifest:
    """Load and validate ``path``. Raises :class:`ManifestError` on failure."""
    if not path.is_file():
        raise ManifestError(f"install manifest not found at {path}")
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ManifestError(f"{path}: YAML parse error: {exc}") from exc
    if not isinstance(raw, dict):
        raise ManifestError(f"{path}: root must be a mapping, got {type(raw).__name__}")

    errors = sorted(_validator(framework_root).iter_errors(raw), key=lambda e: list(e.path))
    if errors:
        detail = "; ".join(
            f"{'/'.join(str(p) for p in err.path) or '<root>'}: {err.message}"
            for err in errors
        )
        raise ManifestError(f"{path}: schema validation failed: {detail}")

    return _from_dict(raw)


def save(manifest: Manifest, path: Path, *, framework_root: Path | None = None) -> None:
    """Atomically write ``manifest`` to ``path``, validating first."""
    payload = _to_dict(manifest)
    errors = sorted(_validator(framework_root).iter_errors(payload), key=lambda e: list(e.path))
    if errors:
        detail = "; ".join(
            f"{'/'.join(str(p) for p in err.path) or '<root>'}: {err.message}"
            for err in errors
        )
        raise ManifestError(f"refusing to save invalid manifest: {detail}")

    path.parent.mkdir(parents=True, exist_ok=True)
    # Atomic write: tempfile in the same directory, then os.replace.
    fd, tmp_name = tempfile.mkstemp(prefix=".installed-", suffix=".yaml.tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            yaml.safe_dump(payload, handle, sort_keys=False, default_flow_style=False)
        os.replace(tmp_name, path)
    except Exception:
        # Clean up tempfile on any failure; re-raise the original error.
        try:
            os.unlink(tmp_name)
        except FileNotFoundError:
            pass
        raise


def _from_dict(raw: dict[str, Any]) -> Manifest:
    presets: list[InstalledPreset] = []
    for entry in raw.get("installed_presets", []):
        files = [
            InstalledFile(path=f["path"], sha256=f["sha256"], role=f["role"])
            for f in entry.get("files", [])
        ]
        presets.append(
            InstalledPreset(
                name=entry["name"],
                version=entry["version"],
                installed_at=entry["installed_at"],
                variables=dict(entry.get("variables", {})),
                files=files,
            )
        )
    return Manifest(
        aiadev_version=raw["aiadev_version"],
        installed_presets=presets,
    )


def _to_dict(manifest: Manifest) -> dict[str, Any]:
    return {
        "aiadev_version": manifest.aiadev_version,
        "installed_presets": [
            {
                "name": preset.name,
                "version": preset.version,
                "installed_at": preset.installed_at,
                "variables": dict(preset.variables),
                "files": [asdict(f) for f in preset.files],
            }
            for preset in manifest.installed_presets
        ],
    }


def iter_roles() -> Iterable[str]:
    """Yield the allowed :class:`InstalledFile.role` values.

    Exposed so the install engine can assert role validity at write
    time without hard-coding the list.
    """
    return (
        "agent_file",
        "constitution",
        "skill",
        "command",
        "agent",
        "rule",
        "plugin_manifest",
    )
