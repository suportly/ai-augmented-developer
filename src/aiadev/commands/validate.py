"""``aiadev validate`` — check SKILL.md frontmatter against both schemas."""
from __future__ import annotations

import pathlib

import click
from rich.console import Console
from rich.markup import escape

from ..paths import FrameworkNotFound, find_framework_root
from ..validate import validate_paths


@click.command("validate")
@click.argument("paths", nargs=-1, type=click.Path(path_type=pathlib.Path))
@click.option(
    "--quiet",
    is_flag=True,
    help="Print only failures. Exit code still reflects overall success.",
)
def validate_command(paths: tuple[pathlib.Path, ...], quiet: bool) -> None:
    """Validate every SKILL.md frontmatter against both schemas: the vendored
    Agent Skills standard snapshot (schemas/agent-skills.schema.json) and the
    internal shape (schemas/skill-frontmatter.schema.json).

    PATHS: optional list of specific SKILL.md files. If omitted, validates
    every skill under ``skills/`` and ``presets/*/skills/``.
    """
    console = Console()
    try:
        root = find_framework_root()
    except FrameworkNotFound as exc:
        console.print(f"[red]error:[/red] {exc}")
        raise SystemExit(2) from exc

    report = validate_paths(list(paths), root=root)

    if not quiet:
        for path in report.passed:
            console.print(f"[green]OK  [/green] {path.relative_to(root)}")
    for issue in report.failed:
        rel = issue.path.relative_to(root) if issue.path.is_relative_to(root) else issue.path
        # Dual-schema error messages (spec 0016, ADR-3) carry literal
        # "[agent-skills]" / "[aiadev]" origin prefixes; escape them so
        # Rich renders the brackets instead of treating them as markup.
        console.print(f"[red]FAIL[/red] {rel}: {escape(issue.message)}")

    if report.ok:
        if not quiet:
            console.print(
                f"[green]{len(report.passed)} skill(s) passed.[/green]"
            )
        raise SystemExit(0)
    console.print(
        f"[red]{len(report.failed)} skill(s) failed validation; "
        f"{len(report.passed)} passed.[/red]"
    )
    raise SystemExit(1)
