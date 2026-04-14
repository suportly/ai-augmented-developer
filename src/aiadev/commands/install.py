"""``aiadev install`` — materialize a preset for a given platform.

Scope of v0.2 MVP: stub that prints the intended actions. Full install
semantics (variable prompts, platform-specific rendering, symlinks,
plugin.json assembly) land in v0.3.
"""
from __future__ import annotations

import pathlib

import click
from rich.console import Console

from ..paths import FrameworkNotFound, find_framework_root, presets_dir

_PLATFORMS = ("claude-code", "cursor", "codex", "opencode", "gemini")


@click.command("install")
@click.option(
    "--platform",
    type=click.Choice(_PLATFORMS),
    required=True,
    help="Target platform for the plugin install.",
)
@click.option(
    "--preset",
    "preset_name",
    required=True,
    help="Preset name. See `presets/catalog.json`.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Print the actions that would be taken; default for v0.2.",
)
def install_command(platform: str, preset_name: str, dry_run: bool) -> None:
    """Install a preset's files into the current project for the given platform."""
    console = Console()
    try:
        root = find_framework_root()
    except FrameworkNotFound as exc:
        console.print(f"[red]error:[/red] {exc}")
        raise SystemExit(2) from exc

    preset_root = presets_dir(root) / preset_name
    if not preset_root.is_dir():
        console.print(
            f"[red]error:[/red] preset '{preset_name}' not found under {presets_dir(root).relative_to(root)}"
        )
        raise SystemExit(1)

    console.print(
        f"[yellow]aiadev install is a stub in v0.2.[/yellow] "
        "The next release ships variable prompts and platform-specific rendering."
    )
    console.print(
        f"Would install preset [cyan]{preset_name}[/cyan] for platform "
        f"[cyan]{platform}[/cyan]:"
    )
    for child in sorted(preset_root.iterdir()):
        console.print(f"  • {child.relative_to(root)}")

    if not dry_run:
        console.print(
            "\nTo perform the install today, use [cyan]scripts/migrate-to-0.2.sh --apply[/cyan] "
            "(documented in scripts/migrate-to-0.2.sh)."
        )
