# Feature specification: Codex, OpenCode, Gemini platform handlers

**Branch:** `feature/codex-opencode-gemini-handlers`
**Created:** 2026-04-14
**Status:** Draft
**Spec ID:** 0003

---

## Problem

`aiadev install --platform {codex,opencode,gemini}` is not wired. v0.3 and v0.4 shipped Claude Code and Cursor; three of the five advertised platforms remain unimplemented, and users targeting those IDEs fall back to symlink scripts that do not substitute preset variables.

## Users and stakeholders

- Users running Codex CLI, OpenCode, or Gemini CLI as their coding agent.
- Framework maintainers — completing the announced v0.2/v0.3 platform set.

## Success criteria

- `aiadev install --preset <name> --platform codex` writes `AGENTS.md` + `.codex/skills/<name>/SKILL.md` into the project with variables substituted.
- `aiadev install --preset <name> --platform opencode` writes `AGENTS.md` + `.opencode/skills/<name>/SKILL.md`.
- `aiadev install --preset <name> --platform gemini` writes `GEMINI.md` + `.gemini/skills/<name>/SKILL.md`.
- Uninstall cleans up every file and ancestor directory the installer wrote.
- End-to-end round-trip test covers one of the three (the other two are covered by unit tests; the engine and CLI paths are shared).
- 100% coverage on each new platform module.

## Non-goals

- **Per-home install** (symlinks under `~/.codex/`, `~/.config/opencode/`, or `gemini extensions install`). The existing `scripts/migrate-to-0.2.sh` and the platform-specific `INSTALL.md` files still document that path. Widening the engine for system-wide installs is v0.6 scope.
- Verifying that each IDE actually discovers the written files. That depends on upstream configuration which the framework cannot control. The `INSTALL.md` docs spell out the caveats.
- Modifying the platform contract (`resolve_target` + `iter_preset_artifacts`). The contract is frozen; each new platform is one module that fits it.

## User stories

### Story 1 — Codex install (P1)

As a Codex user,
I want `aiadev install --preset lean --platform codex`
so that my project gets an `AGENTS.md` with project-specific values and any preset skills at `.codex/skills/`.

**Acceptance scenarios:**

1. Given an empty project and a preset with an agent file plus one skill, When I run the command with `PROJECT_NAME=Demo`, Then `AGENTS.md` and `.codex/skills/<skill>/SKILL.md` exist with `Demo` substituted.
2. Given a project already installed, When I re-run, Then every file is reported as `skip`.
3. Given a Codex install, When I uninstall, Then `AGENTS.md`, `.codex/`, and `.aiadev/` are gone.

### Story 2 — OpenCode install (P1)

Same as Story 1 with `--platform opencode`, `.opencode/skills/`, agent file `AGENTS.md`.

### Story 3 — Gemini install (P1)

Same as Story 1 with `--platform gemini`, `.gemini/skills/`, agent file `GEMINI.md`.

### Story 4 — Coexistence (P2)

As a user who configures multiple IDEs for the same project,
I want to run `aiadev install --platform <claude-code|cursor|codex|opencode>` in sequence
so that each platform's skill layout lands in the project without overwriting the others. `AGENTS.md` is shared between Cursor, Codex, and OpenCode (sha256 match → skip); `CLAUDE.md` stays Claude-only; `GEMINI.md` stays Gemini-only.

**Acceptance scenarios:**

1. Given a project, When I install `--platform cursor` and then `--platform codex` with the same variables, Then the second install reports `AGENTS.md` as `skip` (sha match) and writes only the platform-specific skills dir.

## Design decisions (resolved during spec)

- **Agent file names:** Codex → `AGENTS.md`; OpenCode → `AGENTS.md`; Gemini → `GEMINI.md`. Follows each IDE's documented convention.
- **Skill directories:** `.codex/skills/<name>/SKILL.md`, `.opencode/skills/<name>/SKILL.md`, `.gemini/skills/<name>/SKILL.md`. These paths may not match every IDE's auto-discovery logic out of the box; the framework writes the canonical layout, and users can configure their IDE to look there (documented in each platform's INSTALL.md).
- **Constitution:** Shared `constitution.md` at project root across every platform — same rule as Claude Code + Cursor.
- **Platform aliases in CLI:** `codex`, `opencode`, `gemini` map to module names `codex`, `opencode`, `gemini` (identity), added alongside the existing `claude-code` and `cursor`.

## Data touched

- `AGENTS.md` (Codex, OpenCode) or `GEMINI.md` (Gemini) at project root.
- `.{codex,opencode,gemini}/skills/<name>/SKILL.md` per declared skill.
- `.aiadev/installed.yaml` manifest entry per install.

## Out-of-band effects

- None. Filesystem-only.

## Open risks

- Each IDE's skill-discovery rules vary. The install layout is our best guess; users may need a one-line config entry pointing at `.{codex,opencode,gemini}/skills/`. Mitigation: document in the release notes and platform-specific `INSTALL.md` files.
- `AGENTS.md` conflicts: if the user already has one, the install reports a conflict unless `--force`. Same existing behaviour from Cursor; no new code.

## Traceability

- Originating issue: v0.4.0 release notes "what's next".
- Related specs: `specs/feature-install-interactive/spec.md` (engine), `specs/feature-cursor-platform-handler/spec.md` (second-platform pattern).
