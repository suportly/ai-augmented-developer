"""Coverage tests for ``aiadev.preflight``.

Asserts that the pipeline skill list, the section-anchor lists, and the
SKILL.md hand-off documentation stay in sync. See plan ADR #2 and
``test_preflight.py`` for the per-scenario behaviour.
"""
from __future__ import annotations

import pathlib

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_every_pipeline_skill_has_a_skill_directory() -> None:
    from aiadev.preflight import PIPELINE_SKILLS

    skills_dir = REPO_ROOT / "skills"
    for skill in PIPELINE_SKILLS:
        assert (skills_dir / skill / "SKILL.md").is_file(), (
            f"PIPELINE_SKILLS lists {skill!r} but skills/{skill}/SKILL.md is missing"
        )


@pytest.mark.parametrize(
    ("anchors_attr", "template_name"),
    [
        ("SPEC_ANCHORS", "spec-template.md"),
        ("PLAN_ANCHORS", "plan-template.md"),
        ("TASKS_ANCHORS", "tasks-template.md"),
    ],
)
def test_every_anchor_exists_in_its_template(
    anchors_attr: str, template_name: str
) -> None:
    import aiadev.preflight as mod

    anchors = getattr(mod, anchors_attr)
    template = (REPO_ROOT / "templates" / template_name).read_text(encoding="utf-8")
    missing = [a for a in anchors if f"<!-- section: {a} -->" not in template]
    assert not missing, (
        f"{anchors_attr} contains anchors not present in templates/{template_name}: "
        f"{missing}"
    )


def _read_skill(name: str) -> str:
    return (REPO_ROOT / "skills" / name / "SKILL.md").read_text(encoding="utf-8")


def test_clarify_skill_md_has_preflight_callout() -> None:
    assert "aiadev preflight clarify --feature" in _read_skill("clarify")
