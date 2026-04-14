"""Tests for :mod:`aiadev.install_manifest`."""
from __future__ import annotations

import datetime as dt
import hashlib
import pathlib

import pytest

from aiadev.install_manifest import (
    InstalledFile,
    InstalledPreset,
    Manifest,
    ManifestError,
    compute_sha256,
    iter_roles,
    load,
    save,
)

FIXTURES = pathlib.Path(__file__).parent / "fixtures" / "manifest"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sample_manifest() -> Manifest:
    return Manifest(
        aiadev_version="0.2.0",
        installed_presets=[
            InstalledPreset(
                name="demo",
                version="1.0.0",
                installed_at="2026-04-14T12:00:00Z",
                variables={"FOO": "bar", "BAZ": "qux"},
                files=[
                    InstalledFile(
                        path="CLAUDE.md",
                        sha256="0" * 64,
                        role="agent_file",
                    ),
                    InstalledFile(
                        path=".claude/skills/foo/SKILL.md",
                        sha256="a" * 64,
                        role="skill",
                    ),
                ],
            )
        ],
    )


# ---------------------------------------------------------------------------
# compute_sha256
# ---------------------------------------------------------------------------


class TestComputeSha256:
    def test_matches_hashlib_for_small_file(self, tmp_path: pathlib.Path) -> None:
        target = tmp_path / "a.txt"
        target.write_bytes(b"hello world")
        assert compute_sha256(target) == hashlib.sha256(b"hello world").hexdigest()

    def test_empty_file(self, tmp_path: pathlib.Path) -> None:
        target = tmp_path / "empty.bin"
        target.write_bytes(b"")
        assert compute_sha256(target) == hashlib.sha256(b"").hexdigest()

    def test_large_file_is_streamed(self, tmp_path: pathlib.Path) -> None:
        target = tmp_path / "big.bin"
        payload = b"0" * (256 * 1024)  # 256 KiB — larger than one read chunk.
        target.write_bytes(payload)
        assert compute_sha256(target) == hashlib.sha256(payload).hexdigest()


# ---------------------------------------------------------------------------
# Load / save round-trip
# ---------------------------------------------------------------------------


class TestLoadSaveRoundTrip:
    def test_save_then_load_returns_equivalent_manifest(
        self, tmp_path: pathlib.Path
    ) -> None:
        manifest = _sample_manifest()
        path = tmp_path / ".aiadev" / "installed.yaml"
        save(manifest, path)
        loaded = load(path)
        assert loaded == manifest

    def test_save_creates_parent_directory(self, tmp_path: pathlib.Path) -> None:
        manifest = _sample_manifest()
        path = tmp_path / "nested" / "dir" / "installed.yaml"
        save(manifest, path)
        assert path.is_file()

    def test_save_is_atomic_no_leftover_tempfile(self, tmp_path: pathlib.Path) -> None:
        path = tmp_path / "installed.yaml"
        save(_sample_manifest(), path)
        siblings = [p.name for p in tmp_path.iterdir() if p.name != "installed.yaml"]
        assert siblings == []


# ---------------------------------------------------------------------------
# Manifest helper methods
# ---------------------------------------------------------------------------


class TestManifestHelpers:
    def test_find_preset_returns_matching_record(self) -> None:
        manifest = _sample_manifest()
        found = manifest.find_preset("demo")
        assert found is not None
        assert found.name == "demo"

    def test_find_preset_returns_none_when_missing(self) -> None:
        assert _sample_manifest().find_preset("absent") is None

    def test_upsert_replaces_existing_record(self) -> None:
        manifest = _sample_manifest()
        replacement = InstalledPreset(
            name="demo",
            version="2.0.0",
            installed_at="2026-04-14T13:00:00Z",
            variables={"FOO": "updated"},
            files=[],
        )
        manifest.upsert(replacement)
        assert len(manifest.installed_presets) == 1
        assert manifest.find_preset("demo") == replacement

    def test_upsert_appends_new_record(self) -> None:
        manifest = _sample_manifest()
        extra = InstalledPreset(
            name="mobile-ops",
            version="1.0.0",
            installed_at="2026-04-14T13:00:00Z",
            variables={},
            files=[],
        )
        manifest.upsert(extra)
        assert [p.name for p in manifest.installed_presets] == ["demo", "mobile-ops"]

    def test_remove_returns_the_removed_preset(self) -> None:
        manifest = _sample_manifest()
        removed = manifest.remove("demo")
        assert removed is not None
        assert removed.name == "demo"
        assert manifest.installed_presets == []

    def test_remove_absent_preset_is_noop(self) -> None:
        manifest = _sample_manifest()
        assert manifest.remove("absent") is None
        assert len(manifest.installed_presets) == 1


# ---------------------------------------------------------------------------
# Error paths
# ---------------------------------------------------------------------------


class TestErrors:
    def test_load_missing_file_raises(self, tmp_path: pathlib.Path) -> None:
        with pytest.raises(ManifestError, match="not found"):
            load(tmp_path / "nope.yaml")

    def test_load_malformed_yaml_raises(self, tmp_path: pathlib.Path) -> None:
        path = tmp_path / "bad.yaml"
        path.write_text("aiadev_version: : :\n", encoding="utf-8")
        with pytest.raises(ManifestError, match="YAML parse error"):
            load(path)

    def test_load_non_mapping_root_raises(self, tmp_path: pathlib.Path) -> None:
        path = tmp_path / "list.yaml"
        path.write_text("- just\n- a\n- list\n", encoding="utf-8")
        with pytest.raises(ManifestError, match="must be a mapping"):
            load(path)

    def test_load_schema_violation_raises(self) -> None:
        with pytest.raises(ManifestError, match="schema validation failed"):
            load(FIXTURES / "invalid_missing_preset_name.yaml")

    def test_load_bad_sha_fails_schema(self) -> None:
        with pytest.raises(ManifestError, match="sha256"):
            load(FIXTURES / "invalid_bad_sha.yaml")

    def test_save_rejects_invalid_manifest(self, tmp_path: pathlib.Path) -> None:
        # A hand-built manifest that the schema rejects: invalid semver.
        invalid = Manifest(
            aiadev_version="not-a-version",
            installed_presets=[],
        )
        with pytest.raises(ManifestError, match="refusing to save"):
            save(invalid, tmp_path / "installed.yaml")

    def test_save_does_not_leave_tempfile_on_failure(
        self, tmp_path: pathlib.Path
    ) -> None:
        invalid = Manifest(aiadev_version="not-a-version")
        with pytest.raises(ManifestError):
            save(invalid, tmp_path / "installed.yaml")
        leftovers = list(tmp_path.glob(".installed-*.yaml.tmp"))
        assert leftovers == []

    def test_save_cleans_tempfile_when_yaml_dump_crashes(
        self, tmp_path: pathlib.Path, monkeypatch
    ) -> None:
        # Force yaml.safe_dump to raise so we hit the cleanup branch in
        # the atomic-write helper.
        import yaml as yaml_module

        from aiadev import install_manifest as im

        def boom(*_args, **_kwargs):
            raise RuntimeError("boom")

        monkeypatch.setattr(im.yaml, "safe_dump", boom)
        with pytest.raises(RuntimeError, match="boom"):
            save(_sample_manifest(), tmp_path / "installed.yaml")
        leftovers = list(tmp_path.glob(".installed-*.yaml.tmp"))
        assert leftovers == []


class TestRolesHelper:
    def test_iter_roles_covers_schema_enum(self) -> None:
        assert set(iter_roles()) == {
            "agent_file",
            "constitution",
            "skill",
            "plugin_manifest",
        }


# ---------------------------------------------------------------------------
# Valid fixture round-trip
# ---------------------------------------------------------------------------


class TestValidFixture:
    def test_fixture_loads_cleanly(self) -> None:
        manifest = load(FIXTURES / "valid.yaml")
        assert manifest.aiadev_version == "0.2.0"
        assert len(manifest.installed_presets) == 1
        preset = manifest.installed_presets[0]
        assert preset.name == "django-drf-react"
        assert preset.variables["PROJECT_NAME"] == "demo"
        assert [f.role for f in preset.files] == ["agent_file", "skill"]
