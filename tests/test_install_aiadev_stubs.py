"""Tests for the ``_aiadev/`` stubs emitted by ``aiadev install``.

Story 2 sc1 of ``specs/0014-bmad-inspired-evolutions/spec.md``:

    Given projeto recém-instalado via `aiadev install --preset lean`,
    when a instalação completa, then os arquivos `_aiadev/team.toml`
    (commit-ready, com header explicando merge rules) e `.gitignore`-entry
    para `_aiadev/user.toml` estão criados; ambos vazios são válidos.

The stubs must be IDEMPOTENT: a second install run must neither
overwrite hand edits to ``_aiadev/team.toml`` nor duplicate the
``.gitignore`` line.
"""
from __future__ import annotations

import pathlib
import tomllib

from click.testing import CliRunner

from aiadev.commands.install import install_command


def _invoke(runner: CliRunner, project_root: pathlib.Path, *args: str):
    return runner.invoke(
        install_command, ["--project-root", str(project_root), *args]
    )


def _install_lean(
    isolated_framework: pathlib.Path,
    project_root: pathlib.Path,
    monkeypatch,
) -> "object":
    monkeypatch.chdir(isolated_framework)
    return _invoke(
        CliRunner(),
        project_root,
        "--preset",
        "lean",
        "--non-interactive",
        "--vars",
        "PROJECT_NAME=Demo",
    )


class TestTeamTomlStub:
    def test_install_creates_team_toml(
        self,
        isolated_framework: pathlib.Path,
        tmp_path: pathlib.Path,
        monkeypatch,
    ) -> None:
        result = _install_lean(isolated_framework, tmp_path, monkeypatch)
        assert result.exit_code == 0, result.output

        team_toml = tmp_path / "_aiadev" / "team.toml"
        assert team_toml.is_file(), "expected _aiadev/team.toml to be emitted"

    def test_team_toml_parses_as_valid_toml(
        self,
        isolated_framework: pathlib.Path,
        tmp_path: pathlib.Path,
        monkeypatch,
    ) -> None:
        _install_lean(isolated_framework, tmp_path, monkeypatch)
        team_toml = tmp_path / "_aiadev" / "team.toml"
        # Must parse cleanly (header comments + nothing else => empty mapping).
        data = tomllib.loads(team_toml.read_text(encoding="utf-8"))
        assert data == {}

    def test_team_toml_header_explains_merge_rules(
        self,
        isolated_framework: pathlib.Path,
        tmp_path: pathlib.Path,
        monkeypatch,
    ) -> None:
        _install_lean(isolated_framework, tmp_path, monkeypatch)
        body = (tmp_path / "_aiadev" / "team.toml").read_text(encoding="utf-8")
        # Header must reference the precedence and the gitignored sibling
        # so a reader understands the merge rules without leaving the file.
        assert "user.toml" in body
        assert "team.toml" in body
        # Reference the docs page hosting the full merge rules.
        assert "docs/customization.md" in body

    def test_team_toml_is_not_overwritten_on_reinstall(
        self,
        isolated_framework: pathlib.Path,
        tmp_path: pathlib.Path,
        monkeypatch,
    ) -> None:
        _install_lean(isolated_framework, tmp_path, monkeypatch)
        team_toml = tmp_path / "_aiadev" / "team.toml"
        edited = (
            "# user keeps their own header\n"
            "[analyze]\n"
            "default_model = \"haiku\"\n"
        )
        team_toml.write_text(edited, encoding="utf-8")

        second = _install_lean(isolated_framework, tmp_path, monkeypatch)
        assert second.exit_code == 0, second.output
        assert team_toml.read_text(encoding="utf-8") == edited


class TestGitignoreEntry:
    def test_install_creates_gitignore_with_user_toml_line(
        self,
        isolated_framework: pathlib.Path,
        tmp_path: pathlib.Path,
        monkeypatch,
    ) -> None:
        _install_lean(isolated_framework, tmp_path, monkeypatch)
        gitignore = tmp_path / ".gitignore"
        assert gitignore.is_file()
        lines = gitignore.read_text(encoding="utf-8").splitlines()
        assert "_aiadev/user.toml" in lines

    def test_install_appends_to_existing_gitignore(
        self,
        isolated_framework: pathlib.Path,
        tmp_path: pathlib.Path,
        monkeypatch,
    ) -> None:
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("node_modules/\n.env\n", encoding="utf-8")

        _install_lean(isolated_framework, tmp_path, monkeypatch)
        body = gitignore.read_text(encoding="utf-8")
        # Pre-existing entries preserved.
        assert "node_modules/" in body
        assert ".env" in body
        # New entry appended.
        assert "_aiadev/user.toml" in body.splitlines()

    def test_install_is_idempotent_for_gitignore(
        self,
        isolated_framework: pathlib.Path,
        tmp_path: pathlib.Path,
        monkeypatch,
    ) -> None:
        _install_lean(isolated_framework, tmp_path, monkeypatch)
        first_lines = (
            (tmp_path / ".gitignore").read_text(encoding="utf-8").splitlines()
        )
        # Second install: the line must not be appended a second time.
        second = _install_lean(isolated_framework, tmp_path, monkeypatch)
        assert second.exit_code == 0, second.output
        second_lines = (
            (tmp_path / ".gitignore").read_text(encoding="utf-8").splitlines()
        )
        assert second_lines.count("_aiadev/user.toml") == 1
        # The full file should be unchanged on the second pass.
        assert first_lines == second_lines

    def test_existing_gitignore_with_entry_is_left_alone(
        self,
        isolated_framework: pathlib.Path,
        tmp_path: pathlib.Path,
        monkeypatch,
    ) -> None:
        gitignore = tmp_path / ".gitignore"
        original = "node_modules/\n_aiadev/user.toml\nbuild/\n"
        gitignore.write_text(original, encoding="utf-8")

        _install_lean(isolated_framework, tmp_path, monkeypatch)
        body = gitignore.read_text(encoding="utf-8")
        assert body.count("_aiadev/user.toml") == 1
        # Pre-existing content order preserved.
        assert body.splitlines()[:3] == ["node_modules/", "_aiadev/user.toml", "build/"]


class TestSyncAssetsManifest:
    """The sync_assets.py manifest knows about the new stub template."""

    def test_team_toml_template_listed_in_sync_assets(self) -> None:
        # The stub body lives next to install.py so sync_assets can ship
        # the canonical template alongside the rest of the framework
        # assets.  When the template changes, sync_assets must pick up
        # the new content; the manifest is the contract.
        from scripts import sync_assets

        sources = [src for src, _dest in sync_assets.COPY_PLAN]
        assert any(
            "_aiadev" in src and src.endswith("team.toml") for src in sources
        ), f"expected an _aiadev/team.toml entry in COPY_PLAN; got {sources!r}"
