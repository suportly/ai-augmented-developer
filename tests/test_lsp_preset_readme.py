"""T005 — the knowledge-graph preset README documents LSP as an alternative provider."""
from pathlib import Path

README = (
    Path(__file__).resolve().parents[1]
    / "presets"
    / "knowledge-graph"
    / "README.md"
)


def test_preset_readme_mentions_lsp_provider() -> None:
    body = README.read_text(encoding="utf-8")
    assert "LSP" in body
    # graphify stays the reference implementation
    assert "graphify" in body.lower()
    # links the mapping doc
    assert "lsp-provider-mapping.md" in body
