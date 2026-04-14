"""Tests for the ``aiadev install`` CLI command.

Exercises the wiring only — the engine has its own test suite. We spin
up the real framework layout inside ``isolated_framework`` so every
command path resolves correctly.
"""
from __future__ import annotations

import pathlib

import pytest
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


class TestNewPlatforms:
    def test_codex_writes_agents_md_and_codex_skills(
        self, isolated_framework: pathlib.Path, tmp_path: pathlib.Path, monkeypatch
    ) -> None:
        monkeypatch.chdir(isolated_framework)
        result = _invoke(
            CliRunner(),
            tmp_path,
            "--preset",
            "lean",
            "--platform",
            "codex",
            "--non-interactive",
            "--vars",
            "PROJECT_NAME=Demo",
        )
        assert result.exit_code == 0, result.output
        assert (tmp_path / "AGENTS.md").is_file()
        assert not (tmp_path / "CLAUDE.md").exists()

    def test_opencode_writes_agents_md(
        self, isolated_framework: pathlib.Path, tmp_path: pathlib.Path, monkeypatch
    ) -> None:
        monkeypatch.chdir(isolated_framework)
        result = _invoke(
            CliRunner(),
            tmp_path,
            "--preset",
            "lean",
            "--platform",
            "opencode",
            "--non-interactive",
            "--vars",
            "PROJECT_NAME=Demo",
        )
        assert result.exit_code == 0, result.output
        assert (tmp_path / "AGENTS.md").is_file()

    def test_gemini_writes_gemini_md(
        self, isolated_framework: pathlib.Path, tmp_path: pathlib.Path, monkeypatch
    ) -> None:
        monkeypatch.chdir(isolated_framework)
        result = _invoke(
            CliRunner(),
            tmp_path,
            "--preset",
            "lean",
            "--platform",
            "gemini",
            "--non-interactive",
            "--vars",
            "PROJECT_NAME=Demo",
        )
        assert result.exit_code == 0, result.output
        assert (tmp_path / "GEMINI.md").is_file()
        assert not (tmp_path / "AGENTS.md").exists()
        assert not (tmp_path / "CLAUDE.md").exists()

    def test_cursor_then_codex_coexistence(
        self, isolated_framework: pathlib.Path, tmp_path: pathlib.Path, monkeypatch
    ) -> None:
        """Installing the same preset for two IDEs that share AGENTS.md
        must leave only one AGENTS.md file and skip it on the second
        run when the sha matches."""
        monkeypatch.chdir(isolated_framework)
        runner = CliRunner()

        first = _invoke(
            runner, tmp_path,
            "--preset", "lean",
            "--platform", "cursor",
            "--non-interactive",
            "--vars", "PROJECT_NAME=Demo",
        )
        assert first.exit_code == 0, first.output
        assert (tmp_path / "AGENTS.md").is_file()

        second = _invoke(
            runner, tmp_path,
            "--preset", "lean",
            "--platform", "codex",
            "--non-interactive",
            "--vars", "PROJECT_NAME=Demo",
        )
        assert second.exit_code == 0, second.output
        # AGENTS.md already present with matching sha -> reported as skip.
        output = second.output.lower()
        assert "skip" in output or "nothing to do" in output


class TestExtensionPreset:
    """Install picks up a preset that lives in a registered extension."""

    @pytest.fixture
    def fake_home(self, tmp_path: pathlib.Path, monkeypatch) -> pathlib.Path:
        home = tmp_path / "home"
        home.mkdir()
        monkeypatch.setenv("HOME", str(home))
        monkeypatch.setattr(pathlib.Path, "home", staticmethod(lambda: home))
        return home

    def _add_sample_extension(self, fake_home: pathlib.Path) -> None:
        """Install the sample extension fixture into the fake HOME."""
        import shutil
        import subprocess

        fixture = (
            pathlib.Path(__file__).parent
            / "fixtures"
            / "extensions"
            / "sample-extension"
        )
        work = fake_home / "_work"
        bare = fake_home / "_remote.git"
        shutil.copytree(fixture, work)
        subprocess.check_call(["git", "init", "-q", "-b", "main"], cwd=str(work))
        subprocess.check_call(
            ["git", "-c", "user.email=t@t", "-c", "user.name=t", "add", "."],
            cwd=str(work),
        )
        subprocess.check_call(
            ["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "x"],
            cwd=str(work),
        )
        subprocess.check_call(
            ["git", "init", "--bare", "-q", "-b", "main", str(bare)],
        )
        subprocess.check_call(
            ["git", "remote", "add", "origin", str(bare)], cwd=str(work)
        )
        subprocess.check_call(["git", "push", "-q", "origin", "main"], cwd=str(work))
        from aiadev.extensions import add as extension_add

        extension_add(str(bare))

    def test_install_extension_only_preset(
        self,
        isolated_framework: pathlib.Path,
        fake_home: pathlib.Path,
        tmp_path: pathlib.Path,
        monkeypatch,
    ) -> None:
        self._add_sample_extension(fake_home)
        monkeypatch.chdir(isolated_framework)
        project = tmp_path / "project"
        project.mkdir()
        result = _invoke(
            CliRunner(),
            project,
            "--preset",
            "sample",
            "--non-interactive",
            "--vars",
            "PROJECT_NAME=Demo",
        )
        assert result.exit_code == 0, result.output
        assert "from extension" in result.output
        agent = project / "CLAUDE.md"
        assert agent.is_file()
        assert "Demo" in agent.read_text(encoding="utf-8")

    def test_built_in_wins_on_collision(
        self,
        isolated_framework: pathlib.Path,
        fake_home: pathlib.Path,
        tmp_path: pathlib.Path,
        monkeypatch,
    ) -> None:
        import shutil
        import subprocess

        fixture = (
            pathlib.Path(__file__).parent
            / "fixtures"
            / "extensions"
            / "sample-extension"
        )
        clash_root = fake_home / "_clash"
        shutil.copytree(fixture, clash_root)
        (clash_root / "extension.yaml").write_text(
            "name: clash-extension\nversion: '1.0.0'\npresets: [lean]\n",
            encoding="utf-8",
        )
        (clash_root / "presets" / "sample").rename(clash_root / "presets" / "lean")
        bare = fake_home / "_clash.git"
        subprocess.check_call(["git", "init", "-q", "-b", "main"], cwd=str(clash_root))
        subprocess.check_call(
            ["git", "-c", "user.email=t@t", "-c", "user.name=t", "add", "."],
            cwd=str(clash_root),
        )
        subprocess.check_call(
            ["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "x"],
            cwd=str(clash_root),
        )
        subprocess.check_call(
            ["git", "init", "--bare", "-q", "-b", "main", str(bare)],
        )
        subprocess.check_call(
            ["git", "remote", "add", "origin", str(bare)], cwd=str(clash_root)
        )
        subprocess.check_call(["git", "push", "-q", "origin", "main"], cwd=str(clash_root))
        from aiadev.extensions import add as extension_add

        extension_add(str(bare))

        monkeypatch.chdir(isolated_framework)
        project = tmp_path / "project"
        project.mkdir()
        result = _invoke(
            CliRunner(),
            project,
            "--preset",
            "lean",
            "--non-interactive",
            "--vars",
            "PROJECT_NAME=Demo",
        )
        assert result.exit_code == 0, result.output
        # rich wraps the warning across two lines; check for both pieces.
        assert "built-in takes" in result.output
        assert "precedence" in result.output
        agent = project / "CLAUDE.md"
        assert agent.is_file()
        assert "lean preset" in agent.read_text(encoding="utf-8")


class TestUserScope:
    @pytest.fixture
    def fake_home(self, tmp_path: pathlib.Path, monkeypatch) -> pathlib.Path:
        home = tmp_path / "home"
        home.mkdir()
        monkeypatch.setenv("HOME", str(home))
        monkeypatch.setattr(pathlib.Path, "home", staticmethod(lambda: home))
        return home

    def test_user_scope_skips_agent_file_writes_skills(
        self,
        isolated_framework: pathlib.Path,
        fake_home: pathlib.Path,
        tmp_path: pathlib.Path,
        monkeypatch,
    ) -> None:
        monkeypatch.chdir(isolated_framework)
        project = tmp_path / "proj"
        project.mkdir()
        result = CliRunner().invoke(
            install_command,
            [
                "--project-root", str(project),
                "--preset", "lean",
                "--scope", "user",
                "--non-interactive",
                "--vars", "PROJECT_NAME=Demo",
            ],
        )
        assert result.exit_code == 0, result.output
        # Lean preset has no skills, only an agent file — which user
        # scope skips. Expect a "note" line and nothing written.
        assert "note" in result.output.lower()
        assert not (fake_home / "CLAUDE.md").exists()
        assert not (project / "CLAUDE.md").exists()

    def test_user_scope_help_mentions_scope_flag(self) -> None:
        result = CliRunner().invoke(install_command, ["--help"])
        assert "--scope" in result.output
        assert "user" in result.output.lower()


class TestCursorPlatform:
    def test_cursor_install_writes_agents_md(
        self, isolated_framework: pathlib.Path, tmp_path: pathlib.Path, monkeypatch
    ) -> None:
        monkeypatch.chdir(isolated_framework)
        result = _invoke(
            CliRunner(),
            tmp_path,
            "--preset",
            "lean",
            "--platform",
            "cursor",
            "--non-interactive",
            "--vars",
            "PROJECT_NAME=Demo",
        )
        assert result.exit_code == 0, result.output
        assert (tmp_path / "AGENTS.md").is_file()
        # Claude Code's CLAUDE.md must NOT appear.
        assert not (tmp_path / "CLAUDE.md").exists()
        assert "Demo" in (tmp_path / "AGENTS.md").read_text(encoding="utf-8")


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
