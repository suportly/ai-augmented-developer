"""T010 — `product` skill registered in the pipeline generator and CLAUDE.md.

`product` runs once per project (bootstrap/update of specs/_product/) before
`specify` ever fires, so it must lead PIPELINE and the CLAUDE.md "Skill to
invoke" table's first row — without breaking the CLAUDE.md/pipeline-reference
drift guard in tests/test_pipeline_reference_drift.py.
"""

from __future__ import annotations

import pathlib
import re

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "scripts" / "generate_pipeline_reference.py"
REFERENCE = ROOT / "docs" / "pipeline-reference.md"

CLAUDE_TABLE_RE = re.compile(r"^\|.*\|\s*`product`\s*\|\s*$", re.MULTILINE)


def test_pipeline_lists_product_before_specify():
    text = GENERATOR.read_text(encoding="utf-8")
    match = re.search(r"PIPELINE:\s*tuple\[str, \.\.\.\]\s*=\s*\((.*?)\)", text, re.DOTALL)
    assert match, "expected a PIPELINE tuple literal in the generator"
    names = re.findall(r'"([a-z][a-z0-9-]*)"', match.group(1))
    assert "product" in names, "PIPELINE must include 'product'"
    assert names.index("product") < names.index("specify"), (
        "'product' must precede 'specify' in PIPELINE"
    )

    assert REFERENCE.exists(), "docs/pipeline-reference.md must be committed"
    ref_body = REFERENCE.read_text(encoding="utf-8")
    assert "`/aia:product`" in ref_body


def test_claude_md_table_has_product(framework_root: pathlib.Path):
    claude_md = (framework_root / "CLAUDE.md").read_text(encoding="utf-8")
    match = CLAUDE_TABLE_RE.search(claude_md)
    assert match, "expected a CLAUDE.md table row with `product` in the skill column"
    row = match.group(0)
    assert "specs/_product/" in row, (
        "the `product` row must mention specs/_product/ as its condition"
    )


# T011 — `product` must also be listed in every remaining registry that
# enumerates skills by name: the agent-file
# template's stage table, the lean preset's pipeline line, the slash-commands
# rule, and the README.
REGISTRY_FILES = (
    "templates/agent-file-template.md",
    "presets/lean/CLAUDE.md",
    "rules/slash-commands.md",
    "README.md",
)


@pytest.mark.parametrize("relative_path", REGISTRY_FILES)
def test_product_listed_in_every_registry(framework_root: pathlib.Path, relative_path: str):
    text = (framework_root / relative_path).read_text(encoding="utf-8")
    if relative_path == "rules/slash-commands.md":
        assert "`/aia:product`" in text
    elif relative_path == "presets/lean/CLAUDE.md":
        assert "product → specify" in text
    elif relative_path == "README.md":
        # README's pipeline bullets and workflow list bold skill names
        # (`**specify**`, ...) rather than backtick-code them.
        assert "0. **product**" in text, "The Basic Workflow must list product"
        assert "- **product**" in text, "What's Inside must list product"
    else:
        assert "`product`" in text
