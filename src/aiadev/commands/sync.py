"""``aiadev sync`` — re-pull installed artifacts and refresh the stack block.

The sync flow has two steps:

1. **Re-install every preset recorded in .aiadev/installed.yaml.** Uses
   the same engine as ``aiadev install`` with the variables captured at
   install time. Framework-generic artifacts (commands/agents/skills)
   come along for the ride, so projects that installed under an older
   ``aiadev`` pick up any new pipeline files the framework grew since.
2. **Regenerate the ``<!-- aiadev:auto-stack -->`` block in the agent
   file.** Reads well-known config files (package.json, pyproject.toml,
   docker-compose.yml, Makefile, .github/workflows/) via
   :func:`aiadev.project_introspect.introspect` and writes a stack
   summary. Content outside the markers is preserved byte-for-byte.

Flags control granularity: ``--skip-artifacts`` runs only step 2,
``--skip-stack`` runs only step 1. ``--dry-run`` and ``--force`` mirror
the flags on ``aiadev install``.
"""
from __future__ import annotations

import datetime as dt
import pathlib

import click
from rich.console import Console
from rich.table import Table

from ..install_engine import InstallError, InstallMode, install as run_install
from ..install_manifest import ManifestError, load as load_manifest
from ..paths import FrameworkNotFound, find_framework_root
from ..project_introspect import apply_stack_block, introspect, render_stack_block

_PLATFORM_DIRS = {
    ".claude": "claude_code",
    ".cursor": "cursor",
    ".codex": "codex",
    ".opencode": "opencode",
    ".gemini": "gemini",
}

_PLATFORM_AGENT_FILE = {
    "claude_code": "CLAUDE.md",
    "cursor": "AGENTS.md",
    "codex": "AGENTS.md",
    "opencode": "AGENTS.md",
    "gemini": "GEMINI.md",
}


@click.command("sync")
@click.option(
    "--project-root",
    "project_root",
    type=click.Path(file_okay=False, path_type=pathlib.Path),
    default=None,
    help="Project root to sync. Defaults to the current directory.",
)
@click.option(
    "--platform",
    "platform",
    type=click.Choice(("claude-code", "cursor", "codex", "opencode", "gemini")),
    default=None,
    help="Force a specific platform. Default: auto-detect from the project layout.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show the plan without writing anything.",
)
@click.option(
    "--force",
    is_flag=True,
    help="Overwrite conflicting files (hand-edited artifacts).",
)
@click.option(
    "--skip-artifacts",
    is_flag=True,
    help="Skip step 1 (artifact re-sync); run only the stack-block refresh.",
)
@click.option(
    "--skip-stack",
    is_flag=True,
    help="Skip step 2 (stack-block refresh); run only the artifact re-sync.",
)
def sync_command(
    project_root: pathlib.Path | None,
    platform: str | None,
    dry_run: bool,
    force: bool,
    skip_artifacts: bool,
    skip_stack: bool,
) -> None:
    """Re-sync installed artifacts and regenerate the Detected Stack block."""
    console = Console()

    project = (project_root or pathlib.Path.cwd()).resolve()
    manifest_path = project / ".aiadev" / "installed.yaml"
    if not manifest_path.is_file():
        console.print(
            f"[red]error:[/red] no install manifest at {manifest_path}. "
            "Run `aiadev install --preset <name>` first."
        )
        raise SystemExit(2)

    try:
        framework_root = find_framework_root()
    except FrameworkNotFound as exc:
        console.print(f"[red]error:[/red] {exc}")
        raise SystemExit(2) from exc

    try:
        manifest = load_manifest(manifest_path)
    except ManifestError as exc:
        console.print(f"[red]error:[/red] manifest: {exc}")
        raise SystemExit(1) from exc

    detected_platform = platform.replace("-", "_") if platform else _detect_platform(project, console)
    if detected_platform is None:
        raise SystemExit(2)

    mode = InstallMode.DRY_RUN if dry_run else InstallMode.INSTALL

    total_written: list[pathlib.Path] = []
    total_skipped: list[pathlib.Path] = []
    total_conflicts: list[pathlib.Path] = []

    # Step 1 — artifact re-sync.
    if not skip_artifacts:
        for preset_record in manifest.installed_presets:
            preset_path = _locate_preset(framework_root, preset_record.name)
            if preset_path is None:
                console.print(
                    f"[yellow]warning:[/yellow] preset "
                    f"[cyan]{preset_record.name}[/cyan] not found in built-ins; "
                    "sync cannot refresh it. Install the matching extension or remove "
                    "the preset from the manifest."
                )
                continue
            try:
                report = run_install(
                    preset_path,
                    project,
                    dict(preset_record.variables),
                    platform=detected_platform,
                    mode=mode,
                    force=force,
                    framework_root=framework_root,
                )
            except InstallError as exc:
                console.print(f"[red]error:[/red] {exc}")
                raise SystemExit(1) from exc
            total_written.extend(report.written)
            total_skipped.extend(report.skipped)
            total_conflicts.extend(report.conflicts)

    # Step 2 — stack block refresh.
    stack_result: str | None = None
    stack_appended = False
    stack_path: pathlib.Path | None = None
    if not skip_stack:
        stack_path = project / _PLATFORM_AGENT_FILE[detected_platform]
        if not stack_path.is_file():
            console.print(
                f"[yellow]warning:[/yellow] {stack_path.name} not found at "
                f"{stack_path.parent}; skipping stack-block refresh."
            )
        else:
            report = introspect(project)
            generated_at = _utc_now_iso()
            block = render_stack_block(report, generated_at)
            original = stack_path.read_text(encoding="utf-8")
            new_text, stack_appended = apply_stack_block(original, block)
            if not dry_run and new_text != original:
                stack_path.write_text(new_text, encoding="utf-8")
            stack_result = "append" if stack_appended else "replace"

    _render_report(
        console,
        project,
        mode,
        total_written,
        total_skipped,
        total_conflicts,
        stack_path=stack_path,
        stack_result=stack_result,
        stack_appended=stack_appended,
    )
    if total_conflicts:
        raise SystemExit(1)


def _detect_platform(project: pathlib.Path, console: Console) -> str | None:
    found = [name for marker, name in _PLATFORM_DIRS.items() if (project / marker).is_dir()]
    if len(found) == 1:
        return found[0]
    if not found:
        console.print(
            "[red]error:[/red] cannot auto-detect platform — no "
            ".claude/.cursor/.codex/.opencode/.gemini directory under the project. "
            "Pass --platform explicitly."
        )
        return None
    console.print(
        f"[red]error:[/red] multiple platform directories present ({', '.join(sorted(found))}); "
        "pass --platform to disambiguate."
    )
    return None


def _locate_preset(framework_root: pathlib.Path, name: str) -> pathlib.Path | None:
    path = framework_root / "presets" / name
    return path if path.is_dir() else None


def _utc_now_iso() -> str:
    return (
        dt.datetime.now(dt.timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def _render_report(
    console: Console,
    project: pathlib.Path,
    mode: InstallMode,
    written: list[pathlib.Path],
    skipped: list[pathlib.Path],
    conflicts: list[pathlib.Path],
    *,
    stack_path: pathlib.Path | None,
    stack_result: str | None,
    stack_appended: bool,
) -> None:
    table = Table(title=f"aiadev sync ({mode.value})")
    table.add_column("Action", style="bold")
    table.add_column("Path")

    def _rel(path: pathlib.Path) -> str:
        try:
            return str(path.relative_to(project))
        except ValueError:
            return str(path)

    for path in written:
        table.add_row("[green]write[/green]", _rel(path))
    for path in skipped:
        table.add_row("[blue]skip[/blue]", _rel(path))
    for path in conflicts:
        table.add_row("[red]conflict[/red]", _rel(path))
    if stack_path is not None and stack_result is not None:
        tag = "stack-append" if stack_appended else "stack-replace"
        table.add_row(f"[magenta]{tag}[/magenta]", _rel(stack_path))

    if written or skipped or conflicts or stack_result:
        console.print(table)
    else:
        console.print("[yellow]nothing to do[/yellow]")

    if conflicts:
        console.print(
            "[red]refusing to overwrite the files above.[/red] "
            "Pass [cyan]--force[/cyan] to override."
        )
    if stack_appended:
        console.print(
            "[yellow]note:[/yellow] the auto-stack markers were missing from the "
            "agent file; a fresh block was appended at the end. Everything above "
            "it is unchanged."
        )
