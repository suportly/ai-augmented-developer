# `knowledge-graph` preset (opt-in)

An **opt-in** preset that wires an optional knowledge-graph context provider
into the pipeline. When enabled, the `analyze` skill grounds its drift gaps
in facts the provider returns (`arquivo:símbolo` with a confidence label)
instead of inference alone. See `specs/0017-knowledge-graph-context-provider/`
for the full spec, and `rules/graph-facts.md` for how facts are cited.

This preset ships **nothing mandatory**: no existing preset gains a
dependency, and `analyze` degrades to its provider-free behaviour whenever
the provider is absent.

## What it declares

`mcps.yaml` declares one MCP server — `graphify`, the reference
implementation behind the provider contract
(`specs/0017-.../contracts/graph-provider.schema.json`). Any provider that
satisfies that contract can be substituted.

## Enabling it (on demand)

```bash
aiadev install --preset knowledge-graph
```

You must install the provider yourself (it is not bundled):

```bash
pip install graphifyy   # provides the `graphify` CLI / --mcp server
```

## Privacy

- **Local by default.** The provider parses your code locally with a
  deterministic AST; your code does **not** leave your machine.
- **LLM backend is opt-in.** A remote LLM backend is only used if *you*
  configure one (for docs/PDFs/images). Until you do, nothing is sent to a
  third party. This mirrors Article VI (Privacy by design).
