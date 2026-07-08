"""``aiadev sync`` — re-pull installed artifacts and refresh the stack block.

The sync flow has four steps:

0. **Migrate legacy agent files (T012, Story 3 sc2+sc3).** Projects that
   installed before T011 have a ``CLAUDE.md``/``GEMINI.md`` that carries
   real content — including hand-written prose outside the managed
   ``<!-- aiadev:... -->`` blocks — rather than the thin wrapper T011
   introduced. Before anything else runs, :func:`_migrate_legacy_agent_files`
   detects such files, backs up the original bytes to a ``.bak`` sibling,
   rewrites the file as the canonical wrapper, and extracts its manual
   content. This must happen before step 1, so the re-install below sees
   the new wrapper already in place instead of flagging it as a
   conflict. The extracted manual content itself is merged into
   ``AGENTS.md`` a little later, in step 1.5 (after step 1 has already
   converged ``AGENTS.md`` back to the bare preset render — see that
   step's comment for why it cannot happen any earlier), and re-merged on
   every subsequent sync so it survives step 1's churn indefinitely, the
   same way the auto-stack block already does.
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

   Spec 0016 Story 3 / ADR-5: the stack block always lands in the
   canonical ``AGENTS.md``, for every platform — including claude-code
   and gemini, whose ``CLAUDE.md``/``GEMINI.md`` are now thin wrappers
   that never carry generated content (see
   :mod:`aiadev.platforms.claude_code` / :mod:`aiadev.platforms.gemini`).
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
without writing. Step 0 (legacy agent file migration) also always runs;
under ``--dry-run`` it reports what would move without writing anything.
"""
from __future__ import annotations

import datetime as dt
import pathlib
import re
import tempfile
from dataclasses import dataclass

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
from ..platforms import claude_code, gemini
from ..project_introspect import apply_stack_block, introspect, render_stack_block

_PLATFORM_DIRS = {
    ".claude": "claude_code",
    ".cursor": "cursor",
    ".codex": "codex",
    ".opencode": "opencode",
    ".gemini": "gemini",
}

# Spec 0016 Story 3 / ADR-5: every platform's stack block lands in the
# canonical AGENTS.md. claude-code and gemini used to point here at their
# own CLAUDE.md/GEMINI.md; those are now thin wrappers that never carry
# generated content, so all five platforms converge on the same target.
_PLATFORM_AGENT_FILE = {
    "claude_code": "AGENTS.md",
    "cursor": "AGENTS.md",
    "codex": "AGENTS.md",
    "opencode": "AGENTS.md",
    "gemini": "AGENTS.md",
}

#: Reverse of _PLATFORM_DIRS: platform key -> its dot-directory name.
_PLATFORM_DIR_BY_NAME = {name: marker for marker, name in _PLATFORM_DIRS.items()}

# T012 (Story 3 sc2+sc3): the platforms whose agent file is a thin
# wrapper (per ADR-5) and therefore may need one-time legacy migration.
# cursor/codex/opencode have no wrapper concept — AGENTS.md is already
# their one physical file — so they are absent from this map.
_WRAPPER_PLATFORM_MODULES = {
    "claude_code": claude_code,
    "gemini": gemini,
}
_WRAPPER_FILENAMES = {
    "claude_code": "CLAUDE.md",
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

    # Step 0 — migrate legacy agent files (T012, Story 3 sc2+sc3). Must
    # run before step 1: it turns a pre-T011 CLAUDE.md/GEMINI.md into the
    # canonical thin wrapper *before* the re-install below walks the
    # manifest, so step 1 sees an already-consistent wrapper in place
    # instead of flagging it as a conflict. The wrapper's manual content
    # (if any) is extracted but *not yet* written into AGENTS.md — see
    # ``legacy_migration.manual_text`` below and
    # :func:`_apply_migrated_manual_content`.
    legacy_migration = _migrate_legacy_agent_files(
        project, manifest, detected_platform, dry_run=dry_run
    )
    if legacy_migration is not None and not dry_run:
        # _migrate_legacy_agent_files mutates `manifest` in place (the
        # wrapper's InstalledFile record now points at the new canonical
        # wrapper bytes); persist that before step 1 loads/saves its own
        # snapshot so the migration is not lost if step 1 is skipped
        # (--skip-artifacts) or the process exits before step 2's save.
        try:
            save_manifest(manifest, manifest_path, framework_root=framework_root)
        except ManifestError as exc:
            console.print(
                f"[yellow]warning:[/yellow] could not persist manifest after "
                f"agent file migration: {exc}"
            )

    # A previous sync may already have merged a ``migrated-legacy`` block
    # into AGENTS.md (see below). Step 1 is about to run and — like every
    # "recognized" agent_file — will reset AGENTS.md's body back to the
    # bare preset render, the same way it does to the auto-stack block's
    # placeholder content. Capture whatever migrated-legacy text is
    # *currently* on disk before that happens, so it can be re-applied
    # afterwards regardless of whether *this* sync's step 0 found a new
    # legacy wrapper to migrate. Without this, the block would only
    # survive the one sync where the migration actually fired and
    # silently vanish on every sync after that.
    agents_path_pre_step1 = project / "AGENTS.md"
    surviving_manual_text = ""
    if agents_path_pre_step1.is_file():
        surviving_manual_text = _extract_migrated_legacy_block(
            agents_path_pre_step1.read_text(encoding="utf-8")
        )

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

    # Step 1.5 — (re-)apply migrated legacy content to AGENTS.md, now
    # that step 1's re-install has already converged AGENTS.md to the
    # fresh preset render. Must run before step 2 so the stack block
    # refresh sees (and preserves, byte-for-byte outside its own
    # markers) the merged section rather than racing it.
    #
    # Combines two sources, freshest-first: a *new* legacy wrapper this
    # run's step 0 just migrated (``legacy_migration.manual_text``), or
    # — on every sync after that one, once there is no more legacy
    # wrapper left to find — whatever migrated-legacy block already
    # existed in AGENTS.md before step 1 ran this time
    # (``surviving_manual_text``). Exactly one of the two is ever
    # non-empty in practice (the wrapper is gone after the first
    # successful migration), but preferring the fresh extraction if both
    # were somehow present is the safer default.
    migrated_agent_files: list[pathlib.Path] = []
    if legacy_migration is not None:
        migrated_agent_files = [legacy_migration.wrapper_path]
    manual_text_to_apply = (
        legacy_migration.manual_text if legacy_migration is not None else surviving_manual_text
    )
    if manual_text_to_apply and not dry_run:
        _apply_migrated_manual_content(
            project,
            manifest,
            manifest_path,
            manual_text_to_apply,
            framework_root=framework_root,
            console=console,
        )

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
        migrated_agent_files=migrated_agent_files,
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


@dataclass(frozen=True)
class _LegacyAgentFileMigration:
    """Result of migrating one legacy wrapper file (see below).

    ``manual_text`` is the hand-written content extracted from the
    wrapper (managed blocks stripped, trimmed) — still needs to be
    merged into ``AGENTS.md``, which happens *after* step 1 (see
    :func:`_apply_migrated_manual_content`). Kept separate from the
    wrapper rewrite itself so callers can tell "a wrapper was migrated"
    (``wrapper_path``) from "there is manual text pending a merge"
    (``manual_text`` may be empty even when a wrapper was migrated, if
    the legacy file was 100% managed-block).
    """

    wrapper_path: pathlib.Path
    manual_text: str


def _migrate_legacy_agent_files(
    project: pathlib.Path,
    manifest,
    detected_platform: str,
    *,
    dry_run: bool,
) -> _LegacyAgentFileMigration | None:
    """One-time migration: detach a legacy wrapper file's manual content.

    Spec 0016 Story 3 scenario 2+3 (T012). T011 made ``AGENTS.md`` the
    canonical agent file and turned ``CLAUDE.md``/``GEMINI.md`` into thin
    (~3 line) wrappers. Projects that installed *before* T011 have a
    wrapper-named file that is not a wrapper at all — it carries real
    hand-written content (the team's own conventions) plus the managed
    ``<!-- aiadev:auto-stack -->`` block. Flipping such a project onto
    the new layout must not silently discard that manual content.

    Trigger condition (deliberately conservative — see below): the
    wrapper file exists, is **not already** the canonical thin wrapper,
    and either

    (a) the manifest tracks it under role ``agent_file`` with a sha256
        that matches what's on disk right now — i.e. aiadev itself wrote
        these exact bytes and nothing has touched the file since
        (sync-owned), or
    (b) it clearly carries the managed auto-stack markers, even if the
        manifest doesn't recognize the hash (e.g. the user hand-edited
        prose around a block aiadev previously regenerated).

    A file that matches *neither* condition is a plain hand-edit the
    manifest has no story for at all (never installed by aiadev, no
    managed block) — that is exactly the shape a hand-authored
    ``AGENTS.md`` has (Story 3 scenario 2's *other* half), and this
    function must not go anywhere near it; it is not "legacy", it is
    just data. Leaving it alone here means step 1's ordinary
    conflict-detection is free to flag it if it happens to collide with
    something aiadev wants to write, with the normal ``--force`` escape
    hatch — this function never overwrites unrecognized content without
    a backup.

    Regardless of which of (a)/(b) fired, a ``<name>.bak`` sibling with
    the pre-migration bytes is *always* written before the wrapper file
    is mutated, so a hand-edited-but-managed-block-bearing file (b)
    never loses data even though its hash wasn't in the manifest — that
    backup is the "escape hatch" the migration promises.

    This function only rewrites the wrapper file itself (backup + thin
    wrapper) and reconciles *its* manifest entry — it deliberately does
    **not** touch ``AGENTS.md``. See the long comment at the bottom of
    the function body for why: step 1's re-install engine has no notion
    of "partially recognized" content, so injecting the manual text into
    AGENTS.md before step 1 runs would just get clobbered by step 1's
    own fresh-preset-render write. The extracted text is threaded back
    to the caller (:class:`_LegacyAgentFileMigration`), which merges it
    into ``AGENTS.md`` from :func:`_apply_migrated_manual_content`
    *after* step 1 — the same pipeline position the auto-stack block
    already uses to survive step 1's churn.

    Returns ``None`` when nothing needs migrating (already a wrapper, or
    the trigger condition doesn't fire). Under ``--dry-run`` nothing is
    written — the returned migration (if any) exists purely so the
    caller can report what *would* move.
    """
    platform_module = _WRAPPER_PLATFORM_MODULES.get(detected_platform)
    wrapper_name = _WRAPPER_FILENAMES.get(detected_platform)
    if platform_module is None or wrapper_name is None:
        return None  # cursor/codex/opencode share AGENTS.md; no wrapper to migrate.

    wrapper_path = project / wrapper_name
    if not wrapper_path.is_file():
        return None

    canonical_wrapper_text = platform_module.render_wrapper("agent_file", "AGENTS.md")
    current_text = wrapper_path.read_text(encoding="utf-8")
    if canonical_wrapper_text is not None and current_text == canonical_wrapper_text:
        return None  # Already the thin wrapper — nothing to migrate.

    wrapper_rel = wrapper_name  # Project-root-relative; wrapper always lives at root.
    tracked_sha: str | None = None
    for preset_record in manifest.installed_presets:
        for entry in preset_record.files:
            if entry.path == wrapper_rel and entry.role == "agent_file":
                tracked_sha = entry.sha256
                break
        if tracked_sha is not None:
            break

    current_sha = compute_sha256(wrapper_path)
    sync_owned = tracked_sha is not None and tracked_sha == current_sha
    # Fence-aware (see _has_managed_block_marker): a marker string that
    # only appears inside a fenced code sample is documentation about
    # markers, not a managed block — it must not trigger a migration of
    # an otherwise-unrecognized hand-written file.
    carries_managed_block = _has_managed_block_marker(current_text)

    if not (sync_owned or carries_managed_block):
        return None

    if dry_run:
        return _LegacyAgentFileMigration(
            wrapper_path=wrapper_path, manual_text=_strip_managed_blocks(current_text).strip()
        )

    # Backup first — always, before any mutation, regardless of which
    # trigger fired. This is the escape hatch: even the (b) branch above
    # (unrecognized hash, but a managed block is present) never loses
    # bytes, because the pre-migration file is preserved here before
    # anything about it changes.
    backup_path = wrapper_path.with_name(wrapper_path.name + ".bak")
    backup_path.write_bytes(wrapper_path.read_bytes())

    manual_text = _strip_managed_blocks(current_text).strip()

    if canonical_wrapper_text is not None:
        wrapper_path.write_text(canonical_wrapper_text, encoding="utf-8")

    # Reconcile the manifest in place so step 1's re-install (which runs
    # right after this) recognizes the rewritten wrapper instead of
    # flagging it as a conflict — its tracked hash moves to the new
    # canonical-wrapper bytes, which are deterministic and byte-stable
    # (see render_wrapper's docstring), so this recognition never goes
    # stale on its own.
    #
    # AGENTS.md is deliberately NOT touched or re-hashed here. Step 1's
    # install engine always treats a *recognized* agent_file as
    # "converge to the fresh preset render" (see _write_one_target) — it
    # has no notion of partial/merged content. If we injected the
    # migrated manual text into AGENTS.md's body before step 1 ran, step
    # 1 would immediately overwrite it back to the bare preset template
    # the moment it saw a recognized hash, silently destroying the very
    # content this migration exists to save. So the manual text is
    # threaded back to the caller instead (see
    # ``_LegacyAgentFileMigration.manual_text``) and merged into
    # AGENTS.md *after* step 1 has run — same position in the pipeline
    # as the auto-stack block (step 2), which already knows how to
    # preserve everything outside its own markers and re-hash
    # afterwards.
    new_wrapper_sha = compute_sha256(wrapper_path)
    for preset_record in manifest.installed_presets:
        updated = []
        for entry in preset_record.files:
            if entry.path == wrapper_rel and entry.role == "agent_file":
                updated.append(
                    InstalledFile(path=entry.path, sha256=new_wrapper_sha, role=entry.role)
                )
            else:
                updated.append(entry)
        preset_record.files = updated

    return _LegacyAgentFileMigration(wrapper_path=wrapper_path, manual_text=manual_text)


# ---------------------------------------------------------------------------
# Fence-aware managed-block parsing (T012 hardening).
#
# The naive approach — a DOTALL regex over the whole file — silently
# corrupts real content: a legacy CLAUDE.md whose *manual* prose contains
# a fenced code sample illustrating the marker syntax (the marker strings
# appear verbatim in the framework's own docs) would have the fenced
# sample gutted during migration, and a non-greedy ``.*?`` extraction
# would truncate the migrated payload at the first pasted ``:end`` it
# saw. Everything below is therefore line-based and tracks Markdown
# fence state: marker lines only count as managed-block boundaries when
# they sit OUTSIDE a code fence. Stripping, extraction, and in-place
# replacement all share the same scanner so they cannot diverge.
# ---------------------------------------------------------------------------

#: A managed-block marker on its own line (the only shape aiadev ever
#: writes them in): ``<!-- aiadev:NAME:start -->`` / ``:end``.
_MARKER_LINE_RE = re.compile(r"^\s*<!--\s*aiadev:([\w-]+):(start|end)\s*-->\s*$")

#: A CommonMark code-fence delimiter line: up to 3 spaces of indent, then
#: 3+ backticks or 3+ tildes; group 1 is the run, group 2 the info string.
_FENCE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")


def _outside_fence_flags(lines: list[str]) -> list[bool]:
    """Per-line flags: True when the line lies outside any code fence.

    Implements the CommonMark closing rule: a fence only closes on a
    line whose delimiter uses the *same* character, is at least as long
    as the opener, and carries nothing else but trailing whitespace.
    Both the opening and closing delimiter lines themselves report
    False, as does everything between them, so a marker string inside
    (or on) a fence line can never be mistaken for a real boundary.

    Deliberately out of scope (CommonMark constructs this subset does
    NOT track): indented (4-space) code blocks, and fences nested inside
    blockquotes or list items whose legal indentation exceeds the 0-3
    spaces the fence regex accepts. A marker-looking string in those
    contexts would be treated as a real boundary — acceptable for the
    realistic input shape (aiadev-generated agent files plus hand-edited
    prose).
    """
    flags: list[bool] = []
    fence_char: str | None = None
    fence_len = 0
    for line in lines:
        match = _FENCE_RE.match(line)
        if fence_char is None:
            if match:
                delim = match.group(1)
                fence_char, fence_len = delim[0], len(delim)
                flags.append(False)
            else:
                flags.append(True)
        else:
            closes = (
                match is not None
                and match.group(1)[0] == fence_char
                and len(match.group(1)) >= fence_len
                and match.group(2).strip() == ""
            )
            if closes:
                fence_char = None
            flags.append(False)
    return flags


def _managed_block_line_ranges(
    lines: list[str], *, name: str | None = None
) -> list[tuple[int, int]]:
    """Inclusive ``(start_line, end_line)`` pairs of complete managed blocks.

    Only markers outside code fences count (see
    :func:`_outside_fence_flags`), and only *complete* start/end pairs
    with matching names are returned — a dangling start marker strips
    nothing rather than silently swallowing the rest of the file. Pass
    ``name`` to restrict the scan to one block family (e.g.
    ``"migrated-legacy"``); the default matches every aiadev block.
    """
    outside = _outside_fence_flags(lines)
    ranges: list[tuple[int, int]] = []
    open_name: str | None = None
    open_idx = 0
    for idx, line in enumerate(lines):
        if not outside[idx]:
            continue
        match = _MARKER_LINE_RE.match(line)
        if match is None:
            continue
        marker_name, kind = match.group(1), match.group(2)
        if name is not None and marker_name != name:
            continue
        if kind == "start" and open_name is None:
            open_name, open_idx = marker_name, idx
        elif kind == "end" and open_name == marker_name:
            ranges.append((open_idx, idx))
            open_name = None
    return ranges


def _has_managed_block_marker(text: str) -> bool:
    """True when any aiadev marker line exists outside a code fence.

    Used by :func:`_migrate_legacy_agent_files`'s trigger condition (b):
    a marker that only appears *inside* a fenced code sample is prose
    about markers, not evidence the file ever carried a managed block.
    """
    lines = text.splitlines()
    outside = _outside_fence_flags(lines)
    return any(
        outside[idx] and _MARKER_LINE_RE.match(line) is not None
        for idx, line in enumerate(lines)
    )


def _build_migrated_legacy_block(manual_text: str) -> str:
    """Render the ``<!-- aiadev:migrated-legacy -->`` block body.

    Deliberately generic (no wrapper filename baked in): this same block
    shape is re-applied on *every* sync, not just the one where a legacy
    wrapper was actually found (see :func:`_extract_migrated_legacy_block`
    and the "surviving_manual_text" plumbing in ``sync_command``), so the
    intro paragraph cannot depend on transient per-run state.
    """
    return (
        "<!-- aiadev:migrated-legacy:start -->\n"
        "## Migrated legacy agent file content\n\n"
        "> The section below was hand-written content found in this "
        "project's pre-AGENTS.md-canonical agent file (CLAUDE.md/GEMINI.md) "
        "before `aiadev sync` switched the project onto the canonical layout "
        "(T012). Moved here verbatim (managed blocks stripped) so nothing "
        "was lost in the flip.\n\n"
        f"{manual_text}\n"
        "<!-- aiadev:migrated-legacy:end -->"
    )


#: The fixed heading line _build_migrated_legacy_block emits right after
#: the start marker; _extract_migrated_legacy_block strips it (plus the
#: intro paragraph) back off so the payload round-trips byte-exactly.
_MIGRATED_HEADING = "## Migrated legacy agent file content"


def _extract_migrated_legacy_block(agents_text: str) -> str:
    """Return the manual text currently inside AGENTS.md's migrated-legacy block.

    Empty string when the block is absent. Used to recover the block's
    payload *before* step 1 resets AGENTS.md's body to the bare preset
    render, so :func:`_apply_migrated_manual_content` can re-apply it
    afterwards on every sync — not just the one where the migration
    itself fired (see the long comment above the call site in
    ``sync_command``).

    Fence-aware via :func:`_managed_block_line_ranges`: a pasted marker
    string inside a fenced code sample within the payload can neither
    terminate the block early (truncating the payload) nor start a
    phantom one. When the block's boilerplate prefix (heading + intro
    paragraph, exactly as :func:`_build_migrated_legacy_block` writes
    it) is present it is stripped so the payload round-trips
    byte-exactly; if a hand-edit disturbed that prefix, the whole inner
    content is returned instead — preservation-first, never "".
    """
    lines = agents_text.splitlines()
    ranges = _managed_block_line_ranges(lines, name="migrated-legacy")
    if not ranges:
        return ""
    start, end = ranges[0]
    inner = lines[start + 1 : end]
    if (
        len(inner) >= 4
        and inner[0] == _MIGRATED_HEADING
        and inner[1] == ""
        and inner[2].startswith(">")
        and inner[3] == ""
    ):
        inner = inner[4:]
    return "\n".join(inner)


def _apply_migrated_manual_content(
    project: pathlib.Path,
    manifest,
    manifest_path: pathlib.Path,
    manual_text: str,
    *,
    framework_root: pathlib.Path,
    console: Console,
) -> None:
    """(Re-)apply the migrated-legacy managed block to ``AGENTS.md``.

    Runs *after* step 1 (the re-install), for the same reason the
    auto-stack block's refresh does: step 1 always resets a *recognized*
    agent_file back to the bare preset render (see
    :func:`_migrate_legacy_agent_files`'s closing comment), so anything
    meant to survive across syncs has to be layered on top afterwards,
    the same way ``apply_stack_block`` layers the Detected-stack section
    on top of whatever step 1 just wrote. This function must therefore
    run on *every* sync where there is migrated text to preserve, not
    only the sync where a legacy wrapper was first discovered — the
    caller is responsible for recovering any already-merged text via
    :func:`_extract_migrated_legacy_block` before step 1 runs and
    passing it in here even when this run's step 0 found nothing new to
    migrate.

    The manual text lives in its own ``<!-- aiadev:migrated-legacy -->``
    managed block, replaced in place on repeat calls — mirroring
    :func:`aiadev.project_introspect.apply_stack_block`'s own
    idempotency contract.

    No-op (including no manifest write) when ``manual_text`` is empty —
    there is nothing to preserve (either no legacy file ever existed, or
    it was 100% managed-block content with nothing left after
    stripping).
    """
    if not manual_text:
        return

    agents_path = project / "AGENTS.md"
    agents_text = agents_path.read_text(encoding="utf-8") if agents_path.is_file() else ""

    block = _build_migrated_legacy_block(manual_text)

    # Locate any existing block with the same fence-aware scanner the
    # extraction path uses (they must never diverge): a pasted
    # ``:end``-looking string inside a fenced code sample in the payload
    # must not make the replacement cut the block short and leave its
    # tail behind as orphaned text.
    lines = agents_text.splitlines()
    ranges = _managed_block_line_ranges(lines, name="migrated-legacy")
    if ranges:
        start, end = ranges[0]
        new_lines = lines[:start] + block.splitlines() + lines[end + 1 :]
        new_agents_text = "\n".join(new_lines)
        if agents_text.endswith("\n") and not new_agents_text.endswith("\n"):
            new_agents_text += "\n"
    elif agents_text:
        new_agents_text = agents_text.rstrip("\n") + "\n\n" + block + "\n"
    else:
        new_agents_text = block + "\n"

    if new_agents_text == agents_text:
        return

    agents_path.write_text(new_agents_text, encoding="utf-8")

    # Reconcile AGENTS.md's manifest hash the same way step 2 already
    # does for the auto-stack block: reload from disk first, since step
    # 1's run_install saved its own fresh records and this function runs
    # after it.
    try:
        current_manifest = load_manifest(manifest_path)
        _resync_agent_file_hash(current_manifest, project, agents_path)
        save_manifest(current_manifest, manifest_path, framework_root=framework_root)
    except ManifestError as exc:
        console.print(
            f"[yellow]warning:[/yellow] could not refresh manifest hash for "
            f"AGENTS.md after merging migrated content: {exc}"
        )


def _strip_managed_blocks(text: str) -> str:
    """Remove every ``<!-- aiadev:NAME:start -->...<!-- aiadev:NAME:end -->`` block.

    Mirrors the fence grammar :mod:`aiadev.project_introspect` uses for
    the auto-stack block (``<!-- aiadev:auto-stack:start -->`` /
    ``:end``) but generalizes the marker name so any future managed
    block (not just auto-stack) is stripped the same way when computing
    "what's left is manual content". What remains, once every managed
    block is removed, is exactly the hand-written material T012 must
    preserve.

    Line-based and fence-aware (see :func:`_managed_block_line_ranges`):
    marker strings inside a fenced code sample — e.g. documentation that
    *shows* the marker syntax — are prose, not boundaries, so the fenced
    sample survives byte-intact. Only complete, name-matched start/end
    pairs are removed; a dangling start marker strips nothing rather
    than swallowing the rest of the file.
    """
    lines = text.splitlines()
    drop: set[int] = set()
    for start, end in _managed_block_line_ranges(lines):
        drop.update(range(start, end + 1))
    return "\n".join(line for idx, line in enumerate(lines) if idx not in drop)


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
    migrated_agent_files: list[pathlib.Path] | None = None,
) -> None:
    migrated_agent_files = migrated_agent_files or []
    table = Table(title=f"aiadev sync ({mode.value})")
    table.add_column("Action", style="bold")
    table.add_column("Path")

    def _rel(path: pathlib.Path) -> str:
        try:
            return str(path.relative_to(project))
        except ValueError:
            return str(path)

    for path in migrated_agent_files:
        table.add_row("[cyan]migrate-agent-file[/cyan]", _rel(path))
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

    if written or skipped or conflicts or stack_result or migrated or migrated_agent_files:
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
    if migrated_agent_files:
        names = ", ".join(_rel(p) for p in migrated_agent_files)
        console.print(
            f"[cyan]migrated legacy agent file content into AGENTS.md ({names}); "
            "a `.bak` backup of the original was written next to each.[/cyan]"
        )
    if migrated:
        console.print(
            f"[cyan]migrated {len(migrated)} skill frontmatter file"
            f"{'s' if len(migrated) != 1 else ''} to the new metadata.aiadev shape.[/cyan]"
        )
