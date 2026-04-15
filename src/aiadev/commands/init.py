"""``aiadev init`` — scaffold a feature directory under ``specs/<NNNN-slug>/``."""
from __future__ import annotations

import datetime as dt
import pathlib
import re
import subprocess

import click
from rich.console import Console

from ..paths import FrameworkNotFound, find_framework_root, templates_dir


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    if not slug:
        raise click.BadParameter("feature name must contain at least one alphanumeric character")
    return slug


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


def _create_branch(cwd: pathlib.Path, branch: str, dry_run: bool) -> None:
    if dry_run:
        return
    subprocess.check_call(
        ["git", "checkout", "-b", branch], cwd=str(cwd), stderr=subprocess.DEVNULL
    )


def _render_template(template: pathlib.Path, substitutions: dict[str, str]) -> str:
    text = template.read_text(encoding="utf-8")
    for key, value in substitutions.items():
        text = text.replace(f"{{{{{key}}}}}", value)
    return text


def _find_next_spec_id(specs_root: pathlib.Path) -> str:
    existing: list[int] = []
    if specs_root.is_dir():
        for entry in specs_root.iterdir():
            if not entry.is_dir():
                continue
            spec_file = entry / "spec.md"
            if not spec_file.is_file():
                continue
            # Tolerate surrounding Markdown emphasis: **Spec ID:** 0001
            match = re.search(r"Spec ID:[\s*]*?(\d+)", spec_file.read_text(encoding="utf-8"))
            if match:
                existing.append(int(match.group(1)))
    return f"{max(existing) + 1 if existing else 1:04d}"


@click.command("init")
@click.option(
    "--feature",
    "feature_name",
    required=True,
    help="Human-readable feature name. Becomes the feature slug and spec heading.",
)
@click.option(
    "--branch",
    "branch_name",
    default=None,
    help="Git branch name to create. Defaults to 'feature/<slug>'. Use '-' to stay on the current branch.",
)
@click.option(
    "--no-git",
    is_flag=True,
    help="Skip the git branch creation step (still writes files).",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Print what would be done without writing files or creating branches.",
)
def init_command(
    feature_name: str, branch_name: str | None, no_git: bool, dry_run: bool
) -> None:
    """Scaffold ``specs/<branch>/{spec,plan,tasks}.md`` from the templates."""
    console = Console()
    try:
        root = find_framework_root()
    except FrameworkNotFound as exc:
        console.print(f"[red]error:[/red] {exc}")
        raise SystemExit(2) from exc

    slug = _slugify(feature_name)
    if branch_name is None:
        branch_name = f"feature/{slug}"

    specs_root = root / "specs"
    spec_id = _find_next_spec_id(specs_root)
    # Feature dir always carries the zero-padded spec_id prefix so specs
    # sort chronologically: ``specs/0001-<slug>/``.
    feature_dir_name = f"{spec_id}-{slug}"
    feature_dir = specs_root / feature_dir_name

    if feature_dir.exists():
        console.print(
            f"[red]error:[/red] {feature_dir.relative_to(root)} already exists; refusing to overwrite."
        )
        raise SystemExit(1)

    # Branch management.
    if branch_name != "-" and not no_git:
        current = _current_branch(root)
        if current != branch_name:
            console.print(f"Creating git branch [cyan]{branch_name}[/cyan] from [cyan]{current}[/cyan]")
            try:
                _create_branch(root, branch_name, dry_run)
            except subprocess.CalledProcessError as exc:
                console.print(
                    f"[red]error:[/red] failed to create branch {branch_name}: {exc}"
                )
                raise SystemExit(1) from exc

    substitutions = {
        "FEATURE_NAME": feature_name,
        "BRANCH": branch_name if branch_name != "-" else (_current_branch(root) or "main"),
        "DATE": dt.date.today().isoformat(),
        "SPEC_ID": spec_id,
        "SHORT_TITLE": feature_name,
        "ROLE": "user",
        "ACTION": "",
        "OUTCOME": "",
        "ISSUE_URL": "",
        "LIST_OR_NONE": "None",
        "PRESET_NAME": "",
        "LANGUAGE": "",
        "DEPS": "",
        "STORAGE": "",
        "TEST_FRAMEWORK": "",
        "TARGETS": "",
        "PERF_BUDGET_OR_NA": "N/A",
        "SECURITY_NOTES": "",
        "PHASE_1_NAME": "",
        "PHASE_2_NAME": "",
        "RISK": "",
        "MITIGATION": "",
        "AREA": "",
        "TEST_COMMAND": "",
    }

    templates = templates_dir(root)
    artifacts = [
        (templates / "spec-template.md", feature_dir / "spec.md"),
        (templates / "plan-template.md", feature_dir / "plan.md"),
        (templates / "tasks-template.md", feature_dir / "tasks.md"),
    ]

    if dry_run:
        console.print(f"[yellow]dry-run:[/yellow] would create {feature_dir.relative_to(root)}/")
        for _, dest in artifacts:
            console.print(f"  [yellow]dry-run:[/yellow] {dest.relative_to(root)}")
        return

    feature_dir.mkdir(parents=True, exist_ok=False)
    for src, dest in artifacts:
        if not src.exists():
            console.print(f"[red]error:[/red] template missing: {src}")
            raise SystemExit(2)
        dest.write_text(_render_template(src, substitutions), encoding="utf-8")
        console.print(f"[green]wrote[/green] {dest.relative_to(root)}")

    console.print(
        f"\nNext step: open [cyan]{feature_dir.relative_to(root)}/spec.md[/cyan] and invoke the [bold]specify[/bold] skill."
    )
