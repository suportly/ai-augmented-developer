# `token-economy` preset (opt-in)

An **opt-in** preset that wires the [`smart-mcp-proxy`](../../packages/smart-mcp-proxy/)
compressor into a project: long command output is condensed by a **local**
Ollama model before it reaches the agent, so test suites, builds and linters
stop flooding the context window. Spec:
[`specs/0022-smart-mcp-proxy-token-economy/`](../../specs/0022-smart-mcp-proxy-token-economy/).

This preset ships **nothing mandatory**: no other preset gains a dependency,
and when Ollama is absent every path degrades to a truncated excerpt plus the
deterministic `ERROR SIGNATURES` block. The framework core still implements no
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
# 1. the compressor (not bundled; needs Node ≥ 18)
npm install -g @aiadev/smart-mcp-proxy      # or: cd packages/smart-mcp-proxy && npm install && npm run build
ollama pull qwen2.5-coder:3b                 # any Ollama model works; set OLLAMA_MODEL

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
code. It skips background calls and is idempotent. If the hook itself fails
it does nothing, so a broken install can never block the Bash tool.

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

Everything runs locally: the model is served by Ollama on `localhost`, the
raw output cache lives in the MCP server's memory, and `metrics --tokens`
never prints message text. Pointing `OLLAMA_URL` at a remote host is a
consumer decision (Article VI).
