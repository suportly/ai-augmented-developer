"""``aiadev extension <add|list|remove>`` — manage third-party extensions."""
from __future__ import annotations

import click
from rich.console import Console
from rich.table import Table

from ..extensions import (
    ExtensionError,
    add as extension_add,
    list_all as extension_list_all,
    remove as extension_remove,
)


@click.group("extension")
def extension_command() -> None:
    """Manage third-party preset extensions installed under ~/.aiadev/extensions/."""


@extension_command.command("add")
@click.argument("url")
def extension_add_command(url: str) -> None:
    """Clone an extension from URL and register it for `aiadev install --preset`."""
    console = Console()
    try:
        entry = extension_add(url)
    except ExtensionError as exc:
        console.print(f"[red]error:[/red] {exc}")
        raise SystemExit(1) from exc

    console.print(f"[green]added[/green] extension [cyan]{entry['name']}[/cyan]")
    console.print(f"  source:    {entry['source']}")
    console.print(f"  version:   {entry['version']}")
    presets = ", ".join(entry.get("presets", [])) or "(none declared)"
    console.print(f"  presets:   {presets}")


@extension_command.command("list")
def extension_list_command() -> None:
    """Print every registered extension."""
    console = Console()
    try:
        entries = extension_list_all()
    except ExtensionError as exc:
        console.print(f"[red]error:[/red] {exc}")
        raise SystemExit(1) from exc

    if not entries:
        console.print("[yellow]no extensions installed[/yellow]")
        return

    table = Table(title="aiadev extensions")
    table.add_column("Name", style="bold cyan")
    table.add_column("Source")
    table.add_column("Version")
    table.add_column("Installed")
    table.add_column("Presets")
    for entry in entries:
        presets = ", ".join(entry.get("presets", [])) or "—"
        table.add_row(
            entry["name"],
            entry["source"],
            entry["version"],
            entry["installed_at"],
            presets,
        )
    console.print(table)


@extension_command.command("remove")
@click.argument("name")
def extension_remove_command(name: str) -> None:
    """Delete an extension's clone and registry entry."""
    console = Console()
    try:
        removed = extension_remove(name)
    except ExtensionError as exc:
        console.print(f"[red]error:[/red] {exc}")
        raise SystemExit(1) from exc
    if not removed:
        console.print(f"[red]error:[/red] extension {name!r} is not installed")
        raise SystemExit(1)
    console.print(f"[green]removed[/green] extension [cyan]{name}[/cyan]")
