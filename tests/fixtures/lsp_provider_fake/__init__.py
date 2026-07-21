"""A second fake provider — LSP-backed — conforming to the spec-0017 contract.

Spec 0019 proves the ``graph-provider.schema.json`` contract is
provider-agnostic: this fake maps Language Server Protocol operations onto the
same three queries, returning responses that validate against the **unchanged**
0017 schema.

Query → LSP operation mapping (see
``specs/0019-lsp-graph-provider/contracts/lsp-provider-mapping.md``):

- ``impact``     → ``textDocument/references`` + ``callHierarchy/incomingCalls``
- ``drift``      → ``textDocument/documentSymbol`` / ``workspace/symbol``
- ``provenance`` → ``textDocument/definition`` (resolved ⇒ ``explicit``)

Confidence: a reference/definition the language server **resolves** is
``explicit``; a textual/heuristic match is ``inferred``; multiple candidate
definitions are ``ambiguous`` — reusing the vocabulary in
``presets/knowledge-graph/rules/graph-facts.md``.
"""
from __future__ import annotations

from typing import Any


def impact(paths: list[str]) -> dict[str, Any]:
    """Blast-radius via LSP references + incoming call hierarchy."""
    return {
        "subsystems": [
            {
                "name": "cli",
                "edges": [
                    {
                        "symbol": f"{path}:main",
                        "subsystem": "cli",
                        "confidence": "explicit",
                        "provider_label": "lsp:resolved-reference",
                    }
                    for path in paths
                ],
            }
        ]
    }


def drift(tasks: list[str], diff_paths: list[str]) -> dict[str, Any]:
    """Task-without-code / code-without-task via LSP document/workspace symbols."""
    return {
        "missing": [
            {
                "symbol": "src/aiadev/pending.py:do_work",
                "subsystem": "core",
                "confidence": "explicit",
                "provider_label": "lsp:workspace-symbol",
            }
        ],
        "extra": [
            {
                "symbol": f"{path}:unknown",
                "subsystem": "core",
                "confidence": "inferred",
                "provider_label": "lsp:textual-match",
            }
            for path in diff_paths
        ],
    }


def provenance(symbol: str, *, resolved: bool = True, candidates: int = 1) -> dict[str, Any]:
    """Confidence + LSP-native label behind a single fact.

    Models ``textDocument/definition``:

    - uniquely resolved (``resolved`` and ``candidates == 1``) ⇒ ``explicit``;
    - multiple candidate definitions (``candidates > 1``) ⇒ ``ambiguous``;
    - not resolved (textual match only) ⇒ ``inferred``.
    """
    if resolved and candidates == 1:
        confidence, label = "explicit", "lsp:resolved-definition"
    elif candidates > 1:
        confidence, label = "ambiguous", "lsp:multiple-candidates"
    else:
        confidence, label = "inferred", "lsp:textual-match"
    return {
        "symbol": symbol,
        "subsystem": "cli",
        "confidence": confidence,
        "provider_label": label,
    }
