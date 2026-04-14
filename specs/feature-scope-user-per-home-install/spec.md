# Feature specification: per-home install scope

**Branch:** `feature/scope-user-per-home-install`
**Created:** 2026-04-14
**Status:** Draft
**Spec ID:** 0004

---

## Problem

`aiadev install` only installs into a project directory. Users who want a preset's skills available across every project — the pattern the legacy `INSTALL.md` scripts document — must fall back to manual symlinks (`~/.codex/`, `~/.config/opencode/`). The CLI has no equivalent for this "system-wide" install model.

## Users and stakeholders

- Developers who want one preset installed once at user level for all projects (a common pattern for the Python skills catalog, the operational runbooks, etc.).
- CI users who bootstrap container images with framework skills pre-installed in `$HOME` of the CI user.
- Framework maintainers — completing the install story around both scopes.

## Success criteria

- `aiadev install --scope user --preset <name>` writes the preset's **skills** under `~/.<platform>/skills/<name>/SKILL.md` (one per declared skill).
- `aiadev install --scope user --preset <name> --uninstall` removes every user-scope file tracked in the user-level manifest.
- Project-scope installs (`--scope project`, the default) behave exactly as in v0.5 — no regression.
- The per-user manifest lives at `~/.aiadev/installed.yaml`; it is a separate manifest from any project's `.aiadev/installed.yaml`, so project-level and user-level installs never step on each other.
- A preset-declared agent file or constitution is explicitly **skipped** with a clear report entry when `--scope user` is passed (agent files are per-project by nature; a global agent file does not have a stable cross-platform location).
- 100% coverage on the new scope logic.

## Non-goals

- Installing an agent file (`CLAUDE.md`, `AGENTS.md`, `GEMINI.md`) or constitution at user level. Agent files carry project-specific variables (`PROJECT_NAME`, paths); a user-level file would be stale the moment the user opens a different project. Deferred — possibly forever.
- Writing into arbitrary paths outside `$HOME`. `--scope user` is strictly for current-user install; root-owned paths are out of scope.
- Supporting multiple concurrent user-level installs of the same preset with different variables. Re-installing updates the existing record — same idempotency rule as project scope.

## User stories

### Story 1 — Install skills globally (P1)

As a developer,
I want `aiadev install --scope user --preset mobile-ops --non-interactive --vars <...>`
so that every project I open from any directory has the mobile-ops skills available without per-project symlinks.

**Acceptance scenarios:**

1. Given a clean `$HOME`, When I run the command with all mobile-ops variables provided, Then `~/.codex/skills/<each skill>/SKILL.md` (or the claude/cursor/opencode/gemini equivalent per `--platform`) contains the rendered skill, and `~/.aiadev/installed.yaml` records the install.
2. Given a pre-existing user-scope install, When I re-run with the same variables, Then every skill is reported as `skip`.
3. Given a preset that declares an agent file (e.g. `CLAUDE.md` template) and skills, When I run `--scope user`, Then the agent file is reported with a `skip: user scope does not install agent_file` note and only the skills are written.

### Story 2 — Uninstall at user level (P1)

As a developer removing a preset from my machine,
I want `aiadev install --scope user --preset mobile-ops --uninstall`
so that every user-level file the install wrote is removed, while any per-project installs (stored in that project's `.aiadev/installed.yaml`) are untouched.

**Acceptance scenarios:**

1. Given a user-scope install, When I uninstall, Then every tracked file under `~/.<platform>/` disappears, ancestor directories are rmdir'd when empty, and the entry is removed from `~/.aiadev/installed.yaml`.
2. Given a user-scope install **and** a project-scope install of the same preset, When I uninstall at user scope, Then only the user files are removed; the project's manifest and files stay intact.

### Story 3 — Scope separation (P2)

As a user who installs the same preset at both scopes,
I want the manifests to stay separate
so that idempotency, conflict detection, and uninstall all operate on the right files.

**Acceptance scenarios:**

1. Given a user-scope install, When I later run a project-scope install of the same preset in a project directory, Then the project install completes normally, the project manifest records only the project files, and the user manifest is untouched.

## Design decisions (resolved during spec)

- **Flag name:** `--scope {user,project}`. Default is `project` for backward compatibility.
- **Manifest path:** `~/.aiadev/installed.yaml` for `--scope user`; `<project>/.aiadev/installed.yaml` unchanged for project scope. Same schema.
- **Artifact coverage at user scope:** skills only. Agent file and constitution are reported with a `skipped_unsupported` note (new field on `InstallReport`) and excluded from the manifest.
- **Path resolution:** each platform handler exposes `user_scope_supported(role) -> bool` and the engine filters the artifact list accordingly before calling `resolve_target`. The existing `resolve_target(role, name, install_root, scope=...)` signature gains a `scope` keyword to compute the right absolute path from either `project_root` or `$HOME`.
- **Coexistence with project scope:** the engine derives `install_root` from `scope` (project → `project_root`; user → `Path.home()`), loads the scope-specific manifest, and writes/uninstalls through the same code path.

## Data touched

- `~/.aiadev/installed.yaml` — new user-level manifest (same schema as the project manifest).
- `~/.claude/skills/<name>/SKILL.md`, `~/.cursor/skills/<name>/SKILL.md`, `~/.codex/skills/<name>/SKILL.md`, `~/.config/opencode/skills/<name>/SKILL.md` (or `~/.opencode/skills/<name>/SKILL.md` — see decision below), `~/.gemini/skills/<name>/SKILL.md`.
- OpenCode path: `~/.opencode/skills/<name>/SKILL.md`. The legacy `INSTALL.md` pointed at `~/.config/opencode/`; we adopt the shorter `~/.opencode/` to match the other four handlers' dot-prefix convention. Users who want the XDG path can symlink.

## Out-of-band effects

- None. Filesystem-only and strictly under `$HOME`.

## Open risks

- A user with both scopes installed for the same preset could get confused when re-running — the CLI should print the scope explicitly in its report header.
- `$HOME` inside a container may not persist across runs; document that `--scope user` is only useful when `$HOME` is writeable and durable.
- Changing a user-scope install for a new preset version requires the user to re-run with new variables; this is the same ergonomics as project scope.

## Traceability

- Originating issue: v0.5.0 release notes "what's next".
- Related specs: `specs/feature-install-interactive/spec.md` (engine), platform handler specs v0.4 / v0.5.
