"""Tests for :mod:`aiadev.install_engine`.

The engine's behaviour is exercised end-to-end against the
``tests/fixtures/mini-preset/`` fixture introduced by T003. Every
branch the spec cares about (install, idempotent re-install, conflict,
force, dry-run, unresolved placeholders, uninstall, uninstall with
conflicts, uninstall with force) has a dedicated test.
"""
from __future__ import annotations

import pathlib

import pytest

from aiadev.install_engine import (
    InstallError,
    InstallMode,
    install,
)
from aiadev.install_manifest import Manifest, load as load_manifest
from aiadev.placeholders import find_unresolved

FIXTURES = pathlib.Path(__file__).parent / "fixtures" / "mini-preset"
VARIABLES = {"PROJECT_NAME": "Demo App", "GREETING": "Howdy"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _agent_file(project_root: pathlib.Path) -> pathlib.Path:
    return project_root / "CLAUDE.md"


def _skill_file(project_root: pathlib.Path, name: str) -> pathlib.Path:
    return project_root / ".claude" / "skills" / name / "SKILL.md"


def _manifest_file(project_root: pathlib.Path) -> pathlib.Path:
    return project_root / ".aiadev" / "installed.yaml"


# ---------------------------------------------------------------------------
# Fresh install
# ---------------------------------------------------------------------------


class TestFreshInstall:
    def test_writes_agent_file_and_skill(self, tmp_path: pathlib.Path) -> None:
        report = install(FIXTURES, tmp_path, VARIABLES, now="2026-04-14T12:00:00Z")

        assert report.mode is InstallMode.INSTALL
        assert report.ok
        assert _agent_file(tmp_path).is_file()
        assert _skill_file(tmp_path, "hello-world").is_file()

        agent_text = _agent_file(tmp_path).read_text(encoding="utf-8")
        assert "Demo App" in agent_text
        assert "Howdy" in agent_text
        assert find_unresolved(agent_text) == []  # every placeholder resolved

        skill_text = _skill_file(tmp_path, "hello-world").read_text(encoding="utf-8")
        assert "Demo App" in skill_text
        assert find_unresolved(skill_text) == []

    def test_writes_manifest(self, tmp_path: pathlib.Path) -> None:
        install(FIXTURES, tmp_path, VARIABLES, now="2026-04-14T12:00:00Z")
        manifest_path = _manifest_file(tmp_path)
        assert manifest_path.is_file()
        manifest = load_manifest(manifest_path)
        record = manifest.find_preset("mini")
        assert record is not None
        assert record.variables == VARIABLES
        assert {f.role for f in record.files} == {"agent_file", "skill"}

    def test_report_lists_every_new_file(self, tmp_path: pathlib.Path) -> None:
        report = install(FIXTURES, tmp_path, VARIABLES, now="2026-04-14T12:00:00Z")
        assert sorted(p.name for p in report.written) == sorted(
            [_agent_file(tmp_path).name, "SKILL.md"]
        )
        assert report.skipped == []
        assert report.conflicts == []
        assert report.removed == []


# ---------------------------------------------------------------------------
# Idempotent re-install
# ---------------------------------------------------------------------------


class TestReInstall:
    def test_same_variables_produces_only_skips(self, tmp_path: pathlib.Path) -> None:
        install(FIXTURES, tmp_path, VARIABLES, now="2026-04-14T12:00:00Z")
        report = install(FIXTURES, tmp_path, VARIABLES, now="2026-04-14T13:00:00Z")
        assert report.written == []
        assert len(report.skipped) == 2
        assert report.conflicts == []

    def test_new_values_rewrite_files(self, tmp_path: pathlib.Path) -> None:
        install(FIXTURES, tmp_path, VARIABLES, now="2026-04-14T12:00:00Z")
        updated = {**VARIABLES, "GREETING": "Bonjour"}
        report = install(FIXTURES, tmp_path, updated, now="2026-04-14T13:00:00Z")
        assert len(report.written) == 2
        assert "Bonjour" in _agent_file(tmp_path).read_text(encoding="utf-8")

    def test_reinstall_preserves_previous_values_for_unspecified_keys(
        self, tmp_path: pathlib.Path
    ) -> None:
        install(FIXTURES, tmp_path, VARIABLES, now="2026-04-14T12:00:00Z")
        # Second call passes only GREETING; PROJECT_NAME must be kept.
        install(
            FIXTURES,
            tmp_path,
            {"GREETING": "Oi"},
            now="2026-04-14T13:00:00Z",
            allow_unresolved=True,
        )
        manifest = load_manifest(_manifest_file(tmp_path))
        record = manifest.find_preset("mini")
        assert record is not None
        assert record.variables["PROJECT_NAME"] == "Demo App"
        assert record.variables["GREETING"] == "Oi"


# ---------------------------------------------------------------------------
# Conflicts
# ---------------------------------------------------------------------------


class TestConflicts:
    def test_hand_edited_file_is_reported_as_conflict(
        self, tmp_path: pathlib.Path
    ) -> None:
        install(FIXTURES, tmp_path, VARIABLES, now="2026-04-14T12:00:00Z")
        _agent_file(tmp_path).write_text("edited by user\n", encoding="utf-8")

        report = install(FIXTURES, tmp_path, VARIABLES, now="2026-04-14T13:00:00Z")
        assert _agent_file(tmp_path) in report.conflicts
        assert _agent_file(tmp_path).read_text(encoding="utf-8") == "edited by user\n"

    def test_force_overwrites_hand_edited_file(self, tmp_path: pathlib.Path) -> None:
        install(FIXTURES, tmp_path, VARIABLES, now="2026-04-14T12:00:00Z")
        _agent_file(tmp_path).write_text("edited by user\n", encoding="utf-8")

        report = install(
            FIXTURES,
            tmp_path,
            VARIABLES,
            force=True,
            now="2026-04-14T13:00:00Z",
        )
        assert report.conflicts == []
        assert "Demo App" in _agent_file(tmp_path).read_text(encoding="utf-8")

    def test_pre_existing_file_on_first_install_is_conflict(
        self, tmp_path: pathlib.Path
    ) -> None:
        # No prior manifest. An existing CLAUDE.md is unknown territory.
        _agent_file(tmp_path).write_text("my own CLAUDE.md\n", encoding="utf-8")
        report = install(FIXTURES, tmp_path, VARIABLES, now="2026-04-14T12:00:00Z")
        assert _agent_file(tmp_path) in report.conflicts


# ---------------------------------------------------------------------------
# Dry run
# ---------------------------------------------------------------------------


class TestDryRun:
    def test_dry_run_reports_but_writes_nothing(self, tmp_path: pathlib.Path) -> None:
        report = install(
            FIXTURES,
            tmp_path,
            VARIABLES,
            mode=InstallMode.DRY_RUN,
            now="2026-04-14T12:00:00Z",
        )
        assert len(report.written) == 2
        assert not _agent_file(tmp_path).exists()
        assert not _skill_file(tmp_path, "hello-world").exists()
        assert not _manifest_file(tmp_path).exists()


# ---------------------------------------------------------------------------
# Unresolved placeholders
# ---------------------------------------------------------------------------


class TestUnresolvedPlaceholders:
    def test_missing_variable_errors_by_default(self, tmp_path: pathlib.Path) -> None:
        with pytest.raises(InstallError, match="unresolved placeholders"):
            install(
                FIXTURES,
                tmp_path,
                {"PROJECT_NAME": "Demo"},  # GREETING omitted
                now="2026-04-14T12:00:00Z",
            )

    def test_allow_unresolved_writes_files_and_reports_keys(
        self, tmp_path: pathlib.Path
    ) -> None:
        # --allow-unresolved is the escape hatch: files are written even
        # when placeholders survive substitution; the report enumerates
        # which keys remained so the user can fix the preset later.
        report = install(
            FIXTURES,
            tmp_path,
            {"PROJECT_NAME": "Demo"},
            allow_unresolved=True,
            now="2026-04-14T12:00:00Z",
        )
        assert len(report.written) == 2
        assert "GREETING" in report.unresolved
        # The literal {{GREETING}} survives in the output.
        agent_text = _agent_file(tmp_path).read_text(encoding="utf-8")
        assert "{{GREETING}}" in agent_text


# ---------------------------------------------------------------------------
# Uninstall
# ---------------------------------------------------------------------------


class TestUninstall:
    def test_removes_files_and_clears_manifest(self, tmp_path: pathlib.Path) -> None:
        install(FIXTURES, tmp_path, VARIABLES, now="2026-04-14T12:00:00Z")
        report = install(
            FIXTURES,
            tmp_path,
            VARIABLES,
            mode=InstallMode.UNINSTALL,
        )
        assert report.ok
        assert len(report.removed) == 2
        assert not _agent_file(tmp_path).exists()
        assert not _skill_file(tmp_path, "hello-world").exists()
        assert not _manifest_file(tmp_path).exists()

    def test_uninstall_without_prior_install_is_noop(
        self, tmp_path: pathlib.Path
    ) -> None:
        report = install(
            FIXTURES,
            tmp_path,
            VARIABLES,
            mode=InstallMode.UNINSTALL,
        )
        assert report.removed == []
        assert report.conflicts == []

    def test_edited_file_blocks_uninstall(self, tmp_path: pathlib.Path) -> None:
        install(FIXTURES, tmp_path, VARIABLES, now="2026-04-14T12:00:00Z")
        _agent_file(tmp_path).write_text("user-added content\n", encoding="utf-8")
        report = install(
            FIXTURES,
            tmp_path,
            VARIABLES,
            mode=InstallMode.UNINSTALL,
        )
        assert _agent_file(tmp_path) in report.conflicts
        assert _agent_file(tmp_path).exists()
        # Manifest must still describe the preset — we did not uninstall it.
        assert _manifest_file(tmp_path).is_file()

    def test_force_uninstall_removes_edited_file(self, tmp_path: pathlib.Path) -> None:
        install(FIXTURES, tmp_path, VARIABLES, now="2026-04-14T12:00:00Z")
        _agent_file(tmp_path).write_text("user-added content\n", encoding="utf-8")
        report = install(
            FIXTURES,
            tmp_path,
            VARIABLES,
            mode=InstallMode.UNINSTALL,
            force=True,
        )
        assert _agent_file(tmp_path) in report.removed
        assert not _manifest_file(tmp_path).exists()


# ---------------------------------------------------------------------------
# Misconfiguration
# ---------------------------------------------------------------------------


class TestUserScope:
    """Tests for --scope user behaviour.

    Every test in this class monkeypatches HOME to a tmp_path so nothing
    touches the real user home directory.
    """

    @pytest.fixture
    def fake_home(self, tmp_path: pathlib.Path, monkeypatch) -> pathlib.Path:
        home = tmp_path / "home"
        home.mkdir()
        monkeypatch.setenv("HOME", str(home))
        # Path.home() on POSIX honours HOME; make absolutely sure.
        monkeypatch.setattr(pathlib.Path, "home", staticmethod(lambda: home))
        return home

    def test_user_scope_writes_skill_under_home(
        self, fake_home: pathlib.Path, tmp_path: pathlib.Path
    ) -> None:
        project = tmp_path / "unused-project"
        project.mkdir()
        report = install(
            FIXTURES,
            project,
            VARIABLES,
            scope="user",
            now="2026-04-14T12:00:00Z",
        )
        # Agent file is skipped under user scope (not installable).
        assert report.skipped_unsupported
        # The only skill in the mini-preset lands under .claude/skills/.
        skill_target = fake_home / ".claude" / "skills" / "hello-world" / "SKILL.md"
        assert skill_target.is_file()
        # No CLAUDE.md at home root or project root.
        assert not (fake_home / "CLAUDE.md").exists()
        assert not (project / "CLAUDE.md").exists()

    def test_user_scope_manifest_is_under_home(
        self, fake_home: pathlib.Path, tmp_path: pathlib.Path
    ) -> None:
        project = tmp_path / "unused"
        project.mkdir()
        install(FIXTURES, project, VARIABLES, scope="user", now="2026-04-14T12:00:00Z")
        assert (fake_home / ".aiadev" / "installed.yaml").is_file()
        # No project-scope manifest was created.
        assert not (project / ".aiadev").exists()

    def test_user_scope_uninstall_round_trip(
        self, fake_home: pathlib.Path, tmp_path: pathlib.Path
    ) -> None:
        project = tmp_path / "unused"
        project.mkdir()
        install(FIXTURES, project, VARIABLES, scope="user", now="2026-04-14T12:00:00Z")
        uninstall_report = install(
            FIXTURES,
            project,
            VARIABLES,
            scope="user",
            mode=InstallMode.UNINSTALL,
        )
        assert uninstall_report.ok
        assert not (fake_home / ".claude").exists()
        assert not (fake_home / ".aiadev").exists()

    def test_user_and_project_scopes_are_independent(
        self, fake_home: pathlib.Path, tmp_path: pathlib.Path
    ) -> None:
        project = tmp_path / "real-project"
        project.mkdir()
        # Install at project scope first.
        install(FIXTURES, project, VARIABLES, now="2026-04-14T12:00:00Z")
        assert (project / "CLAUDE.md").is_file()
        assert (project / ".aiadev" / "installed.yaml").is_file()

        # Now install at user scope; project artifacts untouched.
        install(FIXTURES, project, VARIABLES, scope="user", now="2026-04-14T13:00:00Z")
        assert (fake_home / ".claude" / "skills" / "hello-world" / "SKILL.md").is_file()
        assert (fake_home / ".aiadev" / "installed.yaml").is_file()
        assert (project / "CLAUDE.md").is_file()  # still there
        assert (project / ".aiadev" / "installed.yaml").is_file()

    def test_unknown_scope_raises(self, tmp_path: pathlib.Path) -> None:
        with pytest.raises(InstallError, match="unknown scope"):
            install(FIXTURES, tmp_path, VARIABLES, scope="moon")


class TestMisconfiguration:
    def test_unknown_platform_raises(self, tmp_path: pathlib.Path) -> None:
        with pytest.raises(InstallError, match="unknown platform"):
            install(FIXTURES, tmp_path, VARIABLES, platform="typewriter")

    def test_missing_preset_yaml_raises(self, tmp_path: pathlib.Path) -> None:
        empty = tmp_path / "preset"
        empty.mkdir()
        with pytest.raises(InstallError, match="preset.yaml not found"):
            install(empty, tmp_path / "project", VARIABLES)

    def test_preset_yaml_not_a_mapping_raises(self, tmp_path: pathlib.Path) -> None:
        preset_dir = tmp_path / "preset"
        preset_dir.mkdir()
        (preset_dir / "preset.yaml").write_text("- a\n- b\n", encoding="utf-8")
        with pytest.raises(InstallError, match="mapping"):
            install(preset_dir, tmp_path / "project", VARIABLES)
