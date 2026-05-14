"""T015 — ``docs/customization.md`` documents the 3-tier TOML resolver.

Story 2 (sc2, sc3) requires consumer-facing documentation of the merge
rules implemented in ``src/aiadev/customization.py`` (T013). This test
asserts the structural sections that consumers must be able to find by
search and by scrolling: precedence, merge rules per shape, ≥ 3
worked examples (skill menu, agent ``principles[]``, scalar
``default_model``), file locations, and parse-error semantics.
"""

from pathlib import Path

DOC = Path(__file__).resolve().parents[1] / "docs" / "customization.md"


def _body() -> str:
    assert DOC.exists(), f"missing documentation file: {DOC}"
    return DOC.read_text(encoding="utf-8")


def test_doc_has_single_h1_at_top():
    body = _body()
    # Count only H1 lines outside fenced code blocks; TOML comments
    # inside ``` fences would otherwise be miscounted.
    in_fence = False
    h1_lines: list[str] = []
    for line in body.splitlines():
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if line.startswith("# "):
            h1_lines.append(line)
    assert len(h1_lines) == 1, (
        f"docs/customization.md must have exactly one H1, found {len(h1_lines)}"
    )


def test_doc_declares_layer_precedence_section():
    body = _body()
    assert "## Layer precedence" in body, (
        "docs/customization.md must contain '## Layer precedence'"
    )


def test_doc_declares_merge_rules_section_with_required_subsections():
    body = _body()
    assert "## Merge rules" in body, (
        "docs/customization.md must contain '## Merge rules'"
    )
    for subsection in (
        "### Scalars",
        "### Tables",
        "### Arrays of tables",
        "### Errors",
    ):
        assert subsection in body, (
            f"docs/customization.md must contain '{subsection}' under Merge rules"
        )


def test_doc_declares_examples_section_with_three_named_subsections():
    body = _body()
    assert "## Examples" in body, (
        "docs/customization.md must contain '## Examples'"
    )
    # Three distinct example sub-sections are required by Story 2 sc2/sc3.
    assert "default_model" in body, (
        "Examples must cover the scalar default_model override case"
    )
    assert "skill.menu" in body or "skill menu" in body, (
        "Examples must cover the skill menu override (array-of-tables by code)"
    )
    assert "principles" in body, (
        "Examples must cover the agent principles[] override case"
    )
    # At least three H3 sub-sections inside Examples.
    examples_block = body.split("## Examples", 1)[1].split("\n## ", 1)[0]
    h3_count = sum(1 for line in examples_block.splitlines() if line.startswith("### "))
    assert h3_count >= 3, (
        f"## Examples must have ≥ 3 named sub-sections, found {h3_count}"
    )


def test_doc_declares_file_locations_section():
    body = _body()
    assert "## File locations" in body, (
        "docs/customization.md must contain '## File locations'"
    )
    assert "_aiadev/team.toml" in body, (
        "File locations must mention _aiadev/team.toml"
    )
    assert "_aiadev/user.toml" in body, (
        "File locations must mention _aiadev/user.toml"
    )
    assert "gitignore" in body.lower(), (
        "File locations must note user.toml is gitignored"
    )


def test_doc_documents_parse_error_behavior():
    body = _body()
    # The Errors sub-section under Merge rules covers the abort path.
    errors_present = "### Errors" in body or "## Errors" in body
    assert errors_present, "docs/customization.md must document parse-error behavior"
    # Mention of file:line annotation surface.
    assert "file:line" in body or "<filename>:<line>" in body or ":<line>" in body, (
        "Errors section must describe the file:line diagnostic shape"
    )


def test_doc_ends_with_trailing_newline():
    raw = DOC.read_bytes()
    assert raw.endswith(b"\n"), "docs/customization.md must end with a newline"
