"""``aiadev doctor`` — run every validator in order and summarize."""
from __future__ import annotations

import json
import pathlib

import click
from rich.console import Console

from ..paths import FrameworkNotFound, find_framework_root, presets_dir
from ..validate import validate_paths


def _check_constitution(root: pathlib.Path, console: Console) -> bool:
    target = root / "constitution.md"
    if not target.is_file():
        console.print(f"[red]FAIL[/red] constitution.md missing at {root}")
        return False
    console.print(f"[green]OK  [/green] constitution.md present")
    return True


def _check_templates(root: pathlib.Path, console: Console) -> bool:
    required = [
        "spec-template.md",
        "plan-template.md",
        "tasks-template.md",
        "checklist-template.md",
        "constitution-template.md",
        "agent-file-template.md",
    ]
    missing = [name for name in required if not (root / "templates" / name).is_file()]
    if missing:
        console.print(f"[red]FAIL[/red] templates/ missing: {', '.join(missing)}")
        return False
    console.print(f"[green]OK  [/green] templates/ complete")
    return True


def _check_catalog(root: pathlib.Path, console: Console) -> bool:
    catalog = presets_dir(root) / "catalog.json"
    if not catalog.is_file():
        console.print(f"[red]FAIL[/red] presets/catalog.json missing")
        return False
    try:
        data = json.loads(catalog.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[red]FAIL[/red] presets/catalog.json: {exc}")
        return False
    if not isinstance(data, dict) or "presets" not in data:
        console.print(f"[red]FAIL[/red] presets/catalog.json has no 'presets' key")
        return False
    bad = [p.get("name") for p in data["presets"] if not (root / p.get("path", "")).is_dir()]
    if bad:
        console.print(f"[red]FAIL[/red] catalog.json references missing presets: {bad}")
        return False
    console.print(f"[green]OK  [/green] presets/catalog.json resolves")
    return True


def _check_skills(root: pathlib.Path, console: Console) -> bool:
    report = validate_paths([], root=root)
    if report.ok:
        console.print(f"[green]OK  [/green] {len(report.passed)} skill(s) valid")
        return True
    for issue in report.failed:
        rel = issue.path.relative_to(root) if issue.path.is_relative_to(root) else issue.path
        console.print(f"[red]FAIL[/red] {rel}: {issue.message}")
    return False


@click.command("doctor")
def doctor_command() -> None:
    """Run every repo-local validator and summarize in one pass."""
    console = Console()
    try:
        root = find_framework_root()
    except FrameworkNotFound as exc:
        console.print(f"[red]error:[/red] {exc}")
        raise SystemExit(2) from exc

    console.print(f"[bold]aiadev doctor[/bold] — framework root: {root}")
    checks = [
        _check_constitution(root, console),
        _check_templates(root, console),
        _check_catalog(root, console),
        _check_skills(root, console),
    ]
    if all(checks):
        console.print("\n[bold green]all checks passed[/bold green]")
        return
    failed = sum(1 for c in checks if not c)
    console.print(f"\n[bold red]{failed} check(s) failed[/bold red]")
    raise SystemExit(1)
