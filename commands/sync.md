---
description: Re-sync framework/preset artifacts and regenerate the Detected Stack block in CLAUDE.md.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
argument-hint: "<optional: --dry-run | --force | --skip-stack | --skip-artifacts>"
---

Run `aiadev sync $ARGUMENTS` inside the project so the installer re-evaluates every tracked
artifact against the manifest and refreshes the `<!-- aiadev:auto-stack -->` block in
`CLAUDE.md` (or `AGENTS.md` / `GEMINI.md` depending on platform). Respect hand-edited
files — report conflicts instead of overwriting unless `--force` is passed.
