#!/usr/bin/env node
/**
 * Smart MCP Proxy — MCP server entry point.
 *
 * Tools:
 *   smart_bash_execute  run a shell command; long output is condensed (see core.ts)
 *   smart_git_diff      git diff --stat verbatim + one local-model summary per file
 *
 * The condensation logic lives in core.ts and is shared with the
 * `smart-bash` CLI and the `smart-bash-hook` PreToolUse hook.
 */

import { z } from "zod";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CONFIG,
  RAW_RETURN_CAP,
  RawCache,
  combineOutput,
  condense,
  headTail,
  renderDiffSummary,
  runCommand,
  statusLine,
  summarizeDiff,
} from "./core.js";

const rawCache = new RawCache(20);

const server = new McpServer({
  name: "ai-augmented-dev-smart-mcp",
  version: "0.2.0",
});

server.tool(
  "smart_bash_execute",
  [
    "Run a shell command and return its output.",
    `If stdout+stderr exceed ${CONFIG.maxChars} characters, the output is condensed: ` +
      (CONFIG.deterministic
        ? "error lines extracted verbatim (with file:line) plus a head/tail excerpt."
        : `by the local Ollama model (${CONFIG.ollamaModel}) down to root errors, clean stack traces and final results.`),
    "Use it for noisy commands (test suites, builds, installs, long logs) to protect the context window.",
    "Condensed responses copy error lines verbatim and append a deterministic ERROR SIGNATURES block and the raw tail;",
    "treat them as sufficient for root-cause answers. Only if something essential is missing, pass raw_id (from the header)",
    "to read the cached raw output without re-running the command.",
  ].join(" "),
  {
    command: z.string().min(1).describe("The shell command to execute."),
    cwd: z.string().optional().describe("Working directory for the command. Defaults to the server's cwd."),
    force_raw: z
      .boolean()
      .optional()
      .describe("If true, skip summarization and return the raw output even when it is long (it will still be truncated at the input cap)."),
    raw_id: z
      .string()
      .optional()
      .describe("Return the cached raw output of a previous call (id from its response header) WITHOUT re-running any command. `command` is ignored when set."),
  },
  async ({ command, cwd, force_raw, raw_id }) => {
    if (raw_id) {
      const cached = rawCache.get(raw_id);
      if (!cached) {
        return { isError: true, content: [{ type: "text", text: `[smart-mcp-proxy] no cached output for raw_id=${raw_id} (cache keeps the last 20 calls).` }] };
      }
      const header = `[smart-mcp-proxy] cached raw output of: ${cached.command} (${cached.output.length} chars)`;
      return { isError: false, content: [{ type: "text", text: `${header}\n\n${headTail(cached.output, RAW_RETURN_CAP)}\n\n${cached.status}` }] };
    }

    const result = await runCommand(command, cwd);
    const output = combineOutput(result);
    const status = statusLine(result);
    const isError = result.exitCode !== 0;

    if (force_raw && output.length > CONFIG.maxChars) {
      return { isError, content: [{ type: "text", text: `${headTail(output, RAW_RETURN_CAP)}\n${status}` }] };
    }

    const c = await condense(command, output, status, rawCache, status.length + 2);
    const text = c.mode === "verbatim" ? (output ? `${output}\n${status}` : status) : `${c.text}\n\n${status}`;
    return { isError, content: [{ type: "text", text }] };
  },
);

server.tool(
  "smart_git_diff",
  [
    "Summarize a git diff for review: returns `git diff --stat` verbatim (deterministic) followed by 1-3 bullets per file",
    (CONFIG.deterministic
      ? "(bullets need SMART_MCP_MODE=model; in the default deterministic mode every file is listed without a summary)."
      : `written by the local Ollama model (${CONFIG.ollamaModel}). Files beyond the input budget are listed without a summary.`),
    "Use it before reading a full diff; read specific files afterwards only where the summary is not enough.",
  ].join(" "),
  {
    range: z.string().default("HEAD").describe("Revision range as accepted by git diff, e.g. 'HEAD', 'HEAD~3', 'main...HEAD'. Use '--staged' for the index."),
    paths: z.array(z.string()).optional().describe("Optional pathspecs to limit the diff."),
    cwd: z.string().optional().describe("Repository directory. Defaults to the server's cwd."),
  },
  async ({ range, paths, cwd }) => {
    const pathArgs = paths?.length ? ` -- ${paths.map((p) => `'${p.replace(/'/g, "'\\''")}'`).join(" ")}` : "";
    const rangeArg = range === "--staged" ? "--staged" : `'${range.replace(/'/g, "'\\''")}'`;
    const stat = await runCommand(`git --no-pager diff --stat=120 ${rangeArg}${pathArgs}`, cwd);
    if (stat.exitCode !== 0) {
      return { isError: true, content: [{ type: "text", text: `[smart-mcp-proxy] git diff failed:\n${combineOutput(stat)}` }] };
    }
    if (!stat.stdout.trim()) {
      return { isError: false, content: [{ type: "text", text: `[smart-mcp-proxy] git diff ${range}: no changes.` }] };
    }
    const diff = await runCommand(`git --no-pager diff --no-color ${rangeArg}${pathArgs}`, cwd);
    const summary = await summarizeDiff(diff.stdout, stat.stdout);
    return { isError: false, content: [{ type: "text", text: renderDiffSummary(range, summary) }] };
  },
);

async function main(): Promise<void> {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  // stdout is the MCP channel; diagnostics must go to stderr.
  console.error(
    `[smart-mcp-proxy] ready — mode=${CONFIG.deterministic ? "deterministic" : `model (${CONFIG.ollamaModel} @ ${CONFIG.ollamaUrl})`} maxChars=${CONFIG.maxChars}`,
  );
}

main().catch((error) => {
  console.error("[smart-mcp-proxy] fatal:", error);
  process.exit(1);
});
