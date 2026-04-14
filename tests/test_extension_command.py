"""Tests for the ``aiadev extension`` CLI subcommand."""
from __future__ import annotations

import pathlib
import shutil
import subprocess

import pytest
from click.testing import CliRunner

from aiadev.commands.extension import extension_command

FIXTURES = pathlib.Path(__file__).parent / "fixtures" / "extensions" / "sample-extension"


def _make_bare_repo(tmp_path: pathlib.Path, fixture_dir: pathlib.Path) -> str:
    """Build a bare git repo from ``fixture_dir`` and return its path."""
    work = tmp_path / "work"
    bare = tmp_path / "source.git"
    shutil.copytree(fixture_dir, work)
    subprocess.check_call(["git", "init", "-q", "-b", "main"], cwd=str(work))
    subprocess.check_call(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t", "add", "."],
        cwd=str(work),
    )
    subprocess.check_call(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "init"],
        cwd=str(work),
    )
    subprocess.check_call(
        ["git", "init", "--bare", "-q", "-b", "main", str(bare)],
    )
    subprocess.check_call(
        ["git", "remote", "add", "origin", str(bare)], cwd=str(work)
    )
    subprocess.check_call(["git", "push", "-q", "origin", "main"], cwd=str(work))
    return str(bare)


@pytest.fixture
def fake_home(tmp_path: pathlib.Path, monkeypatch) -> pathlib.Path:
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr(pathlib.Path, "home", staticmethod(lambda: home))
    return home


@pytest.fixture
def remote_url(tmp_path: pathlib.Path) -> str:
    return _make_bare_repo(tmp_path / "remote", FIXTURES)


class TestList:
    def test_empty_registry(self, fake_home: pathlib.Path) -> None:
        result = CliRunner().invoke(extension_command, ["list"])
        assert result.exit_code == 0, result.output
        assert "no extensions installed" in result.output.lower()

    def test_lists_added_extension(
        self, fake_home: pathlib.Path, remote_url: str
    ) -> None:
        runner = CliRunner()
        added = runner.invoke(extension_command, ["add", remote_url])
        assert added.exit_code == 0, added.output
        listed = runner.invoke(extension_command, ["list"])
        assert listed.exit_code == 0, listed.output
        assert "sample-extension" in listed.output


class TestAdd:
    def test_add_prints_summary(
        self, fake_home: pathlib.Path, remote_url: str
    ) -> None:
        result = CliRunner().invoke(extension_command, ["add", remote_url])
        assert result.exit_code == 0, result.output
        assert "sample-extension" in result.output
        assert "sample" in result.output  # preset name appears
        assert (fake_home / ".aiadev" / "extensions" / "sample-extension").is_dir()

    def test_add_invalid_url_exits_one(self, fake_home: pathlib.Path) -> None:
        result = CliRunner().invoke(
            extension_command, ["add", "file:///definitely/does/not/exist.git"]
        )
        assert result.exit_code == 1
        assert "error" in result.output.lower()


class TestRemove:
    def test_remove_unknown_exits_one(self, fake_home: pathlib.Path) -> None:
        result = CliRunner().invoke(extension_command, ["remove", "nope"])
        assert result.exit_code == 1
        assert "not installed" in result.output

    def test_remove_round_trip(
        self, fake_home: pathlib.Path, remote_url: str
    ) -> None:
        runner = CliRunner()
        runner.invoke(extension_command, ["add", remote_url])
        result = runner.invoke(extension_command, ["remove", "sample-extension"])
        assert result.exit_code == 0, result.output
        assert "removed" in result.output.lower()
        assert not (fake_home / ".aiadev" / "extensions" / "sample-extension").exists()
