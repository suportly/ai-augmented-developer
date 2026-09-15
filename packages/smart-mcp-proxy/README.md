# smart-mcp-proxy

Runs shell commands and, when the output is too long, condenses it with a
local Ollama model before it reaches the agent. Cuts token cost and context
pollution from noisy builds, test runs and logs. Three entry points share one
core:

| Binary | What it is |
| --- | --- |
| `smart-mcp-proxy` | MCP server (stdio) exposing `smart_bash_execute` and `smart_git_diff`. |
| `smart-bash` | CLI: `smart-bash -c "<cmd>"` runs the command and prints condensed output, exit code preserved. |
| `smart-bash-hook` | Claude Code `PreToolUse` hook that routes the **native Bash tool** through `smart-bash`, so the economy is automatic. |

## Hook (recommended)

Add to `.claude/settings.json` (project or `~/.claude`):

```json
{ "hooks": { "PreToolUse": [ { "matcher": "Bash",
  "hooks": [ { "type": "command", "command": "smart-bash-hook", "timeout": 10 } ] } ] } }
```

Every Bash call is rewritten to `smart-bash --b64 <command>`. Short output comes
back byte-for-byte; long output comes back condensed, with a short echo of the
command on the first line. Output that would not get smaller by condensing
(typically just above the budget) is passed through untouched. Background calls
are skipped, the rewrite is idempotent, and
if the hook fails it does nothing (exit 0, no output), so it can never block
Bash. Use `node /abs/path/dist/hook.js` as the command when the package is not
on `PATH`.

**Codex CLI** (hooks in `.codex/hooks.json`, same payload and matcher) applies
a rewrite only together with `permissionDecision: "allow"`, so register it as
`smart-bash-hook --allow`. Never add `--allow` under Claude Code unless you
want every Bash call auto-approved. Not yet exercised against a live Codex
session; unit-tested for the output shape only.

## Tools

`smart_git_diff` — `range` (default `HEAD`; `--staged` for the index), optional
`paths`, `cwd`. Returns `git diff --stat` verbatim, then 1-3 bullets per file
from the local model. Files beyond the input budget (24k chars) are listed
without a summary; without Ollama, all of them are.

`smart_bash_execute`

| Param | Type | Description |
| --- | --- | --- |
| `command` | string | Shell command to run. |
| `cwd` | string? | Working directory (defaults to the server's cwd). |
| `force_raw` | boolean? | Skip summarization; return the (head/tail-clipped) raw output. |
| `raw_id` | string? | Return the cached raw output of a previous call (id from its header) without re-running anything. |

Behavior:

1. Runs the command with `child_process.exec`.
2. If `stdout + stderr` ≤ `SMART_MCP_MAX_CHARS` (default 2000), returns it verbatim.
3. Otherwise POSTs to `${OLLAMA_URL}/api/generate` with a triage prompt
   (root error, clean stack trace, final result only).
4. If Ollama is offline or fails, returns a truncated head/tail excerpt with a warning.

Summarized responses have a fixed shape so the agent can rely on it:

```text
[smart-mcp-proxy] Output was 18142 chars / 405 lines; condensed by qwen2.5-coder:3b. ...

ERRORS:
<root error + project stack frames, verbatim>
RESULT:
<final summary lines, verbatim>

ERROR SIGNATURES (deterministic grep of error-like lines; N distinct):
E   ModuleNotFoundError: No module named 'aiadev'   (x49)

RAW TAIL (last 8 lines, verbatim):
<...>

[exit code: 1]
```

The `ERROR SIGNATURES` block (a deterministic grep of error-like lines,
deduplicated with counts) and the raw tail are appended by the server, so exit summaries
(test counts, build status) survive even when the small model drops them.
If the model's summary is not shorter than a plain excerpt, the excerpt is
returned instead.

Measured against Claude Code's native Bash with `claude-opus-5` as the agent:
85% fewer characters returned by the tool, 44% lower cost, same root-cause
accuracy (6/6). Full method, numbers and caveats in [BENCHMARK.md](./BENCHMARK.md).

## Setup

```bash
cd packages/smart-mcp-proxy
npm install
npm run build          # or: npm test (builds, then runs the node --test suite)
npm install -g .       # puts smart-mcp-proxy, smart-bash and smart-bash-hook on PATH
ollama pull qwen2.5-coder:3b   # once
```

The package is not on the npm registry yet; the global install from the
folder is what makes the `command: "smart-mcp-proxy"` declared by the
`token-economy` preset (and the `smart-bash-hook` command in the hook
snippets) resolve. Without it, point the MCP `command` at
`node /abs/path/dist/index.js` and the hook at `node /abs/path/dist/hook.js`.

Inside the ai-augmented-developer framework, the opt-in `token-economy` preset
(`aiadev install --preset token-economy`) declares the MCP server and ships the
hook snippet; `aiadev metrics --tokens` measures the effect per session.

## Configuration

| Variable | Default |
| --- | --- |
| `OLLAMA_URL` | `http://localhost:11434` |
| `OLLAMA_MODEL` | `qwen2.5-coder:3b` |
| `OLLAMA_TIMEOUT_MS` | `60000` |
| `SMART_MCP_MAX_CHARS` | `2000` |
| `SMART_MCP_EXEC_TIMEOUT_MS` | `300000` |
| `SMART_MCP_MAX_BUFFER` | `52428800` |

## Registering with Claude Code

Add to `mcps.yaml` (or directly to `.mcp.json`):

```yaml
servers:
  smart-bash:
    command: "node"
    args: ["packages/smart-mcp-proxy/dist/index.js"]
    env:
      OLLAMA_MODEL: "qwen2.5-coder:3b"
```
