# LSP → graph-provider contract mapping

How a Language Server Protocol (LSP) backend satisfies the knowledge-graph
provider contract defined in
[`specs/0017-.../contracts/graph-provider.schema.json`](../../0017-knowledge-graph-context-provider/contracts/graph-provider.schema.json).
This proves the contract is **provider-agnostic**: graphify is one reference
implementation, an LSP-backed provider is another. Idea from
`Piebald-AI/claude-code-lsps`.

> **Non-goal / fora de escopo.** This document does **not** specify a runnable
> LSP→MCP adapter (a real server). Building the provider is a provider author's
> job, not the framework's (Article III). aiadev proves conformance (via
> `tests/fixtures/lsp_provider_fake/`) and documents the mapping.

## Query → LSP operation

| Contract query | LSP operation(s) | How it satisfies the query |
|---|---|---|
| `impact(paths)` | `textDocument/references` + `callHierarchy/incomingCalls` | For each changed symbol, the references and incoming calls are the edges to the subsystems that depend on it (blast-radius). |
| `drift(tasks, diff_paths)` | `textDocument/documentSymbol` + `workspace/symbol` | Symbols a done task claimed but absent from the diff → `missing`; symbols present in changed files that no task requested → `extra`. |
| `provenance(symbol)` | `textDocument/definition` | Whether the language server uniquely resolves the symbol's definition (see the confidence mapping in the next task). |

Every fact still cites a verifiable `path:symbol`, exactly as the contract
requires, so a reader can check it against the code even if the index is stale.
