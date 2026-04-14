# Feature specification: Cursor platform handler

**Branch:** `feature/cursor-platform-handler`
**Created:** 2026-04-14
**Status:** Draft
**Spec ID:** 0002

---

## Problem

`aiadev install --platform cursor` is listed in the CLI's choices but no handler exists — the only wired platform in v0.3 is Claude Code. Cursor users who want presets installed into their project cannot use the CLI.

## Users and stakeholders

- Developers using Cursor as their primary agent IDE.
- Framework maintainers — adding a second platform validates the platform abstraction from v0.3.

## Success criteria

- `aiadev install --preset lean --platform cursor --non-interactive --vars PROJECT_NAME=Demo` drops an agent file and any declared skills into a Cursor-friendly layout in the project.
- Uninstall cleanly removes everything the install wrote.
- 100% coverage on the new platform module.
- End-to-end test covers at least one install → uninstall round-trip on the Cursor target.

## Non-goals

- Codex, OpenCode, Gemini platform handlers — deferred to v0.5 (they use a different install model rooted in the user's home directory rather than the project tree).
- Changing Cursor's own plugin discovery mechanism — we pick a convention and document it.
- Rewriting the two-function contract — v0.3 set that shape; this feature must fit it.

## User stories

### Story 1 — Install a preset for Cursor (P1)

As a developer using Cursor,
I want `aiadev install --preset lean --platform cursor`
so that Cursor picks up the agent file and preset skills without me handcrafting the layout.

**Acceptance scenarios:**

1. Given an empty project, When I run the command with `PROJECT_NAME=Demo`, Then `AGENTS.md` lands at the project root with `Demo` substituted.
2. Given the same state, When the preset declares skills, Then each skill lands at `.cursor/skills/<name>/SKILL.md` with placeholders substituted.
3. Given the install completed, When I re-run with the same variables, Then every file is reported as `skip`.

### Story 2 — Uninstall (P1)

As a developer who installed the Cursor preset and wants to switch platforms,
I want `aiadev install --preset lean --platform cursor --uninstall`
so that `AGENTS.md` and `.cursor/skills/` get cleaned up while my own code is left alone.

**Acceptance scenarios:**

1. Given a Cursor install recorded in `.aiadev/installed.yaml`, When I uninstall, Then every tracked file disappears and the manifest entry is removed.
2. Given a hand-edited skill file, When I uninstall, Then the command reports a conflict and leaves the file in place unless `--force`.

## Design decisions (resolved during spec)

- **Agent file name:** `AGENTS.md` at the project root. Cursor's community convention uses either `AGENTS.md` or `CLAUDE.md`; picking `AGENTS.md` avoids a collision when a project has both Cursor and Claude Code configured at the same time.
- **Skill location:** `.cursor/skills/<skill-name>/SKILL.md`. Mirrors the Claude Code layout — Cursor auto-discovery is configured in the consumer project's `.cursor-plugin/plugin.json` when present, but by convention Cursor reads skill-style instructions from `.cursor/`.
- **Constitution file:** `constitution.md` at project root, same as Claude Code. Both IDEs can read the same file; duplicating would create drift.

## Data touched

- `AGENTS.md` at project root (created, or conflict if present).
- `.cursor/skills/<name>/SKILL.md` per declared skill.
- `.aiadev/installed.yaml` manifest record (same schema; `platform` field already captures the per-file origin).

## Out-of-band effects

- None. Filesystem-only.

## Open risks

- Cursor's own layout may evolve. Mitigation: the handler is localised in one module; if Cursor changes, we change one file.
- A project targeting both Claude Code and Cursor will end up with both `CLAUDE.md` and `AGENTS.md`. Acceptable — they can be kept in sync manually, or users can pick one platform per project. v0.5 can add a "merge" mode.

## Traceability

- Originating issue: v0.3.0 release notes "what's next".
- Related specs: `specs/feature-install-interactive/spec.md` defines the platform contract that this feature implements.
