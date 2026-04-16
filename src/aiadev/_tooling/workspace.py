"""Workspace path validation and target path computation."""
from __future__ import annotations

import pathlib
import re
import unicodedata

from . import ArtifactExistsError, InvalidWorkspaceError


def validate_workspace(path: str | pathlib.Path) -> pathlib.Path:
    """Resolve *path* to an existing directory; reject traversal attempts.

    Raises :class:`InvalidWorkspaceError` if the path does not exist, is not
    a directory, or resolves outside its own parent (symlink escape / ``..``).
    """
    p = pathlib.Path(path).expanduser()
    try:
        resolved = p.resolve(strict=True)
    except OSError as exc:
        raise InvalidWorkspaceError(str(exc)) from exc
    if not resolved.is_dir():
        raise InvalidWorkspaceError(f"Not a directory: {resolved}")
    if p.resolve() != resolved:
        raise InvalidWorkspaceError(f"Path resolves unexpectedly: {p} -> {resolved}")
    return resolved


def assert_within(workspace: pathlib.Path, candidate: pathlib.Path) -> None:
    """Raise :class:`InvalidWorkspaceError` if *candidate* escapes *workspace*."""
    ws = workspace.resolve()
    target = candidate.resolve() if candidate.exists() else pathlib.Path(*candidate.parts).resolve()
    if not str(target).startswith(str(ws)):
        raise InvalidWorkspaceError(
            f"Path {candidate} resolves to {target}, outside workspace {ws}"
        )


def _slugify(text: str) -> str:
    """Convert *text* to a kebab-case slug suitable for directory names."""
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii").lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text or "unnamed"


def compute_target_path(
    workspace: pathlib.Path,
    slug_source: str,
    artifact: str = "spec.md",
    *,
    overwrite: bool = False,
) -> pathlib.Path:
    """Compute ``<workspace>/specs/<NNNN>-<slug>/<artifact>`` with monotonic NNNN.

    Raises :class:`ArtifactExistsError` if the target already exists and
    *overwrite* is False.
    """
    specs_dir = workspace / "specs"
    specs_dir.mkdir(parents=True, exist_ok=True)

    slug = _slugify(slug_source)
    existing_ids: list[int] = []
    existing_match: pathlib.Path | None = None
    for entry in specs_dir.iterdir():
        if entry.is_dir():
            m = re.match(r"^(\d+)-(.+)$", entry.name)
            if m:
                existing_ids.append(int(m.group(1)))
                if m.group(2) == slug and (entry / artifact).exists():
                    existing_match = entry / artifact

    if existing_match is not None:
        if not overwrite:
            raise ArtifactExistsError(
                f"Artifact already exists: {existing_match}"
            )
        return existing_match

    next_id = max(existing_ids, default=0) + 1
    dir_name = f"{next_id:04d}-{slug}"
    return specs_dir / dir_name / artifact
