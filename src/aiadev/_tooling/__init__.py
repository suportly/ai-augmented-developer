"""Shared core for aiadev.tools and aiadev.mcp_server."""
from __future__ import annotations


class _ToolingError(Exception):
    code: str = ""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class InvalidWorkspaceError(_ToolingError):
    code = "invalid_workspace"


class ArtifactExistsError(_ToolingError):
    code = "artifact_exists"


class SpecInvalidError(_ToolingError):
    code = "spec_invalid"


class SpecNotFoundError(_ToolingError):
    code = "spec_not_found"


class UnknownMarkerIdError(_ToolingError):
    code = "unknown_marker_id"
