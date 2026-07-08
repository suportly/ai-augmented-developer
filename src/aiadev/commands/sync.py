"""``aiadev sync`` — re-pull installed artifacts and refresh the stack block.

The sync flow has three steps:

1. **Re-install every preset recorded in .aiadev/installed.yaml.** Uses
   the same engine as ``aiadev install`` with the variables captured at
   install time. Framework-generic artifacts (commands/agents/skills)
   come along for the ride, so projects that installed under an older
   ``aiadev`` pick up any new pipeline files the framework grew since.
2. **Regenerate the ``<!-- aiadev:auto-stack -->`` block in the agent
   file.** Reads well-known config files (package.json, pyproject.toml,
   docker-compose.yml, Makefile, .github/workflows/) via
   :func:`aiadev.project_introspect.introspect` and writes a stack
   summary. Content outside the markers is preserved byte-for-byte. The
   manifest's recorded hash for the agent file is refreshed to match so
   a subsequent sync does not mistake the regenerated stack block for a
   hand-edit conflict.
3. **Auto-migrate installed skills' frontmatter.** Sweeps every
   ``<platform-dir>/skills/*/SKILL.md`` under the project and rewrites
   any file still using the old proprietary top-level pipeline fields
   into the new ``metadata.aiadev`` shape (spec 0016, Story 1 sc4 +
   cl-5; see :mod:`aiadev.frontmatter_migrate`, ADR-4). Step 1 already
   overwrites any installed skill that matches a framework/preset
   artifact byte-for-byte with a fresh (already-conformant) copy; this
   step covers the skills step 1 does *not* touch — those installed
   under an older ``aiadev`` version or hand-added by the consumer.
   Malformed files are reported as a warning and left untouched; they
   never abort the sync.

Flags control granularity: ``--skip-artifacts`` runs only steps 2-3,
``--skip-stack`` skips step 2 only. ``--dry-run`` and ``--force`` mirror
the flags on ``aiadev install``. Step 3 always runs (even under
``--skip-artifacts``) since it targets files step 1 would not have
touched anyway; under ``--dry-run`` it reports what would be migrated
without writing.
"""
from __future__ import annotations

import datetime as dt
import pathlib
import tempfile

import click
from rich.console import Console
from rich.table import Table

from ..frontmatter_migrate import FrontmatterError, migrate_skill_file
from ..install_engine import InstallError, InstallMode, install as run_install
from ..install_manifest import (
    InstalledFile,
    ManifestError,
    compute_sha256,
    load as load_manifest,
    save as save_manifest,
)
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

#: Reverse of _PLATFORM_DIRS: platform key -> its dot-directory name.
_PLATFORM_DIR_BY_NAME = {name: marker for marker, name in _PLATFORM_DIRS.items()}


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
    help="Skip step 1 (artifact re-sync); stack-block refresh and frontmatter migration still run.",
)
@click.option(
    "--skip-stack",
    is_flag=True,
    help="Skip step 2 (stack-block refresh); artifact re-sync and frontmatter migration still run.",
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
                # The agent file's on-disk hash just moved (new
                # generated_at + any stack-content changes); refresh the
                # manifest's recorded hash for it so the *next* sync's
                # step-1 re-install does not mistake this self-inflicted
                # rewrite for a hand-edit conflict. Reload the manifest
                # from disk first: step 1's run_install saved its own
                # fresh records (new/updated artifacts), and saving the
                # snapshot loaded at the top of this function would
                # silently wipe them.
                try:
                    current_manifest = load_manifest(manifest_path)
                    _resync_agent_file_hash(current_manifest, project, stack_path)
                    save_manifest(
                        current_manifest, manifest_path, framework_root=framework_root
                    )
                except ManifestError as exc:
                    console.print(
                        f"[yellow]warning:[/yellow] could not refresh manifest hash "
                        f"for {stack_path.name}: {exc}"
                    )
            stack_result = "append" if stack_appended else "replace"

    # Step 3 — auto-migrate installed skills' frontmatter (spec 0016,
    # Story 1 sc4 + cl-5). Runs regardless of --skip-artifacts: it only
    # touches skills step 1 did not already overwrite with a fresh,
    # conformant copy.
    migrated, migration_warnings = _migrate_installed_skills(
        project, detected_platform, dry_run=dry_run
    )
    for warning in migration_warnings:
        console.print(f"[yellow]warning:[/yellow] {warning}")

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
        migrated=migrated,
    )
    if total_conflicts:
        raise SystemExit(1)


def _resync_agent_file_hash(
    manifest, project: pathlib.Path, stack_path: pathlib.Path
) -> None:
    """Update the manifest's recorded hash for ``stack_path`` in place.

    ``stack_path`` is always tracked with role ``agent_file`` by whichever
    preset installed it. Re-hashing after the stack-block rewrite keeps
    the manifest truthful without needing any change to the install
    engine itself — sync owns this file's post-processing, so sync owns
    reconciling the manifest afterwards.
    """
    rel_path = str(stack_path.relative_to(project)).replace("\\", "/")
    new_sha = compute_sha256(stack_path)
    for preset_record in manifest.installed_presets:
        for idx, entry in enumerate(preset_record.files):
            if entry.path == rel_path and entry.role == "agent_file":
                preset_record.files[idx] = InstalledFile(
                    path=entry.path, sha256=new_sha, role=entry.role
                )


def _migrate_installed_skills(
    project: pathlib.Path, detected_platform: str, *, dry_run: bool
) -> tuple[list[pathlib.Path], list[str]]:
    """Sweep the detected platform's skills dir, migrating old-format SKILL.md files.

    Returns ``(migrated_paths, warnings)``. Under ``--dry-run`` nothing is
    written to the real file: :func:`migrate_skill_file` runs against a
    scratch copy in a temp dir so the report can still say what would
    change, without touching the project. A malformed SKILL.md is
    reported as a warning and left untouched — never raised, so one
    broken skill cannot brick the whole sync.
    """
    platform_dir_name = _PLATFORM_DIR_BY_NAME.get(detected_platform)
    if platform_dir_name is None:
        return [], []

    skills_root = project / platform_dir_name / "skills"
    if not skills_root.is_dir():
        return [], []

    migrated: list[pathlib.Path] = []
    warnings: list[str] = []
    for skill_file in sorted(skills_root.glob("*/SKILL.md")):
        try:
            if dry_run:
                changed = _would_migrate(skill_file)
            else:
                changed = migrate_skill_file(skill_file)
        except FrontmatterError as exc:
            warnings.append(str(exc))
            continue
        if changed:
            migrated.append(skill_file)
    return migrated, warnings


def _would_migrate(skill_file: pathlib.Path) -> bool:
    """Dry-run counterpart of :func:`migrate_skill_file`: no writes to ``skill_file``.

    Copies the file into a throwaway temp dir and migrates the copy, so
    the exact same parsing/validation path runs (including
    :class:`FrontmatterError` on malformed input) without mutating the
    original.
    """
    with tempfile.TemporaryDirectory() as scratch:
        scratch_file = pathlib.Path(scratch) / "SKILL.md"
        scratch_file.write_bytes(skill_file.read_bytes())
        return migrate_skill_file(scratch_file)


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
    migrated: list[pathlib.Path],
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
    for path in migrated:
        table.add_row("[cyan]migrate[/cyan]", _rel(path))

    if written or skipped or conflicts or stack_result or migrated:
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
    if migrated:
        console.print(
            f"[cyan]migrated {len(migrated)} skill frontmatter file"
            f"{'s' if len(migrated) != 1 else ''} to the new metadata.aiadev shape.[/cyan]"
        )
