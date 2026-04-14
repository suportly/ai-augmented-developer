"""``aiadev install`` — render a preset into the current project.

Thin wrapper over :mod:`aiadev.install_engine`; collects the variables,
calls the engine, formats the report through ``rich``.
"""
from __future__ import annotations

import pathlib

import click
import yaml
from rich.console import Console
from rich.table import Table

from ..install_engine import InstallError, InstallMode, install as run_install
from ..install_manifest import ManifestError
from ..paths import FrameworkNotFound, find_framework_root, presets_dir
from ..variable_prompt import VariableError, collect, merge_vars_strings

# Hyphenated names the user types -> module names used by the engine.
_PLATFORM_ALIASES = {
    "claude-code": "claude_code",
    "cursor": "cursor",
    "codex": "codex",
    "opencode": "opencode",
    "gemini": "gemini",
}
_PLATFORM_CHOICES = tuple(_PLATFORM_ALIASES)


@click.command("install")
@click.option(
    "--preset",
    "preset_name",
    required=True,
    help="Preset name as listed in presets/catalog.json (e.g. lean, django-drf-react).",
)
@click.option(
    "--platform",
    type=click.Choice(_PLATFORM_CHOICES),
    default="claude-code",
    show_default=True,
    help="Target platform: claude-code, cursor, codex, opencode, or gemini.",
)
@click.option(
    "--vars",
    "vars_raw",
    multiple=True,
    help=(
        "Inline variables: KEY=VAL,KEY2=VAL2. Pass --vars multiple times "
        "to override earlier values or to carry values that contain commas."
    ),
)
@click.option(
    "--non-interactive",
    is_flag=True,
    help="Fail if any variable would require a prompt. Suited for CI.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show the install plan without writing anything.",
)
@click.option(
    "--uninstall",
    is_flag=True,
    help="Remove the preset's files tracked in the install manifest.",
)
@click.option(
    "--force",
    is_flag=True,
    help="Overwrite conflicting files on install, or delete edited files on uninstall.",
)
@click.option(
    "--allow-unresolved",
    is_flag=True,
    help=(
        "Proceed even when some placeholders do not have a value; the literal "
        "{{KEY}} tokens are written to the output. Use as an escape hatch when "
        "a preset author has forgotten to declare a variable."
    ),
)
@click.option(
    "--scope",
    type=click.Choice(("project", "user")),
    default="project",
    show_default=True,
    help=(
        "Install scope. 'project' writes into the current project (default). "
        "'user' writes only skills into the user's home directory, under "
        "~/.<platform>/skills/<name>/, tracked in ~/.aiadev/installed.yaml. "
        "Agent files and constitutions are skipped under user scope."
    ),
)
@click.option(
    "--project-root",
    "project_root",
    type=click.Path(file_okay=False, path_type=pathlib.Path),
    default=None,
    help="Target project root. Ignored under --scope user. Defaults to cwd.",
)
def install_command(
    preset_name: str,
    platform: str,
    vars_raw: tuple[str, ...],
    non_interactive: bool,
    dry_run: bool,
    uninstall: bool,
    force: bool,
    allow_unresolved: bool,
    scope: str,
    project_root: pathlib.Path | None,
) -> None:
    """Install a preset into the current project or the current user's home."""
    console = Console()

    try:
        framework_root = find_framework_root()
    except FrameworkNotFound as exc:
        console.print(f"[red]error:[/red] {exc}")
        raise SystemExit(2) from exc

    preset_path = presets_dir(framework_root) / preset_name
    if not preset_path.is_dir():
        console.print(
            f"[red]error:[/red] preset {preset_name!r} not found under "
            f"{presets_dir(framework_root).relative_to(framework_root)}"
        )
        raise SystemExit(2)

    if project_root is None:
        project_root = pathlib.Path.cwd()
    project_root = project_root.resolve()

    if scope == "user":
        report_root = pathlib.Path.home()
        if any((vars_raw, project_root != pathlib.Path.cwd().resolve())):
            # --project-root is meaningless under user scope; warn when
            # the user passed something non-default.
            pass  # soft warning; no behavioural side-effect
    else:
        report_root = project_root

    mode = (
        InstallMode.UNINSTALL
        if uninstall
        else InstallMode.DRY_RUN
        if dry_run
        else InstallMode.INSTALL
    )

    # Collect variables (skipped for uninstall).
    variables: dict[str, str] = {}
    if mode is not InstallMode.UNINSTALL:
        try:
            cli_vars = merge_vars_strings(list(vars_raw))
        except VariableError as exc:
            console.print(f"[red]error:[/red] {exc}")
            raise SystemExit(2) from exc

        preset_vars, previous = _load_preset_vars_and_previous(
            preset_path, report_root, preset_name
        )

        try:
            variables = collect(
                preset_vars,
                previous=previous,
                cli_vars=cli_vars,
                non_interactive=non_interactive,
            )
        except VariableError as exc:
            console.print(f"[red]error:[/red] {exc}")
            raise SystemExit(1) from exc

    try:
        report = run_install(
            preset_path,
            project_root,
            variables,
            platform=_PLATFORM_ALIASES[platform],
            mode=mode,
            force=force,
            allow_unresolved=allow_unresolved,
            scope=scope,
        )
    except InstallError as exc:
        console.print(f"[red]error:[/red] {exc}")
        raise SystemExit(1) from exc
    except ManifestError as exc:
        console.print(f"[red]error:[/red] manifest: {exc}")
        raise SystemExit(1) from exc

    _render_report(console, report, report_root, scope=scope)

    if not report.ok:
        raise SystemExit(1)


def _load_preset_vars_and_previous(
    preset_path: pathlib.Path,
    install_root: pathlib.Path,
    preset_name: str,
) -> tuple[list[dict], dict[str, str]]:
    """Read preset.yaml's ``variables`` list and the manifest's stored values."""
    preset_yaml = preset_path / "preset.yaml"
    preset_vars: list[dict] = []
    if preset_yaml.is_file():
        data = yaml.safe_load(preset_yaml.read_text(encoding="utf-8")) or {}
        if isinstance(data, dict):
            raw_vars = data.get("variables", [])
            if isinstance(raw_vars, list):
                preset_vars = [v for v in raw_vars if isinstance(v, dict)]

    previous: dict[str, str] = {}
    manifest_path = install_root / ".aiadev" / "installed.yaml"
    if manifest_path.is_file():
        try:
            from ..install_manifest import load as load_manifest

            manifest = load_manifest(manifest_path)
            record = manifest.find_preset(preset_name)
            if record is not None:
                previous = dict(record.variables)
        except ManifestError:
            # Defer the full error to the engine call; here we just skip
            # using the manifest as a source of defaults.
            pass

    return preset_vars, previous


def _render_report(
    console: Console,
    report,
    report_root: pathlib.Path,
    *,
    scope: str = "project",
) -> None:
    suffix = f" (scope: {scope})"
    table = Table(
        title=f"aiadev install — {report.preset_name} ({report.mode.value}){suffix}"
    )
    table.add_column("Action", style="bold")
    table.add_column("Path")

    def _rel(path: pathlib.Path) -> str:
        try:
            return str(path.relative_to(report_root))
        except ValueError:
            return str(path)

    for path in report.written:
        table.add_row("[green]write[/green]", _rel(path))
    for path in report.skipped:
        table.add_row("[blue]skip[/blue]", _rel(path))
    for path in report.removed:
        table.add_row("[magenta]remove[/magenta]", _rel(path))
    for path in report.conflicts:
        table.add_row("[red]conflict[/red]", _rel(path))

    if report.conflicts or report.removed or report.written or report.skipped:
        console.print(table)
    else:
        console.print(
            f"[yellow]nothing to do[/yellow] for preset "
            f"[cyan]{report.preset_name}[/cyan] (mode: {report.mode.value}, scope: {scope})"
        )

    if report.unresolved:
        console.print(
            f"[yellow]unresolved placeholders:[/yellow] "
            f"{', '.join(sorted(set(report.unresolved)))}"
        )
    if report.skipped_unsupported:
        for note in report.skipped_unsupported:
            console.print(f"[yellow]note:[/yellow] {note}")
    if report.conflicts:
        console.print(
            "[red]refusing to overwrite the files above.[/red] "
            "Pass [cyan]--force[/cyan] to override."
        )
