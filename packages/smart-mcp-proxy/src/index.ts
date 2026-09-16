#!/usr/bin/env node
/**
 * Smart MCP Proxy — MCP server entry point.
 *
 * Tools:
 *   smart_bash_execute  run a shell command; long output is condensed (see core.ts)
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
  runCommand,
  statusLine,
} from "./core.js";

const rawCache = new RawCache(20);

const server = new McpServer({
  name: "ai-augmented-dev-smart-mcp",
  version: "0.4.0",
});

server.tool(
  "smart_bash_execute",
  [
    "Run a shell command and return its output.",
    `If stdout+stderr exceed ${CONFIG.maxChars} characters, the output is condensed: error lines are extracted`,
    "verbatim with the nearest project file:line, followed by a head/tail excerpt. Nothing is rewritten or summarized,",
    "so every byte comes from the command itself. Use it for noisy commands (test suites, builds, installs, long logs)",
    "to protect the context window. If something essential is missing, pass raw_id (from the header) to read the cached",
    "raw output without re-running the command.",
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

async function main(): Promise<void> {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  // stdout is the MCP channel; diagnostics must go to stderr.
  console.error(
    `[smart-mcp-proxy] ready — deterministic, maxChars=${CONFIG.maxChars}`,
  );
}

main().catch((error) => {
  console.error("[smart-mcp-proxy] fatal:", error);
  process.exit(1);
});
