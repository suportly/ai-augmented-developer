"""T004 — repo-wide SKILL.md conformance to the Agent Skills interop shape.

Spec: specs/0016-agent-skills-interop/spec.md, Story 1, sc2.

Every SKILL.md shipped in this repository (framework skills/ plus every
presets/*/skills/) must:

- carry NO proprietary aiadev pipeline field (``version``, ``inputs``,
  ``outputs``, ``requires``, ``handoffs``) at the top level of its YAML
  frontmatter — those live under ``metadata.aiadev``;
- validate against BOTH the external conformance schema
  (``schemas/agent-skills.schema.json``, the vendorized open Agent Skills
  standard snapshot) and the internal schema
  (``schemas/skill-frontmatter.schema.json``).

The sweep mirrors ``aiadev.validate.iter_skill_files`` (via direct reuse)
so this test and the ``aiadev validate`` CLI always agree on which files
are in scope. Test fixtures under ``tests/fixtures/`` are deliberately
out of scope — some of them exist precisely to exercise invalid shapes.
"""

from __future__ import annotations

import json
import pathlib

import pytest

from aiadev.frontmatter_migrate import PROPRIETARY_KEYS
from aiadev.validate import extract_frontmatter, iter_skill_files
from jsonschema import Draft202012Validator

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]

AGENT_SKILLS_SCHEMA = json.loads(
    (REPO_ROOT / "schemas" / "agent-skills.schema.json").read_text(encoding="utf-8")
)
SKILL_FRONTMATTER_SCHEMA = json.loads(
    (REPO_ROOT / "schemas" / "skill-frontmatter.schema.json").read_text(
        encoding="utf-8"
    )
)

SKILL_FILES = sorted(iter_skill_files(REPO_ROOT))


def _relative_ids() -> list[str]:
    return [str(p.relative_to(REPO_ROOT)) for p in SKILL_FILES]


def test_sweep_finds_the_expected_population() -> None:
    """Sanity guard: the sweep must cover skills/ AND at least two presets."""
    assert len(SKILL_FILES) >= 20, _relative_ids()
    tops = {p.relative_to(REPO_ROOT).parts[0] for p in SKILL_FILES}
    assert tops == {"skills", "presets"}, tops


@pytest.mark.parametrize(
    "skill_path", SKILL_FILES, ids=_relative_ids()
)
def test_no_proprietary_fields_at_top_level(skill_path: pathlib.Path) -> None:
    fm, error = extract_frontmatter(skill_path)
    assert fm is not None, f"{skill_path}: {error}"
    offending = [key for key in PROPRIETARY_KEYS if key in fm]
    assert not offending, (
        f"{skill_path.relative_to(REPO_ROOT)}: proprietary field(s) "
        f"{offending} must live under metadata.aiadev, not at the top level"
    )


@pytest.mark.parametrize(
    "skill_path", SKILL_FILES, ids=_relative_ids()
)
def test_frontmatter_validates_against_both_schemas(
    skill_path: pathlib.Path,
) -> None:
    fm, error = extract_frontmatter(skill_path)
    assert fm is not None, f"{skill_path}: {error}"

    for schema_name, schema in (
        ("agent-skills.schema.json", AGENT_SKILLS_SCHEMA),
        ("skill-frontmatter.schema.json", SKILL_FRONTMATTER_SCHEMA),
    ):
        errors = sorted(
            Draft202012Validator(schema).iter_errors(fm),
            key=lambda e: list(e.path),
        )
        details = "; ".join(
            f"{'/'.join(str(p) for p in err.path) or '<root>'}: {err.message}"
            for err in errors
        )
        assert not errors, (
            f"{skill_path.relative_to(REPO_ROOT)} fails {schema_name}: {details}"
        )
