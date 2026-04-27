"""Tests for the spec-reconnaissance validator (issue #26)."""
from __future__ import annotations

import json
import pathlib

from aiadev.validate import validate_spec

FIXTURES = pathlib.Path(__file__).parent / "fixtures" / "spec-recon"


def test_cutover_spec_id_pinned_at_ten(framework_root: pathlib.Path) -> None:
    """The cutover id is a load-bearing constant — pin it explicitly so an
    accidental bump cannot silently regrandfather every spec.

    Why a regression test: spec 0011's plan risk-table flagged an off-by-one
    where a wrong cutover would reject the very spec that introduces the rule.
    """
    schema_path = framework_root / "schemas" / "spec-recon.schema.json"
    data = json.loads(schema_path.read_text(encoding="utf-8"))

    assert data["cutover_spec_id"] == 10
    assert isinstance(data["recon_entry_pattern"], str)
    assert isinstance(data["opt_out_pattern"], str)


def test_grandfathered_spec_passes_without_recon(framework_root: pathlib.Path) -> None:
    """Spec ID at-or-below the cutover is grandfathered: no recon required."""
    report = validate_spec(FIXTURES / "legacy-spec-0009.md", root=framework_root)
    assert report.ok, report.as_lines()


def test_empty_recon_section_exits_nonzero(framework_root: pathlib.Path) -> None:
    """Spec past the cutover with an empty recon block must fail with the
    actionable message named in spec Story 2 scenario 1."""
    report = validate_spec(FIXTURES / "empty-recon.md", root=framework_root)
    assert not report.ok
    assert any(
        "Reconnaissance section required" in issue.message for issue in report.failed
    ), report.as_lines()


def test_optout_line_passes_validation(framework_root: pathlib.Path) -> None:
    """A single-surface opt-out line satisfies the recon rule."""
    report = validate_spec(FIXTURES / "optout-recon.md", root=framework_root)
    assert report.ok, report.as_lines()


def test_prose_only_recon_fails_validation(framework_root: pathlib.Path) -> None:
    """Recon body with prose but no bulleted file-path entries must fail
    with the message named in spec Story 2 scenario 3."""
    report = validate_spec(FIXTURES / "prose-only-recon.md", root=framework_root)
    assert not report.ok
    assert any(
        "Reconnaissance entries must cite at least one file path" in issue.message
        for issue in report.failed
    ), report.as_lines()
