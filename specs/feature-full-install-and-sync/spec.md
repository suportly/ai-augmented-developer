# Feature specification: full install + `aiadev sync`

**Branch:** `feature/full-install-and-sync`
**Created:** 2026-04-15
**Status:** Draft
**Spec ID:** 0007

---

## Problem

Today `aiadev install --preset <name>` only writes `CLAUDE.md`, `constitution.md` (optional), and the preset's own skills. The 14 framework-generic skills in `/skills/` and the 3 agents in `/agents/` are **not** copied into the project — they rely on the `ai-augmented-developer` Claude Code plugin being loaded globally at the user level. Slash commands do not exist anywhere in the framework.

Observed symptom: `aiadev install --preset lean` on a new project creates a single `CLAUDE.md` and nothing else. Opening Claude Code in that directory shows no `/specify`, `/plan`, `/implement`, etc. — the CLAUDE.md references skills that the project doesn't ship, so the experience is empty.

There is also no mechanism to **update** an installed project when the framework gains new commands/agents/skills or when the project's stack evolves.

## Users and stakeholders

- **Framework users** — want a new project to be productive immediately after `aiadev install`, without hunting for a plugin.
- **Framework maintainers** — want one install path that covers all 5 platforms (claude-code, cursor, codex, opencode, gemini) consistently.
- **Preset authors** — may add their own `commands/` and `agents/` on top of the framework-generic set.

## Success criteria

- `aiadev install --preset <x>` on an empty directory produces (per platform convention):
  - 14 slash-command wrappers for the pipeline skills.
  - 3 agent definitions (code-reviewer, plan-document-reviewer, spec-document-reviewer).
  - 14 framework-generic skills copied under `.<platform>/skills/`.
  - 5 framework-generic rules (`code-style`, `testing`, `api-conventions`, `security`, `git-workflow`) under `.<platform>/rules/` (`.mdc` for Cursor, `.md` elsewhere).
  - The preset's own skills, commands, agents, and rules on top.
  - `CLAUDE.md` (or `AGENTS.md` / `GEMINI.md`) and `constitution.md` as before.
- `aiadev sync` is idempotent: re-running without edits produces zero writes.
- `aiadev sync` on a project whose upstream framework gained new commands/agents **pulls the new artifacts** into the project, respecting hand-edited files (conflict unless `--force`).
- `aiadev sync` **regenerates** a delimited section of `CLAUDE.md` (`<!-- aiadev:auto-stack:start -->` … `<!-- aiadev:auto-stack:end -->`) from project introspection (package.json, pyproject.toml, Makefile, docker-compose.yml, CI workflows). Content outside the markers is never touched.
- All 5 platform handlers honour the two new roles `command` and `agent`. Gemini emits TOML commands; the other four emit Markdown.
- Installing the same preset twice is still idempotent; uninstall still removes exactly what install wrote (including commands and agents), with drift detection.
- Manifest format is forward-compatible: existing v0.8 manifests keep loading; `aiadev sync` fills in the gaps on first run.

## Non-goals

- Extensions providing commands or agents. (v0.10 scope.)
- Migrating the YAML shape of `.aiadev/installed.yaml` beyond adding new values to the `role` enum.
- Per-language deep introspection (LSP, AST parsing). The stack detector reads well-known config files only.
- Interactive prompts during `sync`. Behaviour is governed by flags.
- Removing the global Claude Code plugin. Users who prefer the plugin can keep it; project-local skills take precedence when both are present.

## User stories

### Story 1 — Full install on an empty project (P1)

As a developer starting a new project,
I want `aiadev install --preset lean` to leave the project ready for the full pipeline,
so that `/specify`, `/plan`, `/implement`, `/sync` etc. appear in Claude Code immediately.

**Acceptance scenarios:**

1. Given an empty directory, When `aiadev install --preset lean --vars PROJECT_NAME=Demo` runs, Then `.claude/commands/` contains 15 `.md` files (14 pipeline + `sync`), `.claude/agents/` contains 3 `.md` files, `.claude/skills/` contains 14 directories each with `SKILL.md`, and `CLAUDE.md` is rendered at the root.
2. Given the same directory re-installed, When the command re-runs, Then every file is reported as `skip` (identical sha), no writes happen, and exit code is 0.
3. Given `--platform cursor`, When install runs, Then artifacts land under `.cursor/commands/`, `.cursor/agents/`, `.cursor/skills/` and `AGENTS.md` at root. Gemini uses `.gemini/commands/<name>.toml`.

### Story 2 — Update installed files from framework (P1)

As a developer whose framework version was bumped,
I want `aiadev sync` to pull new commands/agents/skills into my project,
so that I do not have to delete and reinstall.

**Acceptance scenarios:**

1. Given a v0.8 project (commands/agents absent), When `aiadev sync` runs, Then the 14 commands and 3 agents are written, the manifest records them, and existing files are untouched.
2. Given the user has edited `.claude/commands/specify.md`, When `aiadev sync` runs without `--force`, Then the edited file is reported as `conflict` and skipped; other files sync normally.
3. Given the same edit, When `aiadev sync --force` runs, Then the edit is overwritten and the new sha is recorded.

### Story 3 — Regenerate stack snapshot (P1)

As a developer,
I want `aiadev sync` to update the "Detected stack" section of `CLAUDE.md`,
so that the agent has up-to-date facts about my project.

**Acceptance scenarios:**

1. Given a project with `package.json` and `pyproject.toml`, When `aiadev sync` runs, Then the content between `<!-- aiadev:auto-stack:start -->` and `<!-- aiadev:auto-stack:end -->` lists detected languages, top-level scripts, and frameworks.
2. Given the user edited text outside the markers, When sync runs, Then that text is preserved byte-for-byte.
3. Given no markers exist in the CLAUDE.md (legacy project), When sync runs, Then a new block is appended at the end of the file with a one-line note in the console output; pre-existing content is unchanged.

### Story 4 — Uninstall covers new roles (P2)

As a developer removing a preset,
I want `aiadev install --uninstall --preset <x>` to remove commands/agents/skills it installed,
so that the project returns to a clean state.

**Acceptance scenarios:**

1. Given a fresh install, When uninstall runs, Then every file in the manifest is deleted and empty `.claude/commands/`, `.claude/agents/`, `.claude/skills/` directories are removed. Drift on any file blocks that file's deletion unless `--force`.

## Design decisions (resolved during spec)

- **Roles:** `FileRole` gains `command`, `agent`, and `rule`. Existing roles unchanged.
- **Rules layout:** `.claude/rules/*.md`, `.cursor/rules/*.mdc` (Cursor native), `.codex/rules/*.md`, `.opencode/rules/*.md`, `.gemini/rules/*.md`. Handlers translate the `.md` source to `.mdc` for Cursor solely by target path; no content transformation required.
- **Framework scan:** framework-generic `/commands/`, `/agents/`, `/skills/` always install. Preset files of the same name override framework files (preset tightens, never removes).
- **Command wrappers:** each is a thin markdown file with frontmatter (`description`, `allowed-tools`, `argument-hint`) that invokes the same-named skill via `$ARGUMENTS`.
- **Gemini commands:** rendered as TOML (`.gemini/commands/<name>.toml`) via a handler-specific converter; source of truth stays markdown at `/commands/<name>.md`.
- **Markers in CLAUDE.md:** HTML-comment delimiters so the block is invisible in rendered markdown; regex-based replacement preserves everything else.
- **Sync mode:** new `InstallMode.SYNC`. Same sha-based logic as INSTALL, but silent skip when the file matches either the old or new recorded sha (handles framework bumps cleanly).

## Review & acceptance checklist

- [ ] No implementation details in spec (engine flow, CLI flags documented at the "what the user sees" level).
- [ ] Each success criterion is checkable from the CLI.
- [ ] 5 platforms covered by at least one acceptance scenario.
- [ ] Uninstall invariant preserved.
- [ ] No breaking manifest change.
