# smart-mcp-proxy

MCP server that runs shell commands and, when the output is too long,
condenses it with a local Ollama model before returning it to the agent.
Cuts token cost and context pollution from noisy builds, test runs and logs.

## Tool

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
npm run build
ollama pull qwen2.5-coder:3b   # once
```

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
