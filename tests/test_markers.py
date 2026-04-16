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
    result = check_markers(text)
    assert result["errors"] == [], f"Expected no errors for valid markers but got: {result['errors']}"
    assert result["warnings"] == [], f"Expected no warnings for valid markers but got: {result['warnings']}"


def test_validator_rejects_malformed_ids() -> None:
    """check_markers flags malformed cl-N forms as errors."""
    cases = {
        # Zero-padding is forbidden.
        "zero_padded": "[NEEDS CLARIFICATION:cl-001 zero-padded id]",
        # Decimal ids are forbidden.
        "decimal": "[NEEDS CLARIFICATION:cl-1.2 decimal id]",
    }
    for label, token in cases.items():
        result = check_markers(token)
        assert result["errors"], f"Expected an error for {label} ({token!r}) but got none"
        assert any(token in err for err in result["errors"]), (
            f"Error message for {label} should reference the offending token; got {result['errors']}"
        )
        assert result["warnings"] == [], f"{label} must not appear as a warning; got {result['warnings']}"


def test_validator_tolerates_legacy_with_warning() -> None:
    """Legacy [NEEDS CLARIFICATION: ...] (no cl-N) is a warning, not an error.

    Specs created before T001 have markers without the cl-N id. The validator
    must accept them with a back-compat warning so the 7 existing
    specs/feature-*/spec.md continue to validate.
    """
    legacy = "[NEEDS CLARIFICATION: pergunta legacy sem id]"
    result = check_markers(legacy)

    assert result["errors"] == [], (
        f"Legacy marker must NOT be reported as an error; got {result['errors']}"
    )
    assert result["warnings"], "Legacy marker must produce a warning"
    assert any(legacy in w for w in result["warnings"]), (
        f"Warning message should reference the offending token; got {result['warnings']}"
    )
