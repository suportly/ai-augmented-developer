"""T003/T004 — the LSP→contract mapping document (spec 0019)."""
from pathlib import Path

DOC = (
    Path(__file__).resolve().parents[1]
    / "specs"
    / "0019-lsp-graph-provider"
    / "contracts"
    / "lsp-provider-mapping.md"
)


def test_mapping_doc_covers_the_three_queries() -> None:
    body = DOC.read_text(encoding="utf-8")
    assert "impact" in body and "drift" in body and "provenance" in body
    # names the LSP operations behind each query
    assert "textDocument/references" in body
    assert "callHierarchy" in body
    assert "textDocument/definition" in body
    # explicit non-goal: no executable adapter (Article III)
    lower = body.lower()
    assert "non-goal" in lower or "não-goal" in lower or "fora de escopo" in lower


def test_mapping_doc_defines_confidence_mapping() -> None:
    body = DOC.read_text(encoding="utf-8")
    assert "explicit" in body and "inferred" in body and "ambiguous" in body
    lower = body.lower()
    assert "resolv" in lower  # resolved definition → explicit
    assert "textual" in lower or "heur" in lower  # textual/heuristic → inferred
