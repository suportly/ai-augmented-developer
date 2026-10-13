#!/usr/bin/env python3
"""Instruction budget: the always-loaded cost of each preset (spec 0030).

Installs each preset into a temporary project **through the CLI route**
(``aiadev install``, which applies the ``preset.yaml`` variable defaults;
the engine's ``install()`` does not) and measures what the Claude Code
platform loads into context without being invoked:

- ``agent_file`` — ``AGENTS.md``;
- ``wrapper``    — the two-line ``CLAUDE.md`` that points at it;
- ``rules``      — ``.claude/rules/**/*.md`` WITHOUT a ``paths:`` frontmatter
  key (a rule with ``paths:`` is conditional and loads only on a match);
- ``skills`` / ``commands`` / ``agents`` — only the ``name`` and
  ``description`` frontmatter of each file; the body loads on invocation.
  A command has no ``name`` key: the platform exposes it as
  ``<namespace>:<stem>`` (``.claude/commands/aia/plan.md`` -> ``aia:plan``),
  so that path-derived name is counted unless the frontmatter sets one.

The same report also carries the **pipeline path**: the framework files the
default route reads from ``specify`` to ``finish``, as listed per stage in
``docs/pipeline-path.yaml``. Unlike the always-loaded set it is not measured
from an install but from that versioned list, and it is strict: a cited file
that does not exist fails the measurement instead of counting as zero.

"Tokens" are estimated as ``ceil(characters / 4)`` per file, with no
tokenizer: deterministic, dependency-free, and good enough to track a
budget. The figures are a relative gauge, not billing numbers.

Usage:
    scripts/instruction_budget.py                # lean and django-drf-react
    scripts/instruction_budget.py PRESET ...     # specific presets

The pipeline path is always printed after the presets.

Exit codes:
    0 — every preset and the pipeline path measured
    1 — a preset is unknown or its install/measurement failed, or the
        pipeline path file is malformed or cites a file that does not exist
    2 — missing runtime dependencies (pyyaml, aiadev and its click/rich)
"""
from __future__ import annotations

import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

#: Presets measured when none is named on the command line.
DEFAULT_PRESETS: tuple[str, ...] = ("lean", "django-drf-react")

#: Value for the ``PROJECT_NAME`` variable every preset requires. Fixed so
#: the measurement is deterministic across runs and machines.
PROJECT_NAME = "Project"

COMPONENTS: tuple[str, ...] = (
    "agent_file",
    "wrapper",
    "rules",
    "skills",
    "commands",
    "agents",
)

CHARS_PER_TOKEN = 4

#: The versioned list of files read per pipeline stage, under the framework root.
PIPELINE_PATH_FILE = Path("docs") / "pipeline-path.yaml"


def estimate_tokens(text: str) -> int:
    """``ceil(len(text) / 4)`` in integer arithmetic."""
    return (len(text) + CHARS_PER_TOKEN - 1) // CHARS_PER_TOKEN


_KEY_LINE = re.compile(r"^([A-Za-z_][\w-]*):[ \t]*(.*)$")


def _lenient_keys(block: str) -> dict[str, str]:
    """Top-level ``key: value`` pairs read line by line, no YAML involved.

    Claude Code reads frontmatter that strict YAML rejects (an unquoted
    ``: `` inside a description is the common case), so the measurement
    must too. Indented and list lines extend the previous key's value.
    """
    keys: dict[str, str] = {}
    last: str | None = None
    for line in block.splitlines():
        match = _KEY_LINE.match(line)
        if match:
            last = match.group(1)
            keys[last] = match.group(2).strip()
        elif last and line.strip():
            keys[last] = f"{keys[last]} {line.strip()}".strip()
    return keys


def _frontmatter(text: str) -> dict | None:
    """Top-level frontmatter keys of *text*, or None when it has none."""
    import yaml

    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for end, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            break
    else:
        return None  # unterminated block: not frontmatter
    block = "\n".join(lines[1:end])
    try:
        parsed = yaml.safe_load(block)
    except yaml.YAMLError:
        return _lenient_keys(block)
    return parsed if isinstance(parsed, dict) else {}


def _file_tokens(path: Path) -> int:
    if not path.is_file():
        return 0
    return estimate_tokens(path.read_text(encoding="utf-8"))


def _listing_tokens(path: Path, default_name: str | None = None) -> int:
    """Tokens of the ``name`` + ``description`` lines of a skill, command or
    agent: all of it the platform loads before the file is invoked. A file
    without frontmatter contributes nothing.

    *default_name* stands in for a missing ``name`` key (commands are named
    by their path); a ``name`` in the frontmatter always wins.

    Counted as normalised ``key: value`` lines (not the raw YAML), so the
    figure does not move when a description is re-wrapped or re-quoted.
    """
    frontmatter = _frontmatter(path.read_text(encoding="utf-8"))
    if frontmatter is None:
        return 0
    if default_name is not None:
        frontmatter = {"name": default_name, **frontmatter}
    lines = [
        f"{key}: {str(frontmatter[key]).strip()}"
        for key in ("name", "description")
        if key in frontmatter
    ]
    return estimate_tokens("\n".join(lines))


def _rule_tokens(path: Path) -> int:
    """A whole rule file, or 0 when it is conditional (non-empty ``paths:``).

    An empty ``paths:`` value is no condition at all, so the rule counts.
    """
    text = path.read_text(encoding="utf-8")
    if (_frontmatter(text) or {}).get("paths"):
        return 0
    return estimate_tokens(text)


def measure_always_loaded(project_root: Path) -> dict[str, int]:
    """Tokens the platform loads at session start, per component, plus
    ``total``. Pure: reads an already installed project, installs nothing."""
    root = Path(project_root)
    claude = root / ".claude"
    commands = claude / "commands"
    counts = {
        "agent_file": _file_tokens(root / "AGENTS.md"),
        "wrapper": _file_tokens(root / "CLAUDE.md"),
        "rules": sum(_rule_tokens(p) for p in sorted((claude / "rules").rglob("*.md"))),
        "skills": sum(
            _listing_tokens(p) for p in sorted((claude / "skills").glob("*/SKILL.md"))
        ),
        "commands": sum(
            _listing_tokens(p, ":".join(p.relative_to(commands).with_suffix("").parts))
            for p in sorted(commands.rglob("*.md"))
        ),
        "agents": sum(_listing_tokens(p) for p in sorted((claude / "agents").glob("*.md"))),
    }
    counts["total"] = sum(counts.values())
    return counts


class PipelinePathError(ValueError):
    """The pipeline path file is missing or malformed, or cites a file that
    does not exist. A ``ValueError``, so ``main`` reports it like any failed
    measurement."""


def _strict_file_tokens(root: Path, stage: str, file: str) -> int:
    """Tokens of ``root / file``. Strict, unlike ``_file_tokens``: an absent
    file is an error naming it, since a path entry that vanished would
    otherwise shrink the budget without anyone noticing."""
    path = root / file
    if not path.is_file():
        raise PipelinePathError(
            f"stage '{stage}' cites {file}, which does not exist or is not a file"
        )
    return estimate_tokens(path.read_text(encoding="utf-8"))


def _read_stages(path_file: Path) -> list[tuple[str, list[str]]]:
    """``(stage name, cited files)`` in file order, validated.

    Rejects what would make the path silently measure less, or count a file
    twice: an absent or invalid file, a missing or empty ``stages`` or
    ``files``, a repeated stage name, a file cited twice in one stage (however
    spelled: ``./a.md`` is ``a.md``), and a cited path that is absolute or
    climbs out of the framework root. A file cited by two *different* stages
    is legitimate (see ``measure_pipeline_path``). Cited files come back in
    their normalised POSIX spelling.
    """
    import yaml

    if not path_file.is_file():
        raise PipelinePathError(f"{path_file}: file not found")
    try:
        data = yaml.safe_load(path_file.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        detail = " ".join(str(exc).split())
        raise PipelinePathError(f"{path_file}: invalid YAML: {detail}") from exc
    where = path_file.name
    stages = data.get("stages") if isinstance(data, dict) else None
    if not isinstance(stages, list) or not stages:
        raise PipelinePathError(f"{where}: expected a non-empty 'stages' list")

    parsed: list[tuple[str, list[str]]] = []
    for number, entry in enumerate(stages, start=1):
        entry = entry if isinstance(entry, dict) else {}
        name, files = entry.get("name"), entry.get("files")
        if (
            not isinstance(name, str)
            or not isinstance(files, list)
            or not files
            or not all(isinstance(file, str) for file in files)
        ):
            raise PipelinePathError(
                f"{where}: stage #{number} needs a 'name' string and a "
                "non-empty 'files' list of strings"
            )
        if any(name == seen for seen, _ in parsed):
            raise PipelinePathError(f"{where}: stage '{name}' is listed more than once")
        cited: list[str] = []
        for file in files:
            if Path(file).is_absolute() or ".." in Path(file).parts:
                raise PipelinePathError(
                    f"{where}: stage '{name}': {file} must be relative to the "
                    "framework root and stay under it"
                )
            normalised = Path(file).as_posix()
            if normalised in cited:
                raise PipelinePathError(
                    f"{where}: stage '{name}' lists {normalised} more than once"
                )
            cited.append(normalised)
        parsed.append((name, cited))
    return parsed


def measure_pipeline_path(root: Path = ROOT) -> dict:
    """Tokens of the files the default route reads, per stage of the pipeline.

    ``<root>/docs/pipeline-path.yaml`` lists, in order, ``{name, files}``
    stages; each file is read from *root*. Returns::

        {
            "stages": {name: tokens, ...},   # file order
            "files": {file: tokens, ...},    # every distinct file, once
            "total": sum of the stage tokens,
        }

    A file cited by two stages counts in both: a stage's figure is what that
    stage reads, so ``total`` can exceed the sum of ``files``. Raises
    ``PipelinePathError``.
    """
    root = Path(root)
    stages: dict[str, int] = {}
    files: dict[str, int] = {}
    for name, cited in _read_stages(root / PIPELINE_PATH_FILE):
        for file in cited:
            if file not in files:
                files[file] = _strict_file_tokens(root, name, file)
        stages[name] = sum(files[file] for file in cited)
    return {"stages": stages, "files": files, "total": sum(stages.values())}


def _load_installer():
    """Return ``(CliRunner, install_command)``.

    An installed ``aiadev`` (or ``PYTHONPATH=src``) wins; otherwise this
    checkout's ``src/`` is appended to ``sys.path``, so the script also
    runs from a bare clone. Raises ``ImportError`` when neither works.
    """
    src = str(ROOT / "src")
    if src not in sys.path:
        sys.path.append(src)
    from aiadev.commands.install import install_command
    from click.testing import CliRunner

    return CliRunner, install_command


def install_preset(preset: str, dest: Path) -> None:
    """Install *preset* into *dest* the way ``aiadev install`` does.

    Goes through the CLI command (not ``install_engine.install``) because
    only the CLI applies ``preset.yaml`` variable defaults. Resolves the
    framework from this checkout, whatever the caller's working directory.
    """
    cli_runner, install_command = _load_installer()
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    result = cli_runner().invoke(
        install_command,
        [
            "--project-root",
            str(dest),
            "--preset",
            preset,
            "--non-interactive",
            "--vars",
            f"PROJECT_NAME={PROJECT_NAME}",
        ],
        env={"AIADEV_ROOT": str(ROOT)},
    )
    if result.exit_code != 0:
        detail = result.output.strip() or repr(result.exception)
        raise RuntimeError(
            f"aiadev install --preset {preset} exited {result.exit_code}: {detail}"
        )


def _missing_dependency() -> str | None:
    """An actionable message when a runtime dependency is absent, else None."""
    try:
        import yaml  # noqa: F401
    except ImportError:
        return "pyyaml not installed. Run: pip install pyyaml"
    try:
        _load_installer()
    except ImportError as exc:
        return (
            f"aiadev is not importable ({exc}). "
            "Run: pip install -e '.[dev]' (or set PYTHONPATH=src)"
        )
    return None


def main(argv: list[str]) -> int:
    missing = _missing_dependency()
    if missing:
        print(f"error: {missing}", file=sys.stderr)
        return 2

    failed = False
    for preset in argv or list(DEFAULT_PRESETS):
        if not (ROOT / "presets" / preset).is_dir():
            print(f"FAIL {preset}: no such preset under {ROOT / 'presets'}")
            failed = True
            continue
        try:
            with tempfile.TemporaryDirectory(prefix="instruction-budget-") as tmp:
                install_preset(preset, Path(tmp))
                counts = measure_always_loaded(Path(tmp))
        except (RuntimeError, ValueError) as exc:
            print(f"FAIL {preset}: {exc}")
            failed = True
            continue

        print(preset)
        for name in (*COMPONENTS, "total"):
            print(f"  {name:<11}{counts[name]:>7}")
        print(f"OK   {preset}: ~{counts['total']} tokens always loaded (chars / 4)")

    try:
        path = measure_pipeline_path()
    except (RuntimeError, ValueError) as exc:
        print(f"FAIL pipeline path: {exc}")
        failed = True
    else:
        print("pipeline path")
        width = max(11, *(len(name) for name in path["stages"])) + 2
        for name, tokens in (*path["stages"].items(), ("total", path["total"])):
            print(f"  {name:<{width}}{tokens:>7}")
        print(f"OK   pipeline path: ~{path['total']} tokens (chars / 4)")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
