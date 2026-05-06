#!/usr/bin/env python3
"""Provisional skill validator. Replaced by ``aiadev validate`` in phase 5.

Validates every ``skills/*/SKILL.md`` frontmatter against
``schemas/skill-frontmatter.schema.json`` and checks that the frontmatter
``name`` matches the containing directory.

Usage:
    scripts/validate_skills.py              # validate every skill
    scripts/validate_skills.py path ...     # validate specific SKILL.md files

Exit codes:
    0 — everything valid
    1 — at least one skill failed validation
    2 — missing runtime dependencies (pyyaml, jsonschema)
"""
from __future__ import annotations

import json
import pathlib
import re
import sys
from typing import Iterable

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "schemas" / "skill-frontmatter.schema.json"
MARKER_SCHEMA_PATH = ROOT / "schemas" / "marker-grammar.schema.json"


def load_marker_pattern() -> re.Pattern[str]:
    """Compile the canonical cl-N marker regex from the marker-grammar schema.

    Single source of truth for the grammar lives in
    schemas/marker-grammar.schema.json under the `x-marker-pattern` extension.
    """
    schema = json.loads(MARKER_SCHEMA_PATH.read_text(encoding="utf-8"))
    return re.compile(schema["x-marker-pattern"])


_LEGACY_MARKER_RE = re.compile(r"\[NEEDS CLARIFICATION:\s+[^\]]+\]")


def check_markers(text: str) -> dict[str, list[str]]:
    """Classify NEEDS CLARIFICATION markers in *text*.

    Returns a dict with two lists:

    - ``errors``   — tokens that look like the new grammar (have ``cl-``
      after the colon) but do not fully match it. Examples: ``cl-001``,
      ``cl-1.2``.
    - ``warnings`` — legacy tokens without ``cl-N`` (whitespace right after
      the colon). Accepted for back-compat with specs created before T001.

    Valid ``[NEEDS CLARIFICATION:cl-N <question>]`` markers produce neither.
    """
    pattern = load_marker_pattern()
    errors: list[str] = []
    warnings: list[str] = []
    for match in re.finditer(r"\[NEEDS CLARIFICATION:[^\]]*\]", text):
        token = match.group(0)
        if pattern.fullmatch(token):
            continue
        if _LEGACY_MARKER_RE.fullmatch(token):
            warnings.append(f"Legacy marker (no cl-N id): {token}")
        else:
            errors.append(f"Malformed marker: {token}")
    return {"errors": errors, "warnings": warnings}


_BARE_IMPLEMENT_SKILL = ROOT / "skills" / "implement" / "SKILL.md"
_MIRROR_IMPLEMENT_SKILL = ROOT / ".claude" / "skills" / "implement" / "SKILL.md"


class ImplementSkillDriftError(Exception):
    """Raised by ``check_implement_mirror`` when the two SKILL.md copies
    disagree on the loop section."""


def _extract_loop_section(text: str) -> str:
    """Return the ``## The loop`` section verbatim, or raise if absent.

    Anchored on ``## The loop`` and the next top-level ``## `` heading
    so frontmatter and unrelated sections are excluded — only the loop
    contract has to match between the two skill copies.
    """
    start = text.find("\n## The loop\n")
    if start < 0:
        raise ImplementSkillDriftError(
            "implement SKILL.md is missing the '## The loop' section"
        )
    start += 1  # skip the leading newline
    end = text.find("\n## ", start + len("## The loop\n"))
    return text[start:end] if end >= 0 else text[start:]


def check_implement_mirror() -> None:
    """Assert that ``skills/implement/SKILL.md`` and
    ``.claude/skills/implement/SKILL.md`` carry an identical
    ``## The loop`` section (modulo trailing whitespace per line).

    Raises ``ImplementSkillDriftError`` with a unified diff snippet
    on mismatch. Per spec 0013 Story 3 sc2, the two copies must not
    drift; CI invokes this through the script's main entry point.
    """
    bare_text = _BARE_IMPLEMENT_SKILL.read_text(encoding="utf-8")
    mirror_text = _MIRROR_IMPLEMENT_SKILL.read_text(encoding="utf-8")

    bare_loop = _extract_loop_section(bare_text)
    mirror_loop = _extract_loop_section(mirror_text)

    def _normalise(section: str) -> list[str]:
        return [line.rstrip() for line in section.splitlines()]

    if _normalise(bare_loop) == _normalise(mirror_loop):
        return

    import difflib

    diff = "".join(
        difflib.unified_diff(
            _normalise(bare_loop),
            _normalise(mirror_loop),
            fromfile=str(_BARE_IMPLEMENT_SKILL.relative_to(ROOT)),
            tofile=str(_MIRROR_IMPLEMENT_SKILL.relative_to(ROOT)),
            lineterm="",
            n=3,
        )
    )
    raise ImplementSkillDriftError(
        "implement SKILL.md drift detected between the bare and .claude/ "
        f"copies:\n{diff}"
    )


def _die(message: str, code: int = 2) -> None:
    print(f"error: {message}", file=sys.stderr)
    sys.exit(code)


try:
    import yaml  # type: ignore
except ImportError:
    _die("pyyaml not installed. Run: pip install pyyaml jsonschema")

try:
    from jsonschema import Draft202012Validator
except ImportError:
    _die("jsonschema not installed. Run: pip install pyyaml jsonschema")


def extract_frontmatter(path: pathlib.Path) -> dict | None:
    """Return the parsed YAML frontmatter of a markdown file, or None if missing."""
    text = path.read_text(encoding="utf-8").splitlines()
    if not text or text[0].strip() != "---":
        return None
    body: list[str] = []
    for line in text[1:]:
        if line.strip() == "---":
            break
        body.append(line)
    else:
        return None
    try:
        parsed = yaml.safe_load("\n".join(body))
    except yaml.YAMLError as exc:
        return {"__parse_error__": str(exc)}
    if not isinstance(parsed, dict):
        return None
    return parsed


def iter_skill_files(args: list[str]) -> Iterable[pathlib.Path]:
    if args:
        for arg in args:
            yield pathlib.Path(arg)
        return
    # Root catalog.
    for path in sorted((ROOT / "skills").rglob("SKILL.md")):
        yield path
    # Every preset ships its own skills/; validate those too.
    presets_root = ROOT / "presets"
    if presets_root.is_dir():
        for preset_skills in sorted(presets_root.glob("*/skills")):
            for path in sorted(preset_skills.rglob("SKILL.md")):
                yield path


def main(argv: list[str]) -> int:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    failed = False

    for skill_path in iter_skill_files(argv):
        if not skill_path.exists():
            print(f"FAIL {skill_path}: file does not exist")
            failed = True
            continue

        frontmatter = extract_frontmatter(skill_path)
        if frontmatter is None:
            print(f"FAIL {skill_path}: missing YAML frontmatter")
            failed = True
            continue
        if "__parse_error__" in frontmatter:
            print(f"FAIL {skill_path}: YAML parse error")
            print(f"  - {frontmatter['__parse_error__']}")
            failed = True
            continue

        expected_name = skill_path.parent.name
        actual_name = frontmatter.get("name")
        if actual_name != expected_name:
            print(
                f"FAIL {skill_path}: frontmatter name '{actual_name}' "
                f"does not match directory '{expected_name}'"
            )
            failed = True
            continue

        errors = sorted(validator.iter_errors(frontmatter), key=lambda e: e.path)
        if errors:
            print(f"FAIL {skill_path}:")
            for error in errors:
                location = "/".join(str(p) for p in error.path) or "<root>"
                print(f"  - {location}: {error.message}")
            failed = True
            continue

        print(f"OK   {skill_path}")

    # Cross-file drift check between the two implement/SKILL.md copies.
    # Only run when validating the full catalog (no explicit args) — when
    # the user passes specific paths they may not be the implement skill.
    if not argv:
        try:
            check_implement_mirror()
        except ImplementSkillDriftError as exc:
            print(f"FAIL implement SKILL.md drift:\n{exc}")
            failed = True
        else:
            print("OK   implement SKILL.md mirror (loop section aligned)")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
