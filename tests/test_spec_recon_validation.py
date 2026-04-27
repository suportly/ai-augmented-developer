"""Tests for the spec-reconnaissance validator (issue #26)."""
from __future__ import annotations

import json
import pathlib

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
