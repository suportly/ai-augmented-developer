"""Tests for the ``aiadev install`` CLI command.

Exercises the wiring only — the engine has its own test suite. We spin
up the real framework layout inside ``isolated_framework`` so every
command path resolves correctly.
"""
from __future__ import annotations

import pathlib

from click.testing import CliRunner

from aiadev.commands.install import install_command


def _invoke(runner: CliRunner, project_root: pathlib.Path, *args: str):
    """Wrapper that always passes --project-root pointing at the tmpdir."""
    return runner.invoke(install_command, ["--project-root", str(project_root), *args])


class TestValidation:
    def test_unknown_preset_exits_two(
        self, isolated_framework: pathlib.Path, tmp_path: pathlib.Path, monkeypatch
    ) -> None:
        monkeypatch.chdir(isolated_framework)
        result = _invoke(
            CliRunner(),
            tmp_path,
            "--preset",
            "does-not-exist",
        )
        assert result.exit_code == 2
        assert "not found" in result.output

    def test_unknown_platform_rejected_by_click(
        self, isolated_framework: pathlib.Path, tmp_path: pathlib.Path, monkeypatch
    ) -> None:
        monkeypatch.chdir(isolated_framework)
        result = _invoke(
            CliRunner(),
            tmp_path,
            "--preset",
            "lean",
            "--platform",
            "typewriter",
        )
        assert result.exit_code == 2  # Click choice rejection.

    def test_invalid_vars_exits_two(
        self, isolated_framework: pathlib.Path, tmp_path: pathlib.Path, monkeypatch
    ) -> None:
        monkeypatch.chdir(isolated_framework)
        result = _invoke(
            CliRunner(),
            tmp_path,
            "--preset",
            "lean",
            "--vars",
            "BROKEN_ENTRY",
            "--non-interactive",
        )
        assert result.exit_code == 2
        assert "invalid" in result.output.lower()


class TestNonInteractiveInstall:
    def test_missing_required_var_exits_one(
        self, isolated_framework: pathlib.Path, tmp_path: pathlib.Path, monkeypatch
    ) -> None:
        # `lean` requires PROJECT_NAME; running non-interactive without it
        # must fail with a clear error.
        monkeypatch.chdir(isolated_framework)
        result = _invoke(
            CliRunner(),
            tmp_path,
            "--preset",
            "lean",
            "--non-interactive",
        )
        assert result.exit_code == 1
        assert "required variable" in result.output

    def test_happy_path_writes_agent_file(
        self, isolated_framework: pathlib.Path, tmp_path: pathlib.Path, monkeypatch
    ) -> None:
        monkeypatch.chdir(isolated_framework)
        result = _invoke(
            CliRunner(),
            tmp_path,
            "--preset",
            "lean",
            "--non-interactive",
            "--vars",
            "PROJECT_NAME=Demo",
        )
        assert result.exit_code == 0, result.output
        assert (tmp_path / "CLAUDE.md").is_file()
        assert "Demo" in (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")

    def test_dry_run_writes_nothing(
        self, isolated_framework: pathlib.Path, tmp_path: pathlib.Path, monkeypatch
    ) -> None:
        monkeypatch.chdir(isolated_framework)
        result = _invoke(
            CliRunner(),
            tmp_path,
            "--preset",
            "lean",
            "--non-interactive",
            "--vars",
            "PROJECT_NAME=Demo",
            "--dry-run",
        )
        assert result.exit_code == 0, result.output
        assert not (tmp_path / "CLAUDE.md").exists()
        assert not (tmp_path / ".aiadev").exists()


class TestReInstall:
    def test_reinstall_uses_stored_values(
        self, isolated_framework: pathlib.Path, tmp_path: pathlib.Path, monkeypatch
    ) -> None:
        monkeypatch.chdir(isolated_framework)
        runner = CliRunner()
        first = _invoke(
            runner,
            tmp_path,
            "--preset",
            "lean",
            "--non-interactive",
            "--vars",
            "PROJECT_NAME=Demo",
        )
        assert first.exit_code == 0, first.output
        # Second run with no vars; non-interactive must succeed because
        # the manifest supplies PROJECT_NAME.
        second = _invoke(
            runner,
            tmp_path,
            "--preset",
            "lean",
            "--non-interactive",
        )
        assert second.exit_code == 0, second.output
        assert "skip" in second.output.lower() or "nothing to do" in second.output


class TestConflictAndForce:
    def test_hand_edited_file_is_conflict(
        self, isolated_framework: pathlib.Path, tmp_path: pathlib.Path, monkeypatch
    ) -> None:
        monkeypatch.chdir(isolated_framework)
        runner = CliRunner()
        _invoke(
            runner,
            tmp_path,
            "--preset",
            "lean",
            "--non-interactive",
            "--vars",
            "PROJECT_NAME=Demo",
        )
        (tmp_path / "CLAUDE.md").write_text("user edit\n", encoding="utf-8")
        second = _invoke(
            runner,
            tmp_path,
            "--preset",
            "lean",
            "--non-interactive",
            "--vars",
            "PROJECT_NAME=Demo",
        )
        assert second.exit_code == 1
        assert "conflict" in second.output.lower()
        assert (tmp_path / "CLAUDE.md").read_text(encoding="utf-8") == "user edit\n"

    def test_force_overwrites(
        self, isolated_framework: pathlib.Path, tmp_path: pathlib.Path, monkeypatch
    ) -> None:
        monkeypatch.chdir(isolated_framework)
        runner = CliRunner()
        _invoke(
            runner,
            tmp_path,
            "--preset",
            "lean",
            "--non-interactive",
            "--vars",
            "PROJECT_NAME=Demo",
        )
        (tmp_path / "CLAUDE.md").write_text("user edit\n", encoding="utf-8")
        forced = _invoke(
            runner,
            tmp_path,
            "--preset",
            "lean",
            "--non-interactive",
            "--vars",
            "PROJECT_NAME=Demo",
            "--force",
        )
        assert forced.exit_code == 0, forced.output
        assert "Demo" in (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")


class TestUninstall:
    def test_uninstall_removes_files_and_manifest(
        self, isolated_framework: pathlib.Path, tmp_path: pathlib.Path, monkeypatch
    ) -> None:
        monkeypatch.chdir(isolated_framework)
        runner = CliRunner()
        _invoke(
            runner,
            tmp_path,
            "--preset",
            "lean",
            "--non-interactive",
            "--vars",
            "PROJECT_NAME=Demo",
        )
        uninstall = _invoke(runner, tmp_path, "--preset", "lean", "--uninstall")
        assert uninstall.exit_code == 0, uninstall.output
        assert not (tmp_path / "CLAUDE.md").exists()
        assert not (tmp_path / ".aiadev").exists()

    def test_uninstall_blocked_by_edit_without_force(
        self, isolated_framework: pathlib.Path, tmp_path: pathlib.Path, monkeypatch
    ) -> None:
        monkeypatch.chdir(isolated_framework)
        runner = CliRunner()
        _invoke(
            runner,
            tmp_path,
            "--preset",
            "lean",
            "--non-interactive",
            "--vars",
            "PROJECT_NAME=Demo",
        )
        (tmp_path / "CLAUDE.md").write_text("user edit\n", encoding="utf-8")
        uninstall = _invoke(runner, tmp_path, "--preset", "lean", "--uninstall")
        assert uninstall.exit_code == 1
        assert "conflict" in uninstall.output.lower()
        assert (tmp_path / "CLAUDE.md").exists()


class TestNonRequiredVars:
    def test_optional_var_defaults_to_empty_string_in_non_interactive(
        self, isolated_framework: pathlib.Path, tmp_path: pathlib.Path, monkeypatch
    ) -> None:
        # lean's PROJECT_NAME is required, but the engine-level flow where
        # optional variables fall back to "" is covered by
        # test_install_engine; here we only verify the CLI does not add a
        # prompt when --non-interactive is set.
        monkeypatch.chdir(isolated_framework)
        result = _invoke(
            CliRunner(),
            tmp_path,
            "--preset",
            "lean",
            "--non-interactive",
            "--vars",
            "PROJECT_NAME=",
        )
        # Empty value satisfies the CLI var parser; engine substitutes "".
        assert result.exit_code == 0, result.output
        agent = tmp_path / "CLAUDE.md"
        assert agent.is_file()
