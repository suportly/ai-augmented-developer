"""T007 — aiadev._tooling typed errors."""
from __future__ import annotations

import pytest


def test_error_classes_exist_and_are_instantiable() -> None:
    from aiadev._tooling import (
        ArtifactExistsError,
        InvalidWorkspaceError,
        SpecInvalidError,
        SpecNotFoundError,
        UnknownMarkerIdError,
    )

    for cls, code in [
        (InvalidWorkspaceError, "invalid_workspace"),
        (ArtifactExistsError, "artifact_exists"),
        (SpecInvalidError, "spec_invalid"),
        (SpecNotFoundError, "spec_not_found"),
        (UnknownMarkerIdError, "unknown_marker_id"),
    ]:
        err = cls("test message")
        assert err.code == code
        assert str(err) == "test message"
        assert isinstance(err, Exception)
