"""``aiadev manifests`` — check or regenerate the plugin manifests.

Spec: ``specs/0016-agent-skills-interop/spec.md`` (Story 4, scenarios 1-2).

Three files in this repo are Claude Code / Cursor plugin manifests
derived from ``VERSION`` + ``pyproject.toml`` + ``presets/catalog.json``
by the pure functions in ``aiadev.manifests`` (T013):

* ``.claude-plugin/plugin.json``
* ``.claude-plugin/marketplace.json``
* ``.cursor-plugin/plugin.json``

This module is the thin CLI wiring around that derivation:

* ``--check`` (default): compare each committed file, byte-for-byte,
  against what the derivation would produce. Exits ``0`` when all three
  match; exits ``1`` and prints one line per divergent file naming the
  file and the two diverging values (spec scenario 1) when any differ,
  or when a manifest file is simply missing.
* ``--write``: regenerate all three files in place. Idempotent — a
  second ``--write`` (or a ``--check`` immediately after) reports no
  changes and exits ``0`` (spec scenario 2).

``--check`` is the default because it is read-only; ``--write`` must be
requested explicitly.
"""
from __future__ import annotations

import json
import pathlib

import click
from rich.console import Console

from ..manifests import (
    ManifestDerivationError,
    derive_cursor_plugin,
    derive_marketplace,
    derive_plugin_manifest,
    read_sources,
    render_json,
)

# Path (relative to the framework root), derive_* callable pairs. The
# derive callables share the same (version, pyproject[, catalog])
# signature shape; a small lambda normalizes that here so the loop
# below stays generic.
_MANIFEST_TARGETS: tuple[tuple[str, str], ...] = (
    (".claude-plugin/plugin.json", "plugin"),
    (".claude-plugin/marketplace.json", "marketplace"),
    (".cursor-plugin/plugin.json", "cursor"),
)


def _derive(kind: str, sources) -> dict:
    if kind == "plugin":
        return derive_plugin_manifest(sources.version, sources.pyproject)
    if kind == "marketplace":
        return derive_marketplace(sources.version, sources.pyproject, sources.catalog)
    if kind == "cursor":
        return derive_cursor_plugin(sources.version, sources.pyproject)
    raise AssertionError(f"unknown manifest kind {kind!r}")  # pragma: no cover — exhaustive


@click.command(
    "manifests",
    help=(
        "Verifica ou regrava os manifests de plugin "
        "(.claude-plugin/plugin.json, .claude-plugin/marketplace.json, "
        ".cursor-plugin/plugin.json) a partir de VERSION + pyproject.toml + "
        "presets/catalog.json. Default: --check (somente leitura)."
    ),
)
@click.option(
    "--check",
    "check",
    is_flag=True,
    default=False,
    help="Compara os manifests commitados com a derivação; exit 1 se divergirem (default).",
)
@click.option(
    "--write",
    "write",
    is_flag=True,
    default=False,
    help="Regrava os três manifests a partir da derivação. Idempotente.",
)
def manifests_command(check: bool, write: bool) -> None:
    """``aiadev manifests`` entry point."""
    if check and write:
        raise click.UsageError("--check and --write are mutually exclusive")

    console = Console()
    root = pathlib.Path.cwd()

    try:
        sources = read_sources(root)
    except FileNotFoundError as exc:
        console.print(f"[red]error:[/red] missing source file: {exc.filename or exc}")
        raise SystemExit(1) from exc
    except (json.JSONDecodeError, ValueError) as exc:
        # tomllib.load raises tomllib.TOMLDecodeError, a ValueError
        # subclass; json.loads raises JSONDecodeError, also a ValueError
        # subclass. Neither carries a filename, so name the two
        # candidate sources explicitly rather than leak a traceback.
        console.print(
            "[red]error:[/red] malformed source file (pyproject.toml or "
            f"presets/catalog.json): {exc}"
        )
        raise SystemExit(1) from exc

    if write:
        _run_write(console, root, sources)
        return

    _run_check(console, root, sources)


def _run_check(console: Console, root: pathlib.Path, sources) -> None:
    mismatches: list[str] = []

    for rel_path, kind in _MANIFEST_TARGETS:
        target = root / rel_path
        expected = render_json(_derive(kind, sources))

        if not target.is_file():
            mismatches.append(f"{rel_path}: missing (expected to be generated)")
            continue

        actual = target.read_text(encoding="utf-8")
        if actual != expected:
            mismatches.append(_describe_mismatch(rel_path, actual, expected, sources.version))

    if mismatches:
        console.print("[red]manifests out of sync:[/red]")
        for line in mismatches:
            console.print(f"  [red]FAIL[/red] {line}")
        console.print(
            f"[red]{len(mismatches)} manifest(s) diverge from the derivation; "
            "run `aiadev manifests --write` to regenerate.[/red]"
        )
        raise SystemExit(1)

    console.print("[green]all manifests match the derivation.[/green]")
    raise SystemExit(0)


def _describe_mismatch(rel_path: str, actual: str, expected: str, version: str) -> str:
    """Best-effort one-line description naming the diverging values.

    Tries to surface the two ``version`` values specifically (the
    scenario the spec calls out: ``VERSION`` vs. the manifest's
    ``version`` field) since that is overwhelmingly the common drift.
    Falls back to a generic content-mismatch message when the file
    doesn't parse as JSON or has no ``version`` key.
    """
    try:
        actual_obj = json.loads(actual)
    except json.JSONDecodeError:
        return f"{rel_path}: content differs from derivation (not valid JSON on disk)"

    actual_version = actual_obj.get("version") if isinstance(actual_obj, dict) else None
    if actual_version is None and isinstance(actual_obj, dict):
        # marketplace.json carries no top-level version; the core plugin
        # entry (plugins[0]) is where its version lives.
        plugins = actual_obj.get("plugins")
        if isinstance(plugins, list) and plugins and isinstance(plugins[0], dict):
            actual_version = plugins[0].get("version")
    if actual_version is not None and actual_version != version:
        return (
            f"{rel_path}: version mismatch — VERSION={version!r} but manifest has "
            f"version={actual_version!r}"
        )
    return f"{rel_path}: content differs from derivation (version matches; other fields drifted)"


def _run_write(console: Console, root: pathlib.Path, sources) -> None:
    changed: list[str] = []

    for rel_path, kind in _MANIFEST_TARGETS:
        target = root / rel_path
        expected = render_json(_derive(kind, sources))

        before = target.read_text(encoding="utf-8") if target.is_file() else None
        if before == expected:
            continue

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(expected, encoding="utf-8")
        changed.append(rel_path)

    if changed:
        console.print("[green]wrote:[/green]")
        for rel_path in changed:
            console.print(f"  {rel_path}")
    else:
        console.print("[green]no changes; manifests already match the derivation.[/green]")

    raise SystemExit(0)
