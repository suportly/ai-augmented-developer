"""Regression tests pinning the Reconnaissance section in spec-template.md (issue #26).

Why these tests exist: Success criterion 5 in spec 0011 requires that an
accidental removal of the recon anchor or its micro-format example fails CI.
"""
from __future__ import annotations

import json
import pathlib
import re

ANCHOR = "<!-- section: Reconnaissance -->"


def test_spec_template_has_reconnaissance_anchor(framework_root: pathlib.Path) -> None:
    template = (framework_root / "templates" / "spec-template.md").read_text(
        encoding="utf-8"
    )
    assert template.count(ANCHOR) == 1, (
        f"expected exactly one {ANCHOR} in spec-template.md"
    )
