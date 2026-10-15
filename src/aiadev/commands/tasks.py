"""``aiadev tasks`` — task bookkeeping commands.

Spec: ``specs/0030-lean-pipeline`` (T027, Story 2 scenario 2).

``tasks done`` flips a task to ``done``, stages the files plus ``tasks.md``
and commits with exactly the message given. If staging or committing fails
(typically a pre-commit hook) the status line is reverted and the paths this
command staged are unstaged again; nothing else in the tree is touched.

Choice: a task that is already ``done`` is not an error. ``mark_done`` is
idempotent, so the command still stages and commits whatever is staged; if
there is nothing to commit, git fails and the command exits 1 (the status
stays ``done`` because it was ``done`` before).

Index safety: the command refuses (exit 1, nothing changed) if any of FILES
or ``tasks.md`` already has staged changes, so rollback never needs an index
snapshot. The commit uses ``--only -- <paths>``, so unrelated staged files
stay staged and out of the commit. FILES resolve against the cwd; pathspecs
are literal (no globbing or magic).
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import click

from ..session_context import context_lines
from ..tasks_status import TasksMdError, mark_done, parse, restore_status


class _GitError(Exception):
    pass


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "GIT_LITERAL_PATHSPECS": "1"}
    return subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, check=False, env=env
    )


def _git_ok(repo: Path, *args: str) -> str:
    proc = _git(repo, *args)
    if proc.returncode != 0:
        detail = (proc.stderr + proc.stdout).strip() or f"exit {proc.returncode}"
        raise _GitError(f"git {args[0]} failed: {detail}")
    return proc.stdout


def _fail(message: str) -> None:
    click.echo(f"ERROR: {message}", err=True)
    sys.exit(1)


def _tracked(repo: Path, path: Path) -> bool:
    """True when git tracks ``path`` (a deletion to commit); literal pathspec."""
    rel = path.relative_to(repo).as_posix()
    proc = _git(repo, "--literal-pathspecs", "ls-files", "--error-unmatch", "--", rel)
    return proc.returncode == 0


def _resolve_files(repo: Path, cwd: Path, files: tuple[str, ...]) -> list[str]:
    out: list[str] = []
    for raw in files:
        path = (cwd / raw).resolve()
        if not path.is_relative_to(repo):
            _fail(f"{raw}: outside the repository")
        if not path.exists() and not _tracked(repo, path):
            _fail(f"{raw}: file does not exist")
        out.append(path.relative_to(repo).as_posix())
    return out


@click.group("tasks", help="Task bookkeeping for specs/<slug>/tasks.md.")
def tasks_command() -> None:
    """Group; subcommands do the work."""


@tasks_command.command("done")
@click.argument("task_id")
@click.option("--feature", required=True, help="Feature slug under specs/.")
@click.option("--commit", "message", required=True, help="Commit message (used verbatim).")
@click.argument("files", nargs=-1)
def done_command(task_id: str, feature: str, message: str, files: tuple[str, ...]) -> None:
    """Mark TASK_ID done, stage FILES + tasks.md and commit."""
    if not feature or "/" in feature or "\\" in feature or ".." in feature:
        raise click.UsageError(f"invalid --feature slug: {feature!r}")

    cwd = Path.cwd().resolve()
    try:
        top = _git_ok(cwd, "rev-parse", "--show-toplevel").strip()
    except _GitError as exc:
        _fail(str(exc))
    repo = Path(top).resolve()
    tasks_md = repo / "specs" / feature / "tasks.md"
    if not tasks_md.is_file():
        _fail(f"{tasks_md.relative_to(repo).as_posix()} not found")

    rel_files = _resolve_files(repo, cwd, files)
    tasks_rel = tasks_md.relative_to(repo).as_posix()

    try:
        row = next((r for r in parse(tasks_md) if r.id == task_id), None)
    except (TasksMdError, OSError, UnicodeDecodeError) as exc:
        _fail(str(exc))
    if row is None:
        _fail(f"task {task_id} not found in {tasks_rel}")
    original_status = row.status

    to_add = list(dict.fromkeys([*rel_files, tasks_rel]))
    for p in to_add:
        if _git(repo, "diff", "--cached", "--quiet", "--", p).returncode != 0:
            _fail(f"{p} already has staged changes; unstage it first (nothing was changed)")

    try:
        mark_done(tasks_md, task_id)
    except (TasksMdError, OSError) as exc:
        _fail(str(exc))

    try:
        _git_ok(repo, "add", "--", *to_add)
        _git_ok(repo, "commit", "-m", message, "--only", "--", *to_add)
        summary = _git_ok(repo, "log", "-1", "--format=%h %s").strip()
    except _GitError as exc:
        # Only the status line and the paths we staged: no checkout/reset.
        causes = [str(exc)]
        if original_status != "done":
            try:
                restore_status(tasks_md, task_id, original_status)
            except (TasksMdError, OSError) as rexc:
                causes.append(f"rollback of {task_id} status failed: {rexc}")
        has_head = _git(repo, "rev-parse", "--verify", "-q", "HEAD").returncode == 0
        undo = (
            ("restore", "--staged", "--") if has_head else ("rm", "--cached", "-f", "-q", "--")
        )
        proc = _git(repo, *undo, *to_add)
        if proc.returncode != 0:
            causes.append(f"unstaging failed: {(proc.stderr + proc.stdout).strip()}")
        _fail("; ".join(causes))

    click.echo(summary)
    for line in context_lines(repo):
        click.echo(line)
