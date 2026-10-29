"""T008 (spec 0033, success criterion #1): CHANGELOG, README and CLAUDE.md mention the design step."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_unreleased_records_0033_design_step():
    body = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    section = body.split("## [Unreleased]", 1)[1].split("\n## [", 1)[0]
    assert "0033" in section and "/aia:design" in section
    for needle in ("**UI:**", "design.md", "not blocking", "`design`"):
        assert needle in section, needle


def test_readme_lists_the_design_skill():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "- **design** —" in readme and "/aia:design" in readme


def test_claude_md_table_stays_aligned_with_the_pipeline_reference():
    # The skill table in CLAUDE.md is checked against pipeline-reference.md, which is generated
    # from docs/pipeline-path.yaml; design is off the path by design, so it is not listed there.
    claude = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    assert "| `design` |" not in claude
