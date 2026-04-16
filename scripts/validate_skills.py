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


def check_markers(text: str) -> list[str]:
    """Return error messages for malformed cl-N markers in *text*.

    Every recognized token (`[NEEDS CLARIFICATION:...]`) is matched against
    the canonical regex from schemas/marker-grammar.schema.json. Tokens that
    do not fully match (missing `cl-N`, zero-padded, decimal, etc.) yield
    one error each. Legacy back-compat (tokens without `cl-N`) is added in
    T003 — until then they are reported as malformed.
    """
    pattern = load_marker_pattern()
    errors: list[str] = []
    for match in re.finditer(r"\[NEEDS CLARIFICATION:[^\]]*\]", text):
        token = match.group(0)
        if not pattern.fullmatch(token):
            errors.append(f"Malformed marker: {token}")
    return errors


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

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
