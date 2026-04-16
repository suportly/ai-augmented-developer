"""Tests for the cl-N marker grammar validator (T001).

Imports validate_skills via importlib so scripts/ does not need to be a
package. This avoids adding __init__.py to a directory that currently has
none and keeps the import explicit.
"""
from __future__ import annotations

import importlib.util
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location(
    "validate_skills",
    ROOT / "scripts" / "validate_skills.py",
)
_mod = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
sys.modules["validate_skills"] = _mod
_spec.loader.exec_module(_mod)  # type: ignore[union-attr]

check_markers = _mod.check_markers


def test_validator_accepts_cl_n_grammar() -> None:
    """check_markers returns no errors for valid [NEEDS CLARIFICATION:cl-N …] markers."""
    text = (
        "Some spec text.\n"
        "[NEEDS CLARIFICATION:cl-1 What is the expected response shape?]\n"
        "More text.\n"
        "[NEEDS CLARIFICATION:cl-2 Should pagination be cursor-based?]\n"
        "[NEEDS CLARIFICATION:cl-42 Is zero a valid id here?]\n"
    )
    errors = check_markers(text)
    assert errors == [], f"Expected no errors for valid markers but got: {errors}"
