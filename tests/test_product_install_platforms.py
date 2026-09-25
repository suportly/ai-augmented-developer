"""T005 — `product` skill: skeleton + installation on the 5 platforms.

Spec: specs/0023-product-context/spec.md, Story 4 sc1 and sc2.

``product`` is an agent skill only (cl-4): it is NOT part of
``PIPELINE_SKILLS`` and has no preflight. It ships under the
framework-generic ``skills/`` tree, so ``aiadev install`` places it on
every platform's skills directory regardless of which preset is active
(mirrors every other framework skill, e.g. ``checklist``).

This test file covers two things:

- ``test_product_skill_frontmatter_validates``: the skill's frontmatter
  validates against both the external Agent Skills conformance schema
  and the internal aiadev pipeline schema (mirrors
  ``tests/test_skills_conformance.py``).
- ``test_product_skill_installed[<platform>]``: after
  ``aiadev install --preset lean --platform <p>``, the SKILL.md lands
  at that platform's skills directory.
"""

from __future__ import annotations

import json
import pathlib

import pytest
from click.testing import CliRunner
from jsonschema import Draft202012Validator

from aiadev.commands.install import install_command
from aiadev.validate import extract_frontmatter

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
PRODUCT_SKILL = REPO_ROOT / "skills" / "product" / "SKILL.md"

AGENT_SKILLS_SCHEMA = json.loads(
    (REPO_ROOT / "schemas" / "agent-skills.schema.json").read_text(encoding="utf-8")
)
SKILL_FRONTMATTER_SCHEMA = json.loads(
    (REPO_ROOT / "schemas" / "skill-frontmatter.schema.json").read_text(
        encoding="utf-8"
    )
)

PLATFORM_SKILL_PATHS = {
    "claude-code": pathlib.Path(".claude/skills/product/SKILL.md"),
    "cursor": pathlib.Path(".cursor/skills/product/SKILL.md"),
    "codex": pathlib.Path(".codex/skills/product/SKILL.md"),
    "opencode": pathlib.Path(".opencode/skills/product/SKILL.md"),
    "gemini": pathlib.Path(".gemini/skills/product/SKILL.md"),
}


def test_product_skill_frontmatter_validates() -> None:
    fm, error = extract_frontmatter(PRODUCT_SKILL)
    assert fm is not None, f"{PRODUCT_SKILL}: {error}"

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
            f"{PRODUCT_SKILL.relative_to(REPO_ROOT)} fails {schema_name}: {details}"
        )


@pytest.mark.parametrize(
    "platform", sorted(PLATFORM_SKILL_PATHS), ids=sorted(PLATFORM_SKILL_PATHS)
)
def test_product_skill_installed(
    platform: str,
    isolated_framework: pathlib.Path,
    tmp_path: pathlib.Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("AIADEV_ROOT", str(isolated_framework))
    project = tmp_path / "demo-project"
    project.mkdir()

    runner = CliRunner()
    result = runner.invoke(
        install_command,
        [
            "--project-root",
            str(project),
            "--preset",
            "lean",
            "--platform",
            platform,
            "--non-interactive",
            "--vars",
            "PROJECT_NAME=Demo",
        ],
    )
    assert result.exit_code == 0, result.output

    skill_path = project / PLATFORM_SKILL_PATHS[platform]
    assert skill_path.is_file(), (
        f"expected {skill_path} to exist after install; output:\n{result.output}"
    )
