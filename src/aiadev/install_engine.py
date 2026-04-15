"""Preset install / uninstall orchestration.

Sits on top of :mod:`placeholders` (substitution), :mod:`install_manifest`
(persistence), and the per-platform handlers in :mod:`aiadev.platforms`.

Responsibilities in one paragraph: load the preset's ``preset.yaml``,
walk every artifact the platform handler declares, substitute the user's
variables, decide (for each artifact) whether to write, skip, or flag a
conflict, update ``.aiadev/installed.yaml``, and return a structured
:class:`InstallReport`. Uninstall walks the manifest in reverse, removing
only files whose sha256 still matches what the installer recorded.

The engine is pure-enough for tests: every side effect is a file write
inside ``project_root``, and the callers inject ``now=`` for
deterministic timestamps.
"""
from __future__ import annotations

import datetime as dt
import hashlib
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

import yaml

from . import __version__
from .framework_artifacts import iter_framework_artifacts
from .install_manifest import (
    InstalledFile,
    InstalledPreset,
    Manifest,
    compute_sha256,
    load as load_manifest,
    save as save_manifest,
)
from .placeholders import find_unresolved, substitute
from .platforms import claude_code, codex, cursor, gemini, opencode

# Stable order commands/agents/skills install in. Preserves the legacy
# agent_file→constitution→skill order for manifests that already exist,
# and slots the new command/agent roles between constitution and skill.
_ROLE_PRIORITY = {
    "agent_file": 0,
    "constitution": 1,
    "rule": 2,
    "command": 3,
    "agent": 4,
    "skill": 5,
}

MANIFEST_REL_PATH = Path(".aiadev") / "installed.yaml"

_PLATFORMS = {
    "claude_code": claude_code,
    "cursor": cursor,
    "codex": codex,
    "opencode": opencode,
    "gemini": gemini,
}


class InstallMode(str, Enum):
    INSTALL = "install"
    DRY_RUN = "dry_run"
    UNINSTALL = "uninstall"


class InstallError(RuntimeError):
    """Raised when an install cannot proceed (missing preset, unresolved placeholders, …)."""


@dataclass
class InstallReport:
    """Structured outcome of one install / dry-run / uninstall call."""

    preset_name: str
    mode: InstallMode
    written: list[Path] = field(default_factory=list)
    skipped: list[Path] = field(default_factory=list)  # present, identical
    conflicts: list[Path] = field(default_factory=list)  # present, differs
    removed: list[Path] = field(default_factory=list)
    unresolved: list[str] = field(default_factory=list)
    # Artifacts the handler reports as not installable under the current
    # scope (user scope refuses agent_file and constitution). One entry
    # per skipped artifact, human-readable for CLI output.
    skipped_unsupported: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.conflicts and not self.unresolved


def _utc_now_iso() -> str:
    return (
        dt.datetime.now(dt.timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def _load_preset_yaml(preset_path: Path) -> dict:
    manifest = preset_path / "preset.yaml"
    if not manifest.is_file():
        raise InstallError(f"preset.yaml not found at {manifest}")
    data = yaml.safe_load(manifest.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise InstallError(f"{manifest}: expected a mapping at the root")
    return data


def _manifest_path(install_root: Path) -> Path:
    return install_root / MANIFEST_REL_PATH


def _load_or_create_manifest(install_root: Path) -> Manifest:
    path = _manifest_path(install_root)
    if path.is_file():
        return load_manifest(path)
    return Manifest(aiadev_version=__version__)


def _to_rel(target: Path, install_root: Path) -> str:
    return str(target.relative_to(install_root)).replace("\\", "/")


def _resolve_install_root(scope: str, project_root: Path) -> Path:
    """Return the root under which artifacts land for the given scope.

    Project scope -> the project directory (current behaviour).
    User scope    -> the user's home directory.
    """
    if scope == "user":
        return Path.home()
    if scope == "project":
        return project_root
    raise InstallError(f"unknown scope: {scope!r} (expected 'project' or 'user')")


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def install(
    preset_path: Path,
    project_root: Path,
    variables: dict[str, str],
    *,
    platform: str = "claude_code",
    mode: InstallMode = InstallMode.INSTALL,
    force: bool = False,
    allow_unresolved: bool = False,
    scope: str = "project",
    framework_root: Path | None = None,
    now: str | None = None,
) -> InstallReport:
    """Install or re-install a preset into ``project_root`` (or ``$HOME``).

    ``scope='project'`` (default) writes into ``project_root``. ``scope='user'``
    writes into the current user's home directory, covering only the
    roles each platform reports via ``user_scope_supported``; agent files
    and constitutions are skipped and noted in
    :attr:`InstallReport.skipped_unsupported`.

    ``mode=InstallMode.DRY_RUN`` produces the same report without writing.
    ``mode=InstallMode.UNINSTALL`` removes the preset's files using the
    scope-appropriate manifest.

    ``framework_root`` points at the ``aiadev`` checkout whose top-level
    ``commands/``, ``agents/``, and ``skills/`` directories are always
    installed alongside the preset's own artifacts. When ``None`` (the
    default), only preset artifacts are installed — this keeps the
    narrow-scope tests from picking up the real framework's pipeline.
    The CLI always passes a concrete ``framework_root``.
    """
    platform_module = _PLATFORMS.get(platform)
    if platform_module is None:
        raise InstallError(f"unknown platform: {platform!r}")

    install_root = _resolve_install_root(scope, project_root)

    preset_data = _load_preset_yaml(preset_path)
    preset_name = preset_data.get("name", preset_path.name)
    preset_version = str(preset_data.get("version", "0.0.0"))

    manifest = _load_or_create_manifest(install_root)
    existing = manifest.find_preset(preset_name)

    if mode is InstallMode.UNINSTALL:
        return _perform_uninstall(install_root, manifest, existing, preset_name, force)

    report = InstallReport(preset_name=preset_name, mode=mode)
    previous_by_path = {f.path: f for f in existing.files} if existing else {}
    recorded_files: list[InstalledFile] = []

    artifacts = _collect_artifacts(framework_root, platform_module, preset_path)

    for role, name, source_path, verbatim in artifacts:
        # Under user scope, skip artifacts the handler says are not
        # installable there (agent_file, constitution). They stay
        # project-local.
        if scope == "user" and not platform_module.user_scope_supported(role):
            report.skipped_unsupported.append(
                f"role={role!r} skipped: not installable under --scope user"
            )
            continue

        source_text = source_path.read_text(encoding="utf-8")
        if verbatim:
            # Framework-generic artifacts (commands, agents, skills
            # shipped by aiadev itself) are copied as-is: their
            # ``{{UPPER_SNAKE}}``-looking tokens are runtime markers the
            # AI fills in — not install-time variables.
            rendered = source_text
        else:
            rendered = substitute(source_text, variables)
            unresolved = find_unresolved(rendered)
            if unresolved:
                report.unresolved.extend(unresolved)
                if not allow_unresolved:
                    continue

        # Platforms may transform rendered content per-role (Gemini
        # converts markdown commands to TOML, for example). The hook is
        # optional; default is a pass-through.
        render_hook = getattr(platform_module, "render_target", None)
        if render_hook is not None:
            rendered = render_hook(role, name, rendered)

        target = platform_module.resolve_target(role, name, install_root, scope=scope)
        target_rel = _to_rel(target, install_root)
        rendered_sha = _sha256_text(rendered)

        if target.is_file():
            current_sha = compute_sha256(target)
            prev = previous_by_path.get(target_rel)
            recognized = prev is not None and prev.sha256 == current_sha
            if recognized and rendered_sha == current_sha:
                # Identical; nothing to do, but keep the record.
                report.skipped.append(target)
                recorded_files.append(InstalledFile(target_rel, rendered_sha, role))
                continue
            if recognized or force:
                if mode is InstallMode.INSTALL:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(rendered, encoding="utf-8")
                report.written.append(target)
                recorded_files.append(InstalledFile(target_rel, rendered_sha, role))
                continue
            # Target is present, not tracked (or edited) → conflict.
            report.conflicts.append(target)
            if prev is not None:
                recorded_files.append(prev)
            continue

        # Fresh file — write and record.
        if mode is InstallMode.INSTALL:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(rendered, encoding="utf-8")
        report.written.append(target)
        recorded_files.append(InstalledFile(target_rel, rendered_sha, role))

    if report.unresolved and not allow_unresolved:
        raise InstallError(
            "unresolved placeholders after substitution: "
            f"{sorted(set(report.unresolved))}"
        )

    if mode is InstallMode.INSTALL:
        merged_vars: dict[str, str] = {}
        if existing is not None:
            merged_vars.update(existing.variables)
        merged_vars.update(variables)
        record = InstalledPreset(
            name=preset_name,
            version=preset_version,
            installed_at=now or _utc_now_iso(),
            variables=merged_vars,
            files=recorded_files,
        )
        manifest.upsert(record)
        save_manifest(manifest, _manifest_path(install_root))

    return report


def _collect_artifacts(
    framework_root: Path | None,
    platform_module,
    preset_path: Path,
) -> list[tuple[str, str, Path, bool]]:
    """Merge framework-generic and preset artifacts. Preset wins on collision.

    The dedupe key is ``(role, name)`` — a preset that ships a skill
    with the same name as a framework-generic skill overrides it, never
    duplicates it. Order is stable: legacy roles first (agent_file →
    constitution), then command → agent → skill; within each role,
    alphabetical.

    The trailing ``verbatim`` flag tells the engine whether to run
    variable substitution. Framework-generic artifacts are copied
    verbatim because their ``{{UPPER_SNAKE}}`` tokens are runtime
    markers, not install variables. Preset artifacts run through
    substitute()/find_unresolved() as before.
    """
    merged: dict[tuple[str, str], tuple[str, str, Path, bool]] = {}
    if framework_root is not None:
        for role, name, source_path in iter_framework_artifacts(framework_root):
            merged[(role, name)] = (role, name, source_path, True)
    for role, name, source_path in platform_module.iter_preset_artifacts(preset_path):
        merged[(role, name)] = (role, name, source_path, False)
    return sorted(
        merged.values(),
        key=lambda t: (_ROLE_PRIORITY.get(t[0], 99), t[1]),
    )


def _perform_uninstall(
    install_root: Path,
    manifest: Manifest,
    existing: InstalledPreset | None,
    preset_name: str,
    force: bool,
) -> InstallReport:
    report = InstallReport(preset_name=preset_name, mode=InstallMode.UNINSTALL)
    if existing is None:
        return report

    for entry in list(existing.files):
        target = install_root / entry.path
        if not target.is_file():
            continue
        current_sha = compute_sha256(target)
        if current_sha != entry.sha256 and not force:
            report.conflicts.append(target)
            continue
        target.unlink()
        report.removed.append(target)

    # Also clean up now-empty artifact directories we created, walking
    # up each file's path toward the project root so ancestor dirs like
    # `.cursor/commands/` and `.cursor/` disappear when empty.
    if report.conflicts:
        return report

    for entry in existing.files:
        if entry.role not in ("skill", "command", "agent", "rule"):
            continue
        parent = (install_root / entry.path).parent
        while parent.is_dir() and parent != install_root:
            try:
                parent.rmdir()
            except OSError:
                break  # directory not empty; stop climbing.
            parent = parent.parent

    manifest.remove(preset_name)
    manifest_path = _manifest_path(install_root)
    if manifest.installed_presets:
        save_manifest(manifest, manifest_path)
    elif manifest_path.is_file():
        manifest_path.unlink()
        # Clean up the .aiadev directory if it is now empty.
        parent = manifest_path.parent
        if parent.is_dir() and not any(parent.iterdir()):
            parent.rmdir()

    return report
