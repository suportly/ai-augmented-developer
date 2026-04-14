"""Tests for :mod:`aiadev.extensions`.

Each test creates a tmpdir-served bare git repo as the extension
source so no network access is required. The registry root is also
inside ``tmp_path`` to keep the real ``~/.aiadev/`` untouched.
"""
from __future__ import annotations

import pathlib
import shutil
import subprocess

import pytest

from aiadev.extensions import (
    ExtensionError,
    add,
    find_preset,
    list_all,
    load_extension_manifest,
    remove,
)

FIXTURES = pathlib.Path(__file__).parent / "fixtures" / "extensions" / "sample-extension"


def _make_bare_repo(tmp_path: pathlib.Path, fixture_dir: pathlib.Path) -> str:
    """Create a bare git repo in ``tmp_path/source.git`` containing ``fixture_dir``.

    Returns the absolute file:// URL of the bare repo, suitable for
    ``git clone``.
    """
    work = tmp_path / "work"
    bare = tmp_path / "source.git"
    shutil.copytree(fixture_dir, work)
    subprocess.check_call(
        ["git", "init", "-q", "-b", "main"],
        cwd=str(work),
    )
    subprocess.check_call(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t", "add", "."],
        cwd=str(work),
    )
    subprocess.check_call(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "init"],
        cwd=str(work),
    )
    # `-b main` is required so the bare repo's HEAD references the same
    # branch we push to; otherwise `git clone` produces an empty checkout.
    subprocess.check_call(
        ["git", "init", "--bare", "-q", "-b", "main", str(bare)],
    )
    subprocess.check_call(
        ["git", "remote", "add", "origin", str(bare)],
        cwd=str(work),
    )
    subprocess.check_call(
        ["git", "push", "-q", "origin", "main"],
        cwd=str(work),
    )
    return str(bare)


@pytest.fixture
def registry_root(tmp_path: pathlib.Path) -> pathlib.Path:
    return tmp_path / "extensions"


@pytest.fixture
def remote_url(tmp_path: pathlib.Path) -> str:
    return _make_bare_repo(tmp_path, FIXTURES)


# ---------------------------------------------------------------------------
# load_extension_manifest
# ---------------------------------------------------------------------------


class TestLoadManifest:
    def test_valid_fixture_loads(self) -> None:
        data = load_extension_manifest(FIXTURES)
        assert data["name"] == "sample-extension"
        assert "sample" in data["presets"]

    def test_missing_manifest_raises(self, tmp_path: pathlib.Path) -> None:
        with pytest.raises(ExtensionError, match="extension.yaml not found"):
            load_extension_manifest(tmp_path)

    def test_non_mapping_root_raises(self, tmp_path: pathlib.Path) -> None:
        (tmp_path / "extension.yaml").write_text("- a\n- b\n", encoding="utf-8")
        with pytest.raises(ExtensionError, match="mapping"):
            load_extension_manifest(tmp_path)

    def test_schema_violation_raises(self, tmp_path: pathlib.Path) -> None:
        (tmp_path / "extension.yaml").write_text(
            "version: '1.0.0'\n", encoding="utf-8"  # missing name
        )
        with pytest.raises(ExtensionError, match="schema violation"):
            load_extension_manifest(tmp_path)


# ---------------------------------------------------------------------------
# add
# ---------------------------------------------------------------------------


class TestAdd:
    def test_add_clones_and_registers(
        self, remote_url: str, registry_root: pathlib.Path
    ) -> None:
        entry = add(remote_url, registry_root=registry_root)
        assert entry["name"] == "sample-extension"
        assert entry["source"] == remote_url
        assert "sample" in entry["presets"]
        assert (registry_root / "sample-extension" / "extension.yaml").is_file()
        assert (registry_root / "registry.yaml").is_file()

    def test_add_twice_raises(
        self, remote_url: str, registry_root: pathlib.Path
    ) -> None:
        add(remote_url, registry_root=registry_root)
        with pytest.raises(ExtensionError, match="already installed"):
            add(remote_url, registry_root=registry_root)

    def test_add_invalid_url_raises(self, registry_root: pathlib.Path) -> None:
        with pytest.raises(ExtensionError, match="git clone"):
            add("file:///definitely/does/not/exist.git", registry_root=registry_root)


# ---------------------------------------------------------------------------
# list_all
# ---------------------------------------------------------------------------


class TestListAll:
    def test_empty_registry(self, registry_root: pathlib.Path) -> None:
        assert list_all(registry_root=registry_root) == []

    def test_lists_added(
        self, remote_url: str, registry_root: pathlib.Path
    ) -> None:
        add(remote_url, registry_root=registry_root)
        items = list_all(registry_root=registry_root)
        assert len(items) == 1
        assert items[0]["name"] == "sample-extension"


# ---------------------------------------------------------------------------
# remove
# ---------------------------------------------------------------------------


class TestRemove:
    def test_remove_returns_false_when_absent(
        self, registry_root: pathlib.Path
    ) -> None:
        assert remove("nope", registry_root=registry_root) is False

    def test_remove_clears_clone_and_registry(
        self, remote_url: str, registry_root: pathlib.Path
    ) -> None:
        add(remote_url, registry_root=registry_root)
        assert remove("sample-extension", registry_root=registry_root) is True
        assert not (registry_root / "sample-extension").exists()
        # Last extension gone -> registry file gone too.
        assert not (registry_root / "registry.yaml").exists()

    def test_remove_one_of_two_keeps_registry(
        self,
        remote_url: str,
        registry_root: pathlib.Path,
        tmp_path: pathlib.Path,
    ) -> None:
        # Add a second extension by remixing the fixture under a new name.
        second_fixture = tmp_path / "second-fixture"
        shutil.copytree(FIXTURES, second_fixture)
        (second_fixture / "extension.yaml").write_text(
            "name: second-extension\nversion: '1.0.0'\npresets: [sample]\n",
            encoding="utf-8",
        )
        second_url = _make_bare_repo(tmp_path / "second-tmp", second_fixture)

        add(remote_url, registry_root=registry_root)
        add(second_url, registry_root=registry_root)
        remove("sample-extension", registry_root=registry_root)
        remaining = list_all(registry_root=registry_root)
        assert [e["name"] for e in remaining] == ["second-extension"]
        assert (registry_root / "registry.yaml").is_file()


# ---------------------------------------------------------------------------
# find_preset
# ---------------------------------------------------------------------------


class TestFindPreset:
    def test_returns_none_when_no_registry(
        self, registry_root: pathlib.Path
    ) -> None:
        assert find_preset("sample", registry_root=registry_root) is None

    def test_finds_extension_preset(
        self, remote_url: str, registry_root: pathlib.Path
    ) -> None:
        add(remote_url, registry_root=registry_root)
        result = find_preset("sample", registry_root=registry_root)
        assert result is not None
        ext_name, path = result
        assert ext_name == "sample-extension"
        assert path.is_dir()
        assert (path / "preset.yaml").is_file()

    def test_returns_none_for_unknown_preset(
        self, remote_url: str, registry_root: pathlib.Path
    ) -> None:
        add(remote_url, registry_root=registry_root)
        assert find_preset("nope", registry_root=registry_root) is None
