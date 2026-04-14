---
# Minimal frontmatter schema for a command file.
# Used by Claude Code (via the plugin's `commands/` dir), Cursor, and Codex.
# Validated against `schemas/command-frontmatter.schema.json` (ships in phase 5).

name: {{COMMAND_NAME}}            # required, kebab-case, unique within the plugin
description: {{ONE_LINE}}         # required, ≤ 160 chars
version: 0.1.0                    # required, semver

# Optional: what this command hands off to. Enables UI-level "next step"
# buttons in clients that support it (Claude Code picks these up; others
# ignore them).
handoffs:
  - label: Human-readable next step
    agent: {{NEXT_SKILL_OR_AGENT_NAME}}
    prompt: >
      Opening prompt to seed the next skill.
    send: true                    # optional; `true` = auto-send, default = prompt the user first

# Optional: which skill this command is sugar for. If set, the body of
# this file should simply instruct the agent to invoke that skill. Plain
# wrappers without added value should not exist in v0.2+; prefer direct
# skill invocation. This field is here for the rare case where a command
# adds UX (for example, pre-filling a prompt from the clipboard).
invokes: {{SKILL_NAME_OR_OMIT}}
---

# {{COMMAND_TITLE}}

<!-- Short human description. The agent reads this when the command is
     invoked. One or two paragraphs is enough. -->

## What this does

...

## When not to use this

<!-- List the nearby commands/skills the user might have meant instead. -->

-

## Parameters

<!-- If the command takes arguments via $ARGUMENTS or similar, document
     them here. Otherwise delete this section. -->

-
