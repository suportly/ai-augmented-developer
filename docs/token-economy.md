# Token economy: optional output compression

The [`token-economy` checklist category](../templates/checklist-template.md) is
a **review lens** for context bloat. This doc is the **optional integration
path**: how to actually shrink tool output before it reaches the agent's
context, using an **external** compressor.

> **Non-goal / fora de escopo.** aiadev does **not** implement a token
> compressor. `rtk` and `headroom` are dedicated tools; reimplementing that
> inside the framework would violate Article III (Simplicity). This doc
> documents how to wire one — the framework ships no compressor and adds no
> dependency.

## What this complements

- **`terse-mode` (spec 0009)** already compresses **reviewer output** (one line
  per finding). It is orthogonal to this doc, which is about **tool output**
  (test logs, `git status`, build output) entering context.
- The checklist category is the lens; this doc is the tool path.

## External compressors

| Tool | Shape | Notes |
|---|---|---|
| [`rtk-ai/rtk`](https://github.com/rtk-ai/rtk) | Single Rust binary that filters/compresses command output (`git status`, `pytest`, `docker ps`, …). | Ships a `PreToolUse` hook that auto-rewrites commands (e.g. `git status` → `rtk git status`), so adoption is transparent. |
| [`headroomlabs-ai/headroom`](https://github.com/headroomlabs-ai/headroom) | Content-aware compression layer (JSON / code / prose), runnable as a library, HTTP proxy, or MCP server; reversible (originals cached). | Wraps an agent or runs as a proxy/MCP the agent reads through. |

## How to wire one (mechanism)

Two mechanisms, both **opt-in** and installed by the consumer, not the
framework:

1. **`PreToolUse` hook** — a Claude Code hook that rewrites or pipes a command's
   output through the compressor before it lands in context. This is how `rtk`
   integrates (`rtk init`). The hook lives in the consumer's `settings.json`;
   aiadev does not install it.
2. **MCP server** — run the compressor as an MCP server (e.g. `headroom` MCP)
   and let the agent read through it. Declare it in your project's MCP config
   (aiadev's `mcps.yaml` translates one declaration to each platform's native
   config) — the same opt-in mechanism the `knowledge-graph` preset uses.

Whichever you pick: the compressor runs locally, and the decision to send any
output to a remote backend is the consumer's.

## Fast-follow

A ready-made, commented `PreToolUse` hook example (and/or an opt-in preset that
declares a compressor MCP) is a documented follow-up — this v1 is descriptive
so the framework stays compressor-agnostic.
