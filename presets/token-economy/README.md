# `token-economy` preset (opt-in)

An **opt-in** preset that wires the [`smart-mcp-proxy`](../../packages/smart-mcp-proxy/)
compressor into a project: long command output is condensed before it reaches
the agent (error lines verbatim with file:line plus a head/tail excerpt by
default; a **local** Ollama model with `SMART_MCP_MODE=model`), so test
suites, builds and linters stop flooding the context window. Spec:
[`specs/0022-smart-mcp-proxy-token-economy/`](../../specs/0022-smart-mcp-proxy-token-economy/).

This preset ships **nothing mandatory**: no other preset gains a dependency,
no model is required (the default mode is deterministic), and even in model
mode an absent Ollama degrades to the same excerpt plus `ERROR SIGNATURES`. The framework core still implements no
compressor (Article III); the compressor is a separate npm package this preset
merely declares.

## What it declares

- `mcps.yaml` — one MCP server, `smart-bash`, exposing `smart_bash_execute`
  (condensed command output, raw output cached per call) and `smart_git_diff`
  (`git diff --stat` verbatim + one summary per file).
- `hooks/claude-code-settings.snippet.json` — a Claude Code `PreToolUse` hook
  that routes the **native Bash tool** through the same condenser. This is what
  makes the economy automatic: the agent keeps using Bash and never has to pick
  a different tool. Measured with Claude Code headless (`claude-opus-5`): 85%
  fewer characters returned, 44% lower cost, same root-cause accuracy — see
  [`BENCHMARK.md`](../../packages/smart-mcp-proxy/BENCHMARK.md).

## Enabling it (on demand)

```bash
# 1. the compressor (not bundled; needs Node ≥ 18). Not on the npm registry yet:
#    build it from the framework repo and install the folder globally, which
#    puts smart-mcp-proxy, smart-bash and smart-bash-hook on your PATH.
git clone https://github.com/suportly/ai-augmented-developer.git
cd ai-augmented-developer/packages/smart-mcp-proxy && npm install && npm run build
npm install -g .
ollama pull qwen2.5-coder:3b                 # optional: only with SMART_MCP_MODE=model

# 2. the preset (declares the MCP server on every platform aiadev supports)
aiadev install --preset token-economy
```

## The hook (Claude Code only, one manual step)

`aiadev install` does not edit `.claude/settings.json` (it is a file you also
edit by hand; merging it is a follow-up of spec 0022). Copy the snippet into
the project's `.claude/settings.json` (or `~/.claude/settings.json` for every
project):

```json
{
  "hooks": {
    "PreToolUse": [
      { "matcher": "Bash",
        "hooks": [ { "type": "command", "command": "smart-bash-hook", "timeout": 10 } ] }
    ]
  }
}
```

If `smart-bash-hook` is not on the launcher's `PATH` (local build instead of a
global install), use `node /abs/path/packages/smart-mcp-proxy/dist/hook.js`
as the command.

What the hook does: for every Bash call it rewrites `command` to
`smart-bash --b64 <command>`; the CLI runs the original command, prints short
output byte-for-byte and condenses long output, always propagating the exit
code. It skips background calls and plain content dumps (`cat`, `head`,
`sed`, `jq`… — the agent wants that content, not a summary) and is
idempotent. If the hook itself fails
it does nothing, so a broken install can never block the Bash tool.

## Other platforms

The MCP server is platform-neutral: `aiadev install` translates `mcps.yaml`
into each platform's native config (Claude Code `.mcp.json`, Cursor
`.cursor/mcp.json`, Gemini CLI `.gemini/settings.json`, Codex
`.codex/config.toml`, OpenCode `opencode.json`), so `smart_bash_execute` and
`smart_git_diff` are available everywhere. The **automatic** path (the hook on
the native shell tool) depends on the platform having a rewriting hook:

| Platform | MCP tools | Native-shell hook |
| --- | --- | --- |
| Claude Code | yes | yes — `hooks/claude-code-settings.snippet.json` |
| Codex CLI (≥ 0.114, hooks on by default) | yes | yes — `hooks/codex-hooks.snippet.json` into `.codex/hooks.json`; **must** pass `--allow` |
| Cursor, Gemini CLI, OpenCode | yes | no rewriting hook today; ask the agent to prefer `smart_bash_execute` for noisy commands (AGENTS.md rule) |

Codex uses the same `PreToolUse` payload (`tool_name: "Bash"`,
`tool_input.command`) and the same `updatedInput` output, but only applies a
rewrite when the hook also returns `permissionDecision: "allow"`. That is what
`--allow` adds. Do **not** pass `--allow` under Claude Code unless you intend to
auto-approve every Bash call: there, `allow` skips the permission prompt. The
Codex hook was written against the Codex hooks reference and unit-tested for
its output shape; it has not yet been exercised against a live Codex session,
so treat it as beta and check `codex --version` supports hooks.

## Turning it off

- Remove the `PreToolUse` block from `settings.json` — the native Bash tool is
  back to raw output immediately.
- `aiadev uninstall --preset token-economy` removes the MCP declaration.

## Measuring whether it pays

`aiadev metrics --tokens` reads the Claude Code transcripts of the current
workspace (`~/.claude/projects/<slug>/`, read-only, counts only) and prints
tokens per session and characters returned per tool, so you can compare
sessions before and after enabling the preset.

## Privacy

Everything runs locally: the default mode needs no model at all, the optional
model is served by Ollama on `localhost`, the raw output cache lives in the
MCP server's memory, and `metrics --tokens` never prints message text. Pointing `OLLAMA_URL` at a remote host is a
consumer decision (Article VI).
