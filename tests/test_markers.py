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


def test_validator_rejects_malformed_ids() -> None:
    """check_markers flags the three malformed forms documented in marker-format.md."""
    cases = {
        # Missing cl-N id (legacy form is handled by T003; here we test the
        # strict "cl-N or reject" gate so this token must be flagged).
        "no_id": "[NEEDS CLARIFICATION: pergunta sem id]",
        # Zero-padding is forbidden.
        "zero_padded": "[NEEDS CLARIFICATION:cl-001 zero-padded id]",
        # Decimal ids are forbidden.
        "decimal": "[NEEDS CLARIFICATION:cl-1.2 decimal id]",
    }
    for label, token in cases.items():
        errors = check_markers(token)
        assert errors, f"Expected an error for {label} ({token!r}) but got none"
        assert any(token in err for err in errors), (
            f"Error message for {label} should reference the offending token; got {errors}"
        )
