"""Validation helpers shared by ``aiadev validate`` and the test suite.

Replaces ``scripts/validate_skills.py`` once the CLI ships. The script
continues to exist as a zero-install fallback for CI.
"""
from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass, field
from typing import Iterable

import yaml
from jsonschema import Draft202012Validator

from .paths import find_framework_root, skill_frontmatter_schema


@dataclass
class SkillIssue:
    """One problem discovered in one SKILL.md."""

    path: pathlib.Path
    message: str

    def format(self) -> str:
        return f"FAIL {self.path}: {self.message}"


@dataclass
class ValidationReport:
    """Outcome of validating one or more SKILL.md files."""

    passed: list[pathlib.Path] = field(default_factory=list)
    failed: list[SkillIssue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.failed

    def as_lines(self) -> list[str]:
        lines = [f"OK   {p}" for p in self.passed]
        lines.extend(issue.format() for issue in self.failed)
        return lines


def extract_frontmatter(path: pathlib.Path) -> tuple[dict | None, str | None]:
    """Parse the YAML frontmatter of a markdown file.

    Returns ``(data, error)`` where exactly one is ``None``. ``data`` is
    the parsed mapping on success; ``error`` is a human-readable string on
    failure.
    """
    text = path.read_text(encoding="utf-8").splitlines()
    if not text or text[0].strip() != "---":
        return None, "missing YAML frontmatter"
    body: list[str] = []
    closed = False
    for line in text[1:]:
        if line.strip() == "---":
            closed = True
            break
        body.append(line)
    if not closed:
        return None, "unterminated YAML frontmatter"
    try:
        parsed = yaml.safe_load("\n".join(body))
    except yaml.YAMLError as exc:
        return None, f"YAML parse error: {exc}"
    if not isinstance(parsed, dict):
        return None, "frontmatter is not a mapping"
    return parsed, None


def iter_skill_files(root: pathlib.Path) -> Iterable[pathlib.Path]:
    """Yield every ``SKILL.md`` under the root's ``skills/`` and every preset."""
    skills_root = root / "skills"
    if skills_root.is_dir():
        yield from sorted(skills_root.rglob("SKILL.md"))
    presets_root = root / "presets"
    if presets_root.is_dir():
        for preset_skills in sorted(presets_root.glob("*/skills")):
            yield from sorted(preset_skills.rglob("SKILL.md"))


def validate_paths(
    paths: Iterable[pathlib.Path],
    *,
    root: pathlib.Path | None = None,
) -> ValidationReport:
    """Validate the given SKILL.md paths. If empty, validate every skill under root."""
    root = (root or find_framework_root()).resolve()
    schema = json.loads(skill_frontmatter_schema(root).read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)

    report = ValidationReport()
    targets = list(paths) or list(iter_skill_files(root))

    for skill_path in targets:
        skill_path = skill_path.resolve()
        if not skill_path.exists():
            report.failed.append(SkillIssue(skill_path, "file does not exist"))
            continue

        data, error = extract_frontmatter(skill_path)
        if data is None:
            report.failed.append(SkillIssue(skill_path, error or "unknown error"))
            continue

        expected_name = skill_path.parent.name
        actual_name = data.get("name")
        if actual_name != expected_name:
            report.failed.append(
                SkillIssue(
                    skill_path,
                    f"frontmatter name '{actual_name}' does not match directory '{expected_name}'",
                )
            )
            continue

        schema_errors = sorted(validator.iter_errors(data), key=lambda e: list(e.path))
        if schema_errors:
            details = "; ".join(
                f"{'/'.join(str(p) for p in err.path) or '<root>'}: {err.message}"
                for err in schema_errors
            )
            report.failed.append(SkillIssue(skill_path, details))
            continue

        report.passed.append(skill_path)

    return report
