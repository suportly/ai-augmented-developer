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

The **budget** (``docs/instruction-budget.json``) is the ratchet that keeps
all of the above from growing back. It is a flat map of measurement keys to
``{"baseline": N, "teto": N}`` (``teto`` is the ceiling; ``reason`` is an
optional string)::

    preset:<preset>:total            always-loaded total of a preset
    preset:<preset>:<component>      one of agent_file, wrapper, rules,
                                     skills, commands, agents
    path:total                       pipeline path total (sum of the stages)
    path:<file>                      one cited file of the pipeline path,
                                     in its normalised POSIX spelling
    skill:<name>                     whole skills/<name>/SKILL.md

``baseline`` is the measurement taken before any cut (the reference for the
reduction target); ``teto`` starts equal to it and only goes down as the
text is cut. ``--check`` fails for every key measured above its ``teto``.
A key measured but absent from the file is not a failure (a new skill's body
is not budgeted until it is added to the file); a key in the file that is no
longer measured is ignored.

To raise a ``teto`` on purpose, edit the file by hand: set the new ``teto``
and, when it ends up above the ``baseline``, a non-empty ``reason`` on that
entry; a ``teto`` above its ``baseline`` without a ``reason`` makes the
budget malformed and ``--check`` fails. The rule is stateless: raising a
lowered ``teto`` back up to its ``baseline`` needs no ``reason``, and only
the PR diff shows it. The ``reason`` is reviewed in the PR.

Usage:
    scripts/instruction_budget.py                # lean and django-drf-react
    scripts/instruction_budget.py PRESET ...     # specific presets
    scripts/instruction_budget.py --check        # compare against the budget
    scripts/instruction_budget.py --write-baseline [--force]
    scripts/instruction_budget.py --check --budget FILE   # another budget file

The pipeline path is always printed after the presets. ``--check`` and
``--write-baseline`` always cover the default presets (they take no PRESET)
and print that same report before the verdict. ``--check`` prints one
``FAIL <key>: <current> > teto <teto> (+<delta>)`` line per exceeded entry
and ``OK   budget: ...`` otherwise. ``--write-baseline`` records the current
measurement with ``teto == baseline`` and refuses to overwrite an existing
file without ``--force``: the baseline is rewritten only when a spec closes.
``--write-baseline --force`` rewrites EVERY entry as baseline == teto ==
current, discarding any ``reason`` and the previous baseline. The reference
of the reduction target survives as ``origin`` (recorded on the first write
for the three headline totals, preserved afterwards): verify the reduction
BEFORE ``--force``, and restore a ``reason`` by hand if one is still needed.

Exit codes:
    0 — every preset and the pipeline path measured (and, with ``--check``,
        nothing exceeds its teto; with ``--write-baseline``, the file written)
    1 — a preset is unknown or its install/measurement failed, or the
        pipeline path file is malformed or cites a file that does not exist;
        with ``--check``, an entry exceeds its teto, the budget is missing
        or malformed, or no entry matches the measurement; with
        ``--write-baseline``, the file exists and ``--force`` was not given
    2 — missing runtime dependencies (pyyaml, aiadev and its click/rich),
        or a usage error
"""
from __future__ import annotations

import argparse
import json
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

#: The versioned instruction budget (baseline + teto per key).
BUDGET_FILE = ROOT / "docs" / "instruction-budget.json"
BUDGET_VERSION = 1
#: Recorded in the budget: figures are only comparable under the same estimator.
BUDGET_UNIT = "ceil(chars/4)"
#: Headline keys that record ``origin``: the pre-cut baseline, kept stable
#: when ``baseline`` is lowered, so the reduction target stays verifiable.
ORIGIN_KEYS: tuple[str, ...] = (
    "preset:lean:total",
    "preset:django-drf-react:total",
    "path:total",
)


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


def measure_skills(root: Path = ROOT) -> dict[str, int]:
    """Tokens of each whole ``<root>/skills/<name>/SKILL.md``, keyed
    ``skill:<name>`` (directory name). Unlike the always-loaded figures this
    counts the body: it is what a skill costs once invoked."""
    return {
        f"skill:{path.parent.name}": estimate_tokens(path.read_text(encoding="utf-8"))
        for path in sorted((Path(root) / "skills").glob("*/SKILL.md"))
    }


def _measure_preset(preset: str) -> dict[str, int]:
    """Install *preset* into a temporary project and measure it. Raises
    ``ValueError`` for an unknown preset, ``RuntimeError`` if the install fails."""
    if not (ROOT / "presets" / preset).is_dir():
        raise ValueError(f"no such preset under {ROOT / 'presets'}")
    with tempfile.TemporaryDirectory(prefix="instruction-budget-") as tmp:
        install_preset(preset, Path(tmp))
        return measure_always_loaded(Path(tmp))


def _flatten(
    presets: dict[str, dict[str, int]], path: dict, skills: dict[str, int]
) -> dict[str, int]:
    """The measurement as the flat ``key -> tokens`` map the budget is keyed by."""
    measured: dict[str, int] = {}
    for preset, counts in presets.items():
        for name in ("total", *COMPONENTS):
            measured[f"preset:{preset}:{name}"] = counts[name]
    measured["path:total"] = path["total"]
    for file, tokens in path["files"].items():
        measured[f"path:{file}"] = tokens
    measured.update(skills)
    return measured


def measure_all(presets: tuple[str, ...] | list[str] = DEFAULT_PRESETS) -> dict[str, int]:
    """Every budgeted figure of the current tree, keyed as in the budget file
    (see the module docstring). Raises ``RuntimeError`` / ``ValueError`` when
    a preset or the pipeline path cannot be measured."""
    counts = {preset: _measure_preset(preset) for preset in presets}
    return _flatten(counts, measure_pipeline_path(), measure_skills())


class BudgetError(ValueError):
    """The budget file is missing or malformed, or would be overwritten."""


def load_budget(path: Path) -> dict:
    """The parsed budget at *path*, structure validated.

    Raises ``BudgetError`` for a missing file, invalid JSON, another
    ``version`` or ``unit``, or an entry without integer ``baseline`` and
    ``teto``. Whether a ``teto`` above its ``baseline`` has a ``reason`` is
    judged by ``check_budget``.
    """
    path = Path(path)
    where = path.name
    if not path.is_file():
        raise BudgetError(f"{where}: budget file not found (create it with --write-baseline)")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise BudgetError(f"{where}: invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise BudgetError(f"{where}: expected a JSON object")
    if data.get("version") != BUDGET_VERSION:
        raise BudgetError(f"{where}: unsupported version {data.get('version')!r}")
    if data.get("unit") != BUDGET_UNIT:
        raise BudgetError(
            f"{where}: unit is {data.get('unit')!r}, this script measures "
            f"{BUDGET_UNIT!r}; rewrite the baseline with --write-baseline --force"
        )
    entries = data.get("entries")
    if not isinstance(entries, dict):
        raise BudgetError(f"{where}: expected an 'entries' object")
    for key, entry in entries.items():
        if not isinstance(entry, dict):
            raise BudgetError(f"{where}: entry '{key}' must be an object")
        for field in ("baseline", "teto"):
            if not isinstance(entry.get(field), int):
                raise BudgetError(f"{where}: entry '{key}': '{field}' must be an integer")
        if "origin" in entry and not isinstance(entry["origin"], int):
            raise BudgetError(f"{where}: entry '{key}': 'origin' must be an integer")
    return data


def reduction_shortfalls(data: dict, keys: tuple[str, ...] | list[str], minimum: float) -> list[str]:
    """One ``FAIL`` line per key of *keys* whose ``baseline`` is not at least
    *minimum* (0.40 = 40%) below its ``origin``; empty when the target holds.
    The desired ceiling is ``floor(origin * (1 - minimum))``."""
    lines: list[str] = []
    for key in keys:
        entry = data["entries"].get(key, {})
        origin = entry.get("origin")
        if not isinstance(origin, int) or isinstance(origin, bool) or origin <= 0:
            lines.append(f"FAIL {key}: no integer 'origin' recorded")
            continue
        ceiling = int(origin * (1 - minimum))
        current = entry["baseline"]
        if current > ceiling:
            change = (current - origin) / origin * 100
            lines.append(
                f"FAIL {key}: {current} > desired ceiling {ceiling} "
                f"(origin {origin}, {change:+.1f}% < -{minimum * 100:.0f}%; "
                f"+{current - ceiling} to cut)"
            )
    return lines


def check_budget(measured: dict[str, int], budget: dict) -> list[str]:
    """One ``FAIL`` line per problem, in budget order; empty when it holds.

    - a measurement above its ``teto``:
      ``FAIL <key>: <current> > teto <teto> (+<delta>)``;
    - a ``teto`` above its ``baseline`` with no non-empty ``reason``: a
      malformed budget, reported even if the key is no longer measured.

    A measured key absent from the budget is not a failure, and a budget
    entry that is not measured is not compared.
    """
    failures: list[str] = []
    for key, entry in budget["entries"].items():
        baseline, teto = entry["baseline"], entry["teto"]
        reason = entry.get("reason")
        if teto > baseline and not (isinstance(reason, str) and reason.strip()):
            failures.append(
                f"FAIL {key}: teto {teto} > baseline {baseline} needs a non-empty "
                '"reason" (malformed budget)'
            )
        current = measured.get(key)
        if current is not None and current > teto:
            failures.append(f"FAIL {key}: {current} > teto {teto} (+{current - teto})")
    return failures


def write_baseline(path: Path, measured: dict[str, int], force: bool = False) -> None:
    """Record *measured* as the budget: ``baseline == teto == measurement``.

    The baseline is the pre-cut reference, so an existing file is never
    replaced unless *force*. Raises ``BudgetError`` in that case. An
    ``origin`` already in the file is preserved; the first write records it
    (equal to the measurement) for ``ORIGIN_KEYS`` only.
    """
    path = Path(path)
    if path.exists() and not force:
        raise BudgetError(
            f"{path.name} already exists; --force replaces it (rewrites every "
            "baseline and teto from the current measurement)"
        )
    previous: dict = {}
    if path.exists():
        try:
            previous = load_budget(path)["entries"]
        except BudgetError:
            previous = {}  # unreadable old file: nothing to preserve
    entries: dict[str, dict] = {}
    for key, n in measured.items():
        origin = previous.get(key, {}).get("origin")
        if origin is None and key in ORIGIN_KEYS:
            origin = n
        entries[key] = ({"origin": origin} if origin is not None else {}) | {
            "baseline": n,
            "teto": n,
        }
    data = {"version": BUDGET_VERSION, "unit": BUDGET_UNIT, "entries": entries}
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


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


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="instruction_budget.py",
        description="Measure the instruction cost of each preset and of the "
        "pipeline path, and check it against the versioned budget.",
    )
    parser.add_argument(
        "presets",
        nargs="*",
        metavar="PRESET",
        help=f"presets to measure (default: {' '.join(DEFAULT_PRESETS)})",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--check",
        action="store_true",
        help="fail if any measurement exceeds its teto in the budget",
    )
    mode.add_argument(
        "--write-baseline",
        action="store_true",
        help="record the current measurement as baseline and teto "
        "(refuses to overwrite an existing budget)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="with --write-baseline: overwrite an existing budget",
    )
    parser.add_argument(
        "--budget",
        type=Path,
        default=BUDGET_FILE,
        metavar="FILE",
        help="budget file (default: docs/instruction-budget.json)",
    )
    args = parser.parse_args(argv)
    if args.presets and (args.check or args.write_baseline):
        parser.error("--check and --write-baseline cover the default presets: drop PRESET")
    return args


def _report(presets: list[str]) -> tuple[dict[str, dict[str, int]], dict | None, bool]:
    """Print the per-preset blocks and the pipeline path block. Returns the
    per-preset counts, the path measurement (None when it failed) and whether
    anything failed."""
    failed = False
    counts: dict[str, dict[str, int]] = {}
    for preset in presets:
        try:
            counts[preset] = _measure_preset(preset)
        except (RuntimeError, ValueError) as exc:
            print(f"FAIL {preset}: {exc}")
            failed = True
            continue

        print(preset)
        for name in (*COMPONENTS, "total"):
            print(f"  {name:<11}{counts[preset][name]:>7}")
        print(f"OK   {preset}: ~{counts[preset]['total']} tokens always loaded (chars / 4)")

    try:
        path = measure_pipeline_path()
    except (RuntimeError, ValueError) as exc:
        print(f"FAIL pipeline path: {exc}")
        return counts, None, True

    print("pipeline path")
    width = max(11, *(len(name) for name in path["stages"])) + 2
    for name, tokens in (*path["stages"].items(), ("total", path["total"])):
        print(f"  {name:<{width}}{tokens:>7}")
    print(f"OK   pipeline path: ~{path['total']} tokens (chars / 4)")
    return counts, path, failed


def _shown(path: Path) -> str:
    """*path* relative to the framework root when it lives under it."""
    try:
        return Path(path).resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def main(argv: list[str]) -> int:
    args = _parse_args(argv)
    missing = _missing_dependency()
    if missing:
        print(f"error: {missing}", file=sys.stderr)
        return 2

    counts, path, failed = _report(args.presets or list(DEFAULT_PRESETS))
    if not (args.check or args.write_baseline):
        return 1 if failed else 0
    if failed or path is None:
        print("FAIL budget: not evaluated, a measurement above failed")
        return 1

    try:
        measured = _flatten(counts, path, measure_skills())
        if args.write_baseline:
            write_baseline(args.budget, measured, force=args.force)
            print(f"OK   budget: baseline written, {len(measured)} entries ({_shown(args.budget)})")
            return 0
        budget = load_budget(args.budget)
    except (OSError, ValueError) as exc:
        print(f"FAIL budget: {exc}")
        return 1

    failures = check_budget(measured, budget)
    if failures:
        print("\n".join(failures))
        print(
            f"     hint: cut the text, or raise the teto in {_shown(args.budget)} "
            'with a non-empty "reason"'
        )
        return 1
    checked = sum(1 for key in budget["entries"] if key in measured)
    if not checked:
        print("FAIL budget: no budget entry matches the current measurement")
        return 1
    print(f"OK   budget: {checked} entries within teto ({_shown(args.budget)})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
