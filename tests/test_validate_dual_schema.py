"""Tests for the dual-schema validation added in spec 0016 (T005).

``aiadev validate`` must check every SKILL.md frontmatter against BOTH:

- the vendored standard snapshot (``schemas/agent-skills.schema.json``) —
  external conformance to the open Agent Skills standard;
- the internal schema (``schemas/skill-frontmatter.schema.json``) — shape
  of the ``metadata.aiadev`` pipeline namespace.

Each reported error must state its origin (standard vs aiadev), and a
proprietary pipeline field left at the top level (old pre-0016 format)
must fail with a didactic message naming the field and the exact new
location under ``metadata.aiadev.<field>`` (cl-5, ADR-3).
"""
from __future__ import annotations

import pathlib

from aiadev.validate import validate_paths

FIXTURES = pathlib.Path(__file__).parent / "fixtures"


def _write_skill(tmp_path: pathlib.Path, name: str, body: str) -> pathlib.Path:
    skill_dir = tmp_path / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_path = skill_dir / "SKILL.md"
    skill_path.write_text(body, encoding="utf-8")
    return skill_path


def test_conformant_fixture_passes(framework_root: pathlib.Path) -> None:
    report = validate_paths([FIXTURES / "valid-skill" / "SKILL.md"], root=framework_root)
    assert report.ok, "\n".join(issue.format() for issue in report.failed)


def test_old_format_top_level_field_fails_with_didactic_message(
    framework_root: pathlib.Path, tmp_path: pathlib.Path
) -> None:
    """A SKILL.md written in the pre-0016 format (proprietary field at top
    level) must fail validate, naming the field AND the exact new location.
    """
    skill_path = _write_skill(
        tmp_path,
        "old-format-skill",
        "---\n"
        "name: old-format-skill\n"
        "description: A skill still using the old top-level pipeline fields.\n"
        "requires:\n"
        "  - some-other-skill\n"
        "---\n\n"
        "# Old Format Skill\n",
    )
    report = validate_paths([skill_path], root=framework_root)
    assert not report.ok
    message = report.failed[0].message
    assert "requires" in message
    assert "metadata.aiadev.requires" in message


def test_standard_only_violation_reports_standard_origin(
    framework_root: pathlib.Path, tmp_path: pathlib.Path
) -> None:
    """A field unknown to both schemas is a standard-schema violation
    (``additionalProperties: false`` at the top level of the standard
    snapshot) that has nothing to do with the aiadev namespace shape.
    """
    skill_path = _write_skill(
        tmp_path,
        "unknown-field-skill",
        "---\n"
        "name: unknown-field-skill\n"
        "description: A skill with a completely unrecognized top-level field.\n"
        "totally-custom: x\n"
        "---\n\n"
        "# Unknown Field Skill\n",
    )
    report = validate_paths([skill_path], root=framework_root)
    assert not report.ok
    message = report.failed[0].message
    assert "totally-custom" in message
    # The [agent-skills] origin line must specifically name the offending
    # field (the internal schema also rejects unknown top-level fields, so
    # merely finding both prefixes somewhere would pass for the wrong reason).
    assert any(
        "[agent-skills]" in part and "totally-custom" in part
        for part in message.split("; ")
    ), message


def test_aiadev_only_violation_reports_aiadev_origin(
    framework_root: pathlib.Path, tmp_path: pathlib.Path
) -> None:
    """A shape violation inside ``metadata.aiadev`` (here: ``handoffs``
    entries must be strings, not integers) is conformant with the open
    standard (``metadata`` is an open map) but violates the internal
    aiadev schema — must be reported with the aiadev origin.
    """
    skill_path = _write_skill(
        tmp_path,
        "bad-aiadev-shape-skill",
        "---\n"
        "name: bad-aiadev-shape-skill\n"
        "description: A skill whose metadata.aiadev.handoffs has the wrong item type.\n"
        "metadata:\n"
        "  aiadev:\n"
        "    handoffs:\n"
        "      - 123\n"
        "---\n\n"
        "# Bad Aiadev Shape Skill\n",
    )
    report = validate_paths([skill_path], root=framework_root)
    assert not report.ok
    message = report.failed[0].message
    # Strict: the JSON-pointer path itself contains "aiadev", so a loose
    # substring check could pass with the WRONG origin prefix.
    assert "[aiadev]" in message, message
    assert "[agent-skills]" not in message, message


def test_all_repository_skills_pass_dual_validation(framework_root: pathlib.Path) -> None:
    """Sanity: the whole repo (post T004 migration) has zero errors under
    the new dual-schema validation."""
    report = validate_paths([], root=framework_root)
    assert report.ok, "\n".join(issue.format() for issue in report.failed)
    assert len(report.passed) >= 10
