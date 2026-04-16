"""Workspace path validation and target path computation."""
from __future__ import annotations

import pathlib

from . import InvalidWorkspaceError


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
