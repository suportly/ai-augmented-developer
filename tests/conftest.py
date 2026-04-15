"""Shared test fixtures."""
from __future__ import annotations

import pathlib
import shutil
import subprocess

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]


@pytest.fixture
def framework_root() -> pathlib.Path:
    """Absolute path to the actual framework checkout under test."""
    assert (REPO_ROOT / "constitution.md").is_file(), "tests must run from a checkout"
    return REPO_ROOT


@pytest.fixture
def isolated_framework(tmp_path: pathlib.Path) -> pathlib.Path:
    """A fresh copy of the framework files in a tmpdir.

    Cheap enough to use per-test; avoids polluting the real checkout when
    commands like ``init`` mutate ``specs/``.
    """
    dest = tmp_path / "framework"
    dest.mkdir()
    for name in ("constitution.md", "VERSION", "README.md"):
        shutil.copy2(REPO_ROOT / name, dest / name)
    for directory in ("templates", "schemas", "skills", "presets", "commands", "agents"):
        if (REPO_ROOT / directory).is_dir():
            shutil.copytree(REPO_ROOT / directory, dest / directory)
    # Initialise a tiny git repo so commands that shell out to git work.
    subprocess.check_call(
        ["git", "init", "-q", "-b", "main"],
        cwd=str(dest),
    )
    subprocess.check_call(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit",
         "--allow-empty", "-qm", "init"],
        cwd=str(dest),
    )
    return dest
