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
