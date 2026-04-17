"""``aiadev lang`` — rewrite the Language header in an existing feature.

Motivation: the natural language of the pipeline artifacts is stamped once
at ``aiadev init --language <code>`` time. Changing your mind later is a
pure text edit — this command does it in one shot instead of asking the
user to hand-edit three files.
"""
from __future__ import annotations

import pathlib
import re
import subprocess

import click
from rich.console import Console

from ..paths import FrameworkNotFound, find_framework_root


_LANGUAGE_PATTERN = re.compile(
    r"^(\*\*Language:\*\*[ \t]+)(\S+)(.*)$",
    re.MULTILINE,
)

_ARTIFACTS = ("spec.md", "plan.md", "tasks.md")

_BRANCH_PREFIXES = ("feature/", "fix/", "chore/", "docs/", "refactor/")


def _current_branch(cwd: pathlib.Path) -> str | None:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=str(cwd),
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        return out or None
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def _slug_from_branch(branch: str) -> str:
    for prefix in _BRANCH_PREFIXES:
        if branch.startswith(prefix):
            return branch[len(prefix):]
    return branch


def _resolve_feature_dir(
    root: pathlib.Path, explicit: str | None
) -> pathlib.Path:
    specs_root = root / "specs"
    if explicit:
        candidate = specs_root / explicit
        if not candidate.is_dir():
            raise click.UsageError(
                f"feature dir not found: specs/{explicit}"
            )
        return candidate

    if not specs_root.is_dir():
        raise click.UsageError("no specs/ directory in this project.")

    branch = _current_branch(root)
    if not branch:
        raise click.UsageError(
            "could not detect current git branch. "
            "Pass --feature <dir> explicitly."
        )

    slug = _slug_from_branch(branch)
    matches = sorted(
        p
        for p in specs_root.iterdir()
        if p.is_dir() and (p.name == slug or p.name.endswith(f"-{slug}"))
    )
    if not matches:
        raise click.UsageError(
            f"no feature directory in specs/ matches branch slug '{slug}'. "
            "Pass --feature <dir> explicitly."
        )
    if len(matches) > 1:
        names = ", ".join(m.name for m in matches)
        raise click.UsageError(
            f"multiple feature dirs match slug '{slug}': {names}. "
            "Pass --feature <dir> explicitly."
        )
    return matches[0]


@click.command("lang")
@click.argument("language")
@click.option(
    "--feature",
    "feature_dir",
    default=None,
    help=(
        "Feature directory under specs/ (e.g. 0008-llm-tool-integration). "
        "Defaults to the one matching the current git branch slug."
    ),
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Print what would change without writing files.",
)
def lang_command(
    language: str,
    feature_dir: str | None,
    dry_run: bool,
) -> None:
    """Rewrite the ``**Language:**`` header in spec.md / plan.md / tasks.md.

    LANGUAGE is a BCP-47 tag such as ``en``, ``pt-BR``, ``es``, ``fr``.
    Only the header is rewritten — prose already in the file is not
    translated. Downstream skills read the header to decide in which
    language to continue writing.
    """
    console = Console()
    try:
        root = find_framework_root()
    except FrameworkNotFound as exc:
        console.print(f"[red]error:[/red] {exc}")
        raise SystemExit(2) from exc

    try:
        target = _resolve_feature_dir(root, feature_dir)
    except click.UsageError as exc:
        console.print(f"[red]error:[/red] {exc.message}")
        raise SystemExit(2) from exc

    touched = 0
    for name in _ARTIFACTS:
        path = target / name
        if not path.is_file():
            console.print(
                f"[yellow]skip[/yellow] {path.relative_to(root)} — file missing"
            )
            continue

        text = path.read_text(encoding="utf-8")
        new_text, count = _LANGUAGE_PATTERN.subn(
            lambda m: f"{m.group(1)}{language}{m.group(3)}",
            text,
            count=1,
        )
        if count == 0:
            console.print(
                f"[yellow]skip[/yellow] {path.relative_to(root)} — "
                "no Language header"
            )
            continue
        if new_text == text:
            console.print(
                f"[dim]unchanged[/dim] {path.relative_to(root)} "
                f"(already {language})"
            )
            continue

        if dry_run:
            console.print(
                f"[yellow]dry-run:[/yellow] would update "
                f"{path.relative_to(root)} → {language}"
            )
        else:
            path.write_text(new_text, encoding="utf-8")
            console.print(
                f"[green]updated[/green] {path.relative_to(root)} → {language}"
            )
        touched += 1

    if touched == 0 and not dry_run:
        console.print(
            "[yellow]no changes made[/yellow] — header already matched, "
            "or no artifact carried a Language header."
        )
        return

    if not dry_run:
        console.print(
            f"\nLanguage header rewritten in [cyan]{target.relative_to(root)}[/cyan]. "
            "Existing prose is untouched — translate manually if needed."
        )
