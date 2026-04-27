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


def test_spec_template_recon_block_documents_micro_format(
    framework_root: pathlib.Path,
) -> None:
    """The recon block in the template must include an example bullet
    matching the validator's recon_entry_pattern, so a copy-paste author
    has a known-passing starting shape."""
    template = (framework_root / "templates" / "spec-template.md").read_text(
        encoding="utf-8"
    )
    schema = json.loads(
        (framework_root / "schemas" / "spec-recon.schema.json").read_text(
            encoding="utf-8"
        )
    )
    entry_re = re.compile(schema["recon_entry_pattern"], re.MULTILINE)

    anchor_pos = template.find(ANCHOR)
    next_anchor = template.find("<!-- section:", anchor_pos + len(ANCHOR))
    block = template[anchor_pos:next_anchor]

    assert entry_re.search(block), (
        "recon block must contain at least one example bullet matching "
        f"recon_entry_pattern={schema['recon_entry_pattern']!r}"
    )
