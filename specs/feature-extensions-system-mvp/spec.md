# Feature specification: extensions system MVP

**Branch:** `feature/extensions-system-mvp`
**Created:** 2026-04-14
**Status:** Draft
**Spec ID:** 0006

---

## Problem

Today the framework only knows about presets that ship inside the `aiadev` package. There is no way for someone outside the suportly org to publish a preset (or a skill catalog) and let users `aiadev install` it. Third-party presets must be vendored in or copied by hand.

The four releases shipped (v0.3 → v0.7) repeatedly mention an extensions system as v0.8 scope. This spec defines the MVP.

## Users and stakeholders

- **Extension authors** who want to publish a preset (Django, Rails, mobile-only, internal) for others to consume.
- **Framework users** who want one command to install a preset they found on GitHub.
- **Framework maintainers** — keeping the ecosystem opt-in (no surprise auto-loads) and the install model auditable.

## Success criteria

- `aiadev extension add <git-url>` clones a remote extension into `~/.aiadev/extensions/<name>/`, validates its `extension.yaml`, and registers it in `~/.aiadev/extensions/registry.yaml`.
- After adding an extension, `aiadev install --preset <name>` works for any preset declared in that extension, just like a built-in preset.
- `aiadev extension list` prints every registered extension (name, source URL, version, install timestamp).
- `aiadev extension remove <name>` removes the clone and registry entry; built-in presets are untouched.
- `aiadev validate` walks extension-provided skills the same way it walks built-in ones.

## Non-goals

- A central registry / index server. Extensions are git URLs; users curate their own list.
- Cryptographic signing of extensions. The user is trusting the upstream repo at install time; the framework does not verify signatures.
- Dependency resolution between extensions. Each extension is self-contained.
- Auto-update / `aiadev extension update --all`. Updating an extension is `extension remove` + `extension add` for the MVP.
- Adding skills *outside* a preset (a "loose skill catalog" extension). Every shareable artifact lives inside a preset.
- Per-project extension registries. Extensions are user-scope only; project-scope sticks with the preset shipped in the framework.

## User stories

### Story 1 — Add and use an extension (P1)

As a developer who found a Rails preset on GitHub,
I want `aiadev extension add https://github.com/example/rails-preset.git`
so that `aiadev install --preset rails` works in any project on my machine.

**Acceptance scenarios:**

1. Given a clean machine, When I run `aiadev extension add <url>`, Then the extension is cloned to `~/.aiadev/extensions/<name>/` and the registry records `name`, `source`, `version`, `installed_at`.
2. Given the extension above is registered, When I run `aiadev install --preset rails --non-interactive --vars PROJECT_NAME=Demo` in a project, Then the install succeeds and the project's `.aiadev/installed.yaml` records the install with `source: extensions/rails`.
3. Given a built-in preset and an extension preset share the same name, When I run `aiadev install --preset <name>`, Then the built-in wins and the report flags the conflict so the user can rename or remove.

### Story 2 — List and remove (P1)

As a developer cleaning up,
I want `aiadev extension list` and `aiadev extension remove <name>`
so that I can see what is installed and remove what I no longer need.

**Acceptance scenarios:**

1. Given two extensions registered, When I run `aiadev extension list`, Then a table prints both with name / source / version / installed_at.
2. Given one extension installed, When I run `aiadev extension remove <name>`, Then the directory is deleted and the registry no longer lists it. Built-in presets and other extensions are untouched.
3. Given no extensions, When I run `aiadev extension list`, Then it prints "no extensions installed" and exits 0.

### Story 3 — Validate extension manifest (P2)

As an extension author,
I want `aiadev extension add <url>` to fail with a clear error if my `extension.yaml` is malformed
so that I can fix it before users hit the failure.

**Acceptance scenarios:**

1. Given an extension whose `extension.yaml` is missing the `name` field, When `aiadev extension add` runs, Then it fails with a schema error naming the missing field, the clone is removed, and the registry is unchanged.
2. Given an extension that declares a preset name that conflicts with a built-in, When `aiadev extension add` runs, Then it succeeds with a warning (matching Story 1 scenario 3 — built-ins win at install time).

## Design decisions (resolved during spec)

- **Storage:** `~/.aiadev/extensions/<name>/` for the clones, `~/.aiadev/extensions/registry.yaml` for the registry. Both inside the existing `~/.aiadev/` directory introduced in v0.6 for the user-scope manifest.
- **Manifest:** Each extension carries an `extension.yaml` at its root with `name`, `version`, `description`, optional `presets:` list pointing at directory names under `presets/`. Schema lives at `schemas/extension-manifest.schema.json`.
- **Layout requirement:** An extension's `presets/<preset-name>/` must follow the same `preset.yaml` + `CLAUDE.md` + `skills/` layout the framework's built-in presets use.
- **Clone strategy:** `git clone --depth 1` to keep installs fast. The recorded `version` is `git describe --tags --always` of the cloned tip.
- **Conflict policy:** built-in presets win; extensions with a colliding preset name are still installable but `aiadev install --preset <name>` reports the conflict and chooses the built-in. A user can rename the extension preset (manual) or remove the built-in (out of scope) to flip the resolution.
- **CLI command name:** `aiadev extension <add|list|remove>` (singular `extension` to match `aiadev install`).

## Data touched

- `~/.aiadev/extensions/<name>/` — extension clone (entire git repo).
- `~/.aiadev/extensions/registry.yaml` — registry of installed extensions.
- The user-scope install manifest at `~/.aiadev/installed.yaml` is unchanged in shape; entries gain a `source: extensions/<name>` string when they came from an extension preset.

## Out-of-band effects

- Network access during `extension add` (one git clone). All other commands are filesystem-only.

## Open risks

- Cloning arbitrary git URLs runs no code, but the cloned tree may include shell scripts an unaware user runs later. Mitigation: documentation reminds users to inspect the extension before invoking its skills.
- A force-push to the upstream repo can break a future re-install of the same version. Acceptable for MVP.
- Disk usage grows by ~1-5 MB per extension. Acceptable.

## Traceability

- Originating issue: v0.7.0 release notes "what's next".
- Related specs: `specs/feature-install-interactive/` (engine), `specs/feature-scope-user-per-home-install/` (user-level layout).
