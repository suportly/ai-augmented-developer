---
name: find-skills
description: Find installable agent skills for a requested capability. Recommend only; install nothing unasked.
metadata:
  aiadev:
    version: 0.1.0
    inputs:
    - type: text
      description: What the user wants to be able to do.
    outputs:
    - type: text
      description: Vetted skill recommendations with the install command, or a clear "none found".
    requires: []
    handoffs: []
---

# Find Skills

Discover installable skills with the external `npx skills` CLI and recommend them. You only recommend; the user decides.

## When to use

- The user asks "is there a skill for X?", "find a skill for X", or how to extend your capabilities.
- The task is specialized and an existing skill may cover it.

## Steps

1. **Understand the need.** Name the domain and the task in a few words.
2. **Search.** Run `npx skills find <terms>`. Use generic domain terms only. Never put client names, paths, secrets or code snippets in the query.
3. **Verify** each candidate before recommending it:
   - Prefer 1,000 installs or more. Distrust fewer than 100 installs.
   - Be skeptical of a source repository with fewer than 100 stars.
   - If a figure could not be confirmed, say so explicitly instead of guessing.
4. **Inspect.** Read the candidate's `SKILL.md` and flag any network commands, writes outside the project, or package installs.
5. **Present** each option: name, what it does, source, and the command `npx skills add <source>`.
6. **Install only after the user confirms.** Show the command; the user runs it. Never add `-y`/`--yes` or any flag that skips the confirmation prompt.

## Fallbacks

- Nothing found: say so and offer to do the task directly.
- No network or CLI: say you could not search and continue without the skill.
