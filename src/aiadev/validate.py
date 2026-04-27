"""Validation helpers shared by ``aiadev validate`` and the test suite.

Replaces ``scripts/validate_skills.py`` once the CLI ships. The script
continues to exist as a zero-install fallback for CI.
"""
from __future__ import annotations

import json
import pathlib
import re
from dataclasses import dataclass, field
from typing import Iterable

import yaml
from jsonschema import Draft202012Validator

from .paths import find_framework_root, skill_frontmatter_schema

_SPEC_ID_RE = re.compile(r"^\*\*Spec ID:\*\*\s*(\d+)", re.MULTILINE)
_RECON_ANCHOR = "<!-- section: Reconnaissance -->"
_NEXT_ANCHOR_RE = re.compile(r"<!-- section: [^>]+ -->")


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


def _spec_recon_schema(root: pathlib.Path) -> dict:
    return json.loads(
        (root / "schemas" / "spec-recon.schema.json").read_text(encoding="utf-8")
    )


def _extract_recon_body(text: str) -> str | None:
    """Return the body between the recon anchor and the next section anchor.

    Returns ``None`` when the recon anchor is missing entirely.
    """
    anchor_pos = text.find(_RECON_ANCHOR)
    if anchor_pos == -1:
        return None
    after = text[anchor_pos + len(_RECON_ANCHOR):]
    next_match = _NEXT_ANCHOR_RE.search(after)
    return after[: next_match.start()] if next_match else after


def _recon_body_is_empty(body: str) -> bool:
    """The recon body counts as empty when it carries no non-blank,
    non-heading, non-comment content."""
    for raw_line in body.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or line.startswith("<!--"):
            continue
        return False
    return True


def validate_spec(
    path: pathlib.Path,
    *,
    root: pathlib.Path | None = None,
) -> ValidationReport:
    """Validate one ``spec.md`` against the recon rule (issue #26).

    The validator is structural: it does not enforce session-freshness
    (cl-2 resolution in spec 0011). It checks the cutover guard, the
    presence of the recon section, and that entries cite on-disk paths
    or use the explicit opt-out line.
    """
    root = (root or find_framework_root()).resolve()
    schema = _spec_recon_schema(root)
    cutover = int(schema["cutover_spec_id"])

    report = ValidationReport()
    path = path.resolve()
    if not path.exists():
        report.failed.append(SkillIssue(path, "file does not exist"))
        return report

    text = path.read_text(encoding="utf-8")

    spec_id_match = _SPEC_ID_RE.search(text)
    if not spec_id_match:
        report.failed.append(SkillIssue(path, "missing or unparseable Spec ID header"))
        return report
    spec_id = int(spec_id_match.group(1))

    if spec_id <= cutover:
        report.passed.append(path)
        return report

    body = _extract_recon_body(text)
    if body is None or _recon_body_is_empty(body):
        report.failed.append(
            SkillIssue(
                path,
                "Reconnaissance section required; add at least one surface entry or opt-out line",
            )
        )
        return report

    opt_out_re = re.compile(schema["opt_out_pattern"], re.MULTILINE)
    if opt_out_re.search(body):
        report.passed.append(path)
        return report

    entry_re = re.compile(schema["recon_entry_pattern"], re.MULTILINE)
    matches = list(entry_re.finditer(body))
    if not matches:
        report.failed.append(
            SkillIssue(
                path,
                "Reconnaissance entries must cite at least one file path per surface",
            )
        )
        return report

    missing = [
        m.group(1) for m in matches
        if not (root / m.group(1)).exists()
    ]
    if missing:
        for cited in missing:
            report.failed.append(
                SkillIssue(path, f"Reconnaissance path '{cited}' does not exist")
            )
        return report

    report.passed.append(path)
    return report


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
    """Validate the given paths.

    Files are dispatched by basename: ``spec.md`` → :func:`validate_spec`
    (recon rule, issue #26), every other ``SKILL.md``-style path → the
    skill-frontmatter validator. When ``paths`` is empty, the function
    sweeps every ``SKILL.md`` under ``root``; spec sweeping is explicit
    only — pass the ``spec.md`` paths the caller wants validated.
    """
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

        if skill_path.name == "spec.md":
            spec_report = validate_spec(skill_path, root=root)
            report.passed.extend(spec_report.passed)
            report.failed.extend(spec_report.failed)
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
