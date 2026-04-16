"""T008 — workspace_path validation and path traversal protection."""
from __future__ import annotations

import os
import pathlib

import pytest

from aiadev._tooling import InvalidWorkspaceError


class TestValidateWorkspace:
    """Story 3 sc1: reject invalid workspace paths."""

    def test_rejects_nonexistent_directory(self, tmp_path: pathlib.Path) -> None:
        from aiadev._tooling.workspace import validate_workspace

        with pytest.raises(InvalidWorkspaceError):
            validate_workspace(tmp_path / "does-not-exist")

    def test_rejects_file_not_directory(self, tmp_path: pathlib.Path) -> None:
        from aiadev._tooling.workspace import validate_workspace

        f = tmp_path / "afile.txt"
        f.write_text("x")
        with pytest.raises(InvalidWorkspaceError):
            validate_workspace(f)

    def test_rejects_dotdot_traversal(self, tmp_path: pathlib.Path) -> None:
        from aiadev._tooling.workspace import validate_workspace

        traversal = tmp_path / "legit" / ".." / ".." / "etc"
        with pytest.raises(InvalidWorkspaceError):
            validate_workspace(traversal)

    def test_symlink_resolves_to_target(self, tmp_path: pathlib.Path) -> None:
        from aiadev._tooling.workspace import validate_workspace

        real = tmp_path / "real"
        real.mkdir()
        link = tmp_path / "link"
        link.symlink_to(real)
        result = validate_workspace(link)
        assert result == real.resolve()

    def test_accepts_valid_directory(self, tmp_path: pathlib.Path) -> None:
        from aiadev._tooling.workspace import validate_workspace

        result = validate_workspace(tmp_path)
        assert result == tmp_path.resolve()
        assert result.is_absolute()


class TestAssertWithin:
    """Derived path must stay inside workspace."""

    def test_rejects_path_outside_workspace(self, tmp_path: pathlib.Path) -> None:
        from aiadev._tooling.workspace import assert_within

        with pytest.raises(InvalidWorkspaceError):
            assert_within(tmp_path, pathlib.Path("/etc/passwd"))

    def test_accepts_path_inside_workspace(self, tmp_path: pathlib.Path) -> None:
        from aiadev._tooling.workspace import assert_within

        child = tmp_path / "specs" / "0001-foo" / "spec.md"
        assert_within(tmp_path, child)

    def test_rejects_symlink_escaping_workspace(self, tmp_path: pathlib.Path) -> None:
        from aiadev._tooling.workspace import assert_within

        escape_link = tmp_path / "escape"
        escape_link.symlink_to("/tmp")
        target = escape_link / "secret.md"
        with pytest.raises(InvalidWorkspaceError):
            assert_within(tmp_path, target)


class TestComputeTargetPath:
    """T009 — Story 3 sc2 + Story 1 sc1 (NNNN + slug computation)."""

    def test_empty_workspace_starts_at_0001(self, tmp_path: pathlib.Path) -> None:
        from aiadev._tooling.workspace import compute_target_path

        result = compute_target_path(tmp_path, "my feature")
        assert result.parent.name == "0001-my-feature"
        assert result.name == "spec.md"

    def test_increments_from_existing(self, tmp_path: pathlib.Path) -> None:
        from aiadev._tooling.workspace import compute_target_path

        (tmp_path / "specs" / "0007-foo").mkdir(parents=True)
        result = compute_target_path(tmp_path, "bar")
        assert result.parent.name == "0008-bar"

    def test_slugifies_unicode_and_spaces(self, tmp_path: pathlib.Path) -> None:
        from aiadev._tooling.workspace import compute_target_path

        result = compute_target_path(tmp_path, "aiadev como ferramenta")
        assert result.parent.name == "0001-aiadev-como-ferramenta"

    def test_artifact_exists_raises(self, tmp_path: pathlib.Path) -> None:
        from aiadev._tooling import ArtifactExistsError
        from aiadev._tooling.workspace import compute_target_path

        # Pre-create the exact path compute_target_path would generate.
        expected = tmp_path / "specs" / "0001-x" / "spec.md"
        expected.parent.mkdir(parents=True, exist_ok=True)
        expected.write_text("existing")
        with pytest.raises(ArtifactExistsError):
            compute_target_path(tmp_path, "x")

    def test_overwrite_flag_skips_guard(self, tmp_path: pathlib.Path) -> None:
        from aiadev._tooling.workspace import compute_target_path

        expected = tmp_path / "specs" / "0001-x" / "spec.md"
        expected.parent.mkdir(parents=True, exist_ok=True)
        expected.write_text("existing")
        result = compute_target_path(tmp_path, "x", overwrite=True)
        assert result == expected
