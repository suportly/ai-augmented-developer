"""``aiadev tasks done`` — mark done, stage, commit; roll back on failure.

Spec: specs/0030-lean-pipeline (T027, Story 2 scenario 2).
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from click.testing import CliRunner

from aiadev.cli import main

SLUG = "0099-demo"
TASKS = """# Tasks

### T001 — first

- **Status:** pending

### T002 — second

- **Status:** pending
"""


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, check=True, capture_output=True, text=True
    ).stdout


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "t@example.com")
    _git(tmp_path, "config", "user.name", "T")
    _git(tmp_path, "config", "commit.gpgsign", "false")
    d = tmp_path / "specs" / SLUG
    d.mkdir(parents=True)
    (d / "tasks.md").write_text(TASKS)
    (tmp_path / "keep.txt").write_text("base\n")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-qm", "init")
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _run(*args: str):
    return CliRunner().invoke(main, ["tasks", "done", *args])


def _status(repo: Path, tid: str = "T001") -> str:
    text = (repo / "specs" / SLUG / "tasks.md").read_text()
    block = text.split(f"### {tid} ")[1]
    return block.split("**Status:** ")[1].split()[0]


def test_done_marks_stages_and_commits(repo: Path) -> None:
    (repo / "a.py").write_text("x = 1\n")
    res = _run("T001", "--feature", SLUG, "--commit", "feat: T001 a", "a.py")
    assert res.exit_code == 0, res.output
    assert "feat: T001 a" in res.output
    assert _git(repo, "log", "-1", "--format=%s").strip() == "feat: T001 a"
    shown = _git(repo, "show", "--name-only", "--format=").split()
    assert set(shown) == {"a.py", f"specs/{SLUG}/tasks.md"}
    assert _status(repo) == "done"
    assert _status(repo, "T002") == "pending"


def test_failing_hook_rolls_back_status_and_index(repo: Path) -> None:
    hook = repo / ".git" / "hooks" / "pre-commit"
    hook.write_text("#!/bin/sh\necho 'lint boom' >&2\nexit 1\n")
    hook.chmod(0o755)
    (repo / "a.py").write_text("x = 1\n")
    (repo / "keep.txt").write_text("user edit\n")  # unrelated edit, unstaged
    res = _run("T001", "--feature", SLUG, "--commit", "feat: T001", "a.py")
    assert res.exit_code == 1
    assert "lint boom" in res.output
    assert _status(repo) == "pending"
    assert _git(repo, "diff", "--cached", "--name-only").strip() == ""
    assert (repo / "keep.txt").read_text() == "user edit\n"
    assert (repo / "a.py").read_text() == "x = 1\n"
    assert _git(repo, "log", "-1", "--format=%s").strip() == "init"


def _failing_hook(repo: Path) -> None:
    hook = repo / ".git" / "hooks" / "pre-commit"
    hook.write_text("#!/bin/sh\nexit 1\n")
    hook.chmod(0o755)


def test_refuses_when_target_path_already_staged(repo: Path) -> None:
    (repo / "keep.txt").write_text("staged edit\n")
    _git(repo, "add", "keep.txt")
    res = _run("T001", "--feature", SLUG, "--commit", "m", "keep.txt")
    assert res.exit_code == 1 and "already has staged" in res.output
    assert _status(repo) == "pending"
    assert _git(repo, "diff", "--cached", "--name-only").split() == ["keep.txt"]


def test_unrelated_staged_file_stays_out_of_commit(repo: Path) -> None:
    (repo / "other.txt").write_text("o\n")
    _git(repo, "add", "other.txt")
    (repo / "a.py").write_text("x\n")
    res = _run("T001", "--feature", SLUG, "--commit", "m", "a.py")
    assert res.exit_code == 0, res.output
    assert "other.txt" not in _git(repo, "show", "--name-only", "--format=")
    assert _git(repo, "diff", "--cached", "--name-only").split() == ["other.txt"]


def test_rollback_without_head(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "t@example.com")
    _git(tmp_path, "config", "user.name", "T")
    d = tmp_path / "specs" / SLUG
    d.mkdir(parents=True)
    (d / "tasks.md").write_text(TASKS)
    (tmp_path / "a.py").write_text("x\n")
    _failing_hook(tmp_path)
    monkeypatch.chdir(tmp_path)
    res = _run("T001", "--feature", SLUG, "--commit", "m", "a.py")
    assert res.exit_code == 1
    assert _status(tmp_path) == "pending"
    assert _git(tmp_path, "diff", "--cached", "--name-only").strip() == ""
    assert "unstaging failed" not in res.output


def test_files_resolve_against_cwd_subdir(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    sub = repo / "pkg"
    sub.mkdir()
    (sub / "m.py").write_text("x\n")
    monkeypatch.chdir(sub)
    res = _run("T001", "--feature", SLUG, "--commit", "m", "m.py")
    assert res.exit_code == 0, res.output
    assert "pkg/m.py" in _git(repo, "show", "--name-only", "--format=")


@pytest.mark.parametrize("name", ["[x].py", ":(top)x"])
def test_pathspecs_are_literal(repo: Path, name: str) -> None:
    (repo / name).write_text("x\n")
    (repo / "x.py").write_text("decoy\n")
    (repo / "x").write_text("decoy\n")
    res = _run("T001", "--feature", SLUG, "--commit", "m", name)
    assert res.exit_code == 0, res.output
    shown = _git(repo, "show", "--name-only", "--format=").split("\n")
    assert name in shown and "x.py" not in shown and "x" not in shown


@pytest.mark.parametrize("slug", ["../x", "a/b", "..", ""])
def test_rejects_bad_slug(repo: Path, slug: str) -> None:
    res = _run("T001", "--feature", slug, "--commit", "m")
    assert res.exit_code != 0
    assert _status(repo) == "pending"


def test_rejects_missing_and_outside_files(repo: Path, tmp_path_factory) -> None:
    res = _run("T001", "--feature", SLUG, "--commit", "m", "nope.py")
    assert res.exit_code == 1 and "nope.py" in res.output
    outside = tmp_path_factory.mktemp("out") / "o.txt"
    outside.write_text("x")
    res = _run("T001", "--feature", SLUG, "--commit", "m", str(outside))
    assert res.exit_code == 1
    assert _status(repo) == "pending"


def test_unknown_task_errors_without_changes(repo: Path) -> None:
    res = _run("T099", "--feature", SLUG, "--commit", "m")
    assert res.exit_code == 1
    assert "T099" in res.output
    assert _git(repo, "status", "--porcelain").strip() == ""


def test_already_done_still_commits_staged_changes(repo: Path) -> None:
    assert _run("T001", "--feature", SLUG, "--commit", "one").exit_code == 0
    (repo / "b.py").write_text("y = 2\n")
    res = _run("T001", "--feature", SLUG, "--commit", "two", "b.py")
    assert res.exit_code == 0, res.output
    assert _git(repo, "log", "-1", "--format=%s").strip() == "two"
    assert _status(repo) == "done"


def test_already_done_nothing_to_commit_fails_and_stays_done(repo: Path) -> None:
    assert _run("T001", "--feature", SLUG, "--commit", "one").exit_code == 0
    res = _run("T001", "--feature", SLUG, "--commit", "again")
    assert res.exit_code == 1
    assert _status(repo) == "done"  # was done before; rollback must not revert


def test_commits_a_file_deletion(repo: Path) -> None:
    _git(repo, "rm", "-q", "--cached", "keep.txt")
    (repo / "keep.txt").unlink()
    _git(repo, "reset", "-q", "--", "keep.txt")
    res = _run("T001", "--feature", SLUG, "--commit", "chore: T001", "keep.txt")
    assert res.exit_code == 0, res.output
    assert _status(repo) == "done"
    assert "keep.txt" in _git(repo, "show", "--name-status", "--format=", "HEAD")


def test_rollback_restores_original_in_progress_status(repo: Path) -> None:
    p = repo / "specs" / SLUG / "tasks.md"
    p.write_text(p.read_text().replace("**Status:** pending", "**Status:** in_progress", 1))
    _git(repo, "commit", "-qam", "wip")
    _failing_hook(repo)
    (repo / "a.py").write_text("x = 1\n")
    res = _run("T001", "--feature", SLUG, "--commit", "m", "a.py")
    assert res.exit_code == 1
    assert _status(repo) == "in_progress"
