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
| --- | --- | --- |
| [`rtk-ai/rtk`](https://github.com/rtk-ai/rtk) | Single Rust binary that filters/compresses command output (`git status`, `pytest`, `docker ps`, …). | Ships a `PreToolUse` hook that auto-rewrites commands (e.g. `git status` → `rtk git status`), so adoption is transparent. |
| [`headroomlabs-ai/headroom`](https://github.com/headroomlabs-ai/headroom) | Content-aware compression layer (JSON / code / prose), runnable as a library, HTTP proxy, or MCP server; reversible (originals cached). | Wraps an agent or runs as a proxy/MCP the agent reads through. |
| [`@aiadev/smart-mcp-proxy`](../packages/smart-mcp-proxy/) (this repo, separate npm package) | MCP server + `smart-bash` CLI + `smart-bash-hook` PreToolUse hook. Output over 2000 chars is condensed by a **local Ollama model** to root errors and final results, with deterministic `ERROR SIGNATURES` and `RAW TAIL` blocks appended; degrades to truncated excerpts without Ollama. | Declared by the opt-in [`token-economy` preset](../presets/token-economy/). Benchmarked headless against native Bash: 85% fewer chars, 44% lower cost, same accuracy ([BENCHMARK.md](../packages/smart-mcp-proxy/BENCHMARK.md)). Lives outside `src/aiadev`, so the Non-goal above still holds. |

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

## Example: a `PreToolUse` hook

A `PreToolUse` hook (in your project's `.claude/settings.json`) can route a
command's output through a compressor before it reaches context. This is an
**illustrative** example — the framework ships no such hook; you install the
compressor and add the hook yourself (see the Non-goal above).

```jsonc
// .claude/settings.json (consumer-owned; example only)
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": "rtk hook pretooluse" }
        ]
      }
    ]
  }
}
```

With `rtk` installed, this rewrites noisy commands (e.g. `git status`) through
`rtk` transparently. A `headroom` proxy/MCP is the alternative for content-aware
compression. Either way the compressor runs locally and stays consumer-wired —
the framework only documents the shape.

The same shape works with `smart-bash-hook` from `@aiadev/smart-mcp-proxy`
(spec 0022). The ready-to-paste snippet ships with the `token-economy` preset
at `presets/token-economy/hooks/claude-code-settings.snippet.json`:

```jsonc
// .claude/settings.json (consumer-owned; copy from the preset)
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": "smart-bash-hook", "timeout": 10 }
        ]
      }
    ]
  }
}
```

The hook rewrites every Bash `command` to `smart-bash --b64 <command>`; the CLI
runs the original command, prints short output byte-for-byte and condenses long
output, always propagating the exit code. `aiadev install` still does not write
`settings.json` — that merge is a follow-up of spec 0022 — so this remains one
manual step. To see whether it pays in your project, compare
`aiadev metrics --tokens` (tokens per session, characters returned per tool,
read from the local Claude Code transcripts) before and after enabling it.
