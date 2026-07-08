#!/usr/bin/env python3
"""Zero-install fallback skill validator (no ``aiadev`` package import).

Validates every ``skills/*/SKILL.md`` frontmatter against BOTH schemas
(spec 0016, ADR-3), mirroring ``aiadev validate`` (``src/aiadev/validate.py``):

- the vendored open Agent Skills standard snapshot
  (``schemas/agent-skills.schema.json``) — external conformance, errors
  prefixed ``[agent-skills]``;
- the internal aiadev schema (``schemas/skill-frontmatter.schema.json``) —
  shape of the ``metadata.aiadev`` pipeline namespace, errors prefixed
  ``[aiadev]``.

A proprietary pipeline field (``version``, ``inputs``, ``outputs``,
``requires``, ``handoffs``) left at the top level (pre-0016 format) gets an
additional didactic ``[aiadev]`` message naming the field and its new
location under ``metadata.aiadev.<field>`` (cl-5, ADR-3, spec 0016).

Also checks that the frontmatter ``name`` matches the containing directory.

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
STANDARD_SCHEMA_PATH = ROOT / "schemas" / "agent-skills.schema.json"
MARKER_SCHEMA_PATH = ROOT / "schemas" / "marker-grammar.schema.json"

#: The 5 proprietary aiadev pipeline fields that must live under
#: ``metadata.aiadev`` (spec 0016 ADR-4). Kept as a local literal — not
#: imported from ``aiadev.frontmatter_migrate.PROPRIETARY_KEYS`` — so this
#: script stays a zero-install fallback with no dependency on the aiadev
#: package. Keep in sync with that module if the field list ever changes.
PROPRIETARY_KEYS: tuple[str, ...] = (
    "version",
    "inputs",
    "outputs",
    "requires",
    "handoffs",
)


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


def _didactic_proprietary_field_errors(frontmatter: dict) -> list[str]:
    """Didactic message for a proprietary field left at the top level.

    Mirrors ``aiadev.validate._didactic_proprietary_field_errors``: names
    the offending field AND the exact new location (cl-5, ADR-3).
    """
    return [
        f"[aiadev] {key}: proprietary pipeline field at top level — "
        f"move it to metadata.aiadev.{key} (see spec 0016)"
        for key in PROPRIETARY_KEYS
        if key in frontmatter
    ]


def main(argv: list[str]) -> int:
    aiadev_schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    aiadev_validator = Draft202012Validator(aiadev_schema)
    standard_schema = json.loads(STANDARD_SCHEMA_PATH.read_text(encoding="utf-8"))
    standard_validator = Draft202012Validator(standard_schema)
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

        # Dual validation (spec 0016, ADR-3): standard conformance first,
        # then the didactic proprietary-field check, then the internal
        # aiadev shape — same order and origin prefixes as
        # aiadev.validate.validate_paths.
        messages: list[str] = []
        for error in sorted(standard_validator.iter_errors(frontmatter), key=lambda e: e.path):
            location = "/".join(str(p) for p in error.path) or "<root>"
            messages.append(f"[agent-skills] {location}: {error.message}")
        messages.extend(_didactic_proprietary_field_errors(frontmatter))
        for error in sorted(aiadev_validator.iter_errors(frontmatter), key=lambda e: e.path):
            location = "/".join(str(p) for p in error.path) or "<root>"
            messages.append(f"[aiadev] {location}: {error.message}")

        if messages:
            print(f"FAIL {skill_path}:")
            for message in messages:
                print(f"  - {message}")
            failed = True
            continue

        print(f"OK   {skill_path}")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
