# Feature specification: aiadev install --interactive

**Branch:** `feature/install-interactive`
**Created:** 2026-04-14
**Status:** Draft
**Spec ID:** 0001

---

## Problem

`aiadev install` in v0.2 is a stub. It lists a preset's contents but does not render them into the target project. Users who want to adopt a preset still fall back to `scripts/migrate-to-0.2.sh`, which only creates symlinks — no placeholder substitution happens, and the resulting files still contain `{{BACKEND_DIR}}` and siblings at runtime.

The consequence: presets are aspirational. A new project cannot reach a working state via the advertised `aiadev install --preset <name>` command.

## Users and stakeholders

- **Framework users** starting a new project — need a one-shot way to adopt a preset.
- **Framework contributors** publishing new presets — need confidence that variable declarations in `preset.yaml` actually reach the agent file and skills at install time.
- **CI pipelines** bootstrapping scaffolds — need a non-interactive path with all variables on the command line.

## Success criteria

- Running `aiadev install --preset <name>` in an empty project prompts for every variable declared in the preset's `preset.yaml` and writes a project that `aiadev doctor` reports as clean.
- Re-running the same command on an already-installed project detects the existing install, offers to update variables, and does not duplicate files.
- `aiadev install --preset <name> --vars KEY=VAL,KEY2=VAL2 --non-interactive` succeeds in CI without a TTY.
- Installation is fully reversible with `aiadev install --uninstall --preset <name>` or by deleting the files listed in the install manifest.
- No placeholder `{{FOO}}` survives in any file written by the command.

## Non-goals

- Cross-platform install (Cursor, Codex, OpenCode, Gemini) — Claude Code only in the first release; the other four ship in a follow-up.
- Automatic migration from pre-v0.2 consumer layouts — `scripts/migrate-to-0.2.sh` stays the right tool for that path.
- Publishing presets to a remote registry — presets still come from the framework repo.
- GUI or TUI beyond the terminal prompts that `click`/`rich` already provide.

## User stories

### Story 1 — Interactive install in a fresh project (P1)

As a developer starting a new Django + React project,
I want to run `aiadev install --preset django-drf-react` in an empty repo
so that I get a CLAUDE.md, constitution.md extension, and all preset skills in place with my project-specific values substituted.

**Acceptance scenarios:**

1. Given an empty repo with the framework available, When I run `aiadev install --preset django-drf-react`, Then I am prompted for `PROJECT_NAME`, `BACKEND_DIR`, `FRONTEND_DIR`, `GCP_PROJECT`, `GCP_REGION`, and after I answer, `CLAUDE.md` contains my answers in place of every `{{PLACEHOLDER}}`.
2. Given the same initial state, When I run the command, Then `presets/django-drf-react/skills/` content is copied into the project at the location declared by the preset's target (`.claude/skills/<name>/` for Claude Code) with placeholders substituted.
3. Given the same initial state, When I run the command and `aiadev doctor` right after, Then `doctor` returns exit code 0 and reports every installed skill valid.

### Story 2 — Idempotent re-install (P1)

As a developer whose project drifted from the preset after the preset shipped a new skill,
I want to run `aiadev install --preset django-drf-react` again
so that new skills are added and existing ones are updated without duplication and without losing my variable answers.

**Acceptance scenarios:**

1. Given a project with an install manifest at `.aiadev/installed.yaml`, When I run `aiadev install --preset django-drf-react`, Then previously-answered variables are shown as defaults; I accept them with Enter.
2. Given the preset adds a new skill since the last install, When I re-run, Then the new skill appears in the project and the manifest records its install.
3. Given a user-edited skill file, When I re-run, Then the command detects the edit, refuses to overwrite, and tells the user to pass `--force` or move the file out of the way.

### Story 3 — Non-interactive install for CI (P2)

As a CI pipeline building a scaffold in a throwaway container,
I want `aiadev install --preset django-drf-react --non-interactive --vars PROJECT_NAME=demo,BACKEND_DIR=backend,FRONTEND_DIR=frontend,GCP_PROJECT=demo-gcp,GCP_REGION=southamerica-east1`
so that the install completes without a TTY and fails loudly if any required variable is missing.

**Acceptance scenarios:**

1. Given `--non-interactive` and all required variables provided via `--vars`, When the command runs, Then it writes every file without prompting and exits 0.
2. Given `--non-interactive` with a missing required variable, When the command runs, Then it exits non-zero, names the missing variable, and writes no files.
3. Given `--non-interactive --dry-run`, When the command runs, Then it lists every file it would write along with the rendered first line, but writes nothing.

### Story 4 — Uninstall (P2)

As a developer who installed a preset and changed my mind,
I want `aiadev install --preset <name> --uninstall`
so that the files introduced by that preset are removed without touching files I wrote myself.

**Acceptance scenarios:**

1. Given a project with `django-drf-react` installed per the manifest, When I run `aiadev install --preset django-drf-react --uninstall`, Then every file recorded in the manifest is deleted, the manifest entry is removed, and files not recorded (user code, the project's own `spec.md`, etc.) are left untouched.
2. Given a file recorded in the manifest that the user subsequently edited, When uninstall runs, Then the command refuses to delete the file, prints the edit, and instructs the user to pass `--force` or save the file elsewhere.

## Design decisions (resolved during spec)

The following points were ambiguous when the spec was drafted; the `clarify` pass recorded these resolutions so `plan.md` can proceed.

- **Install manifest format:** YAML. Consistent with `preset.yaml`; human-readable for review; matches the tooling already in the codebase.
- **Manifest commit policy:** committed to the repo by default. The preset plus resolved variables describe the project; committing lets CI reproduce the install and lets teammates see what their coworkers installed. An optional `aiadev install --ephemeral` flag (v0.4) can gitignore the manifest for throwaway scaffolds.
- **Claude Code skill destination:** `.claude/skills/<name>/SKILL.md` with `.claude-plugin/plugin.json` updated to reference the path. This respects the existing plugin convention in the framework repo itself.

## Data touched

- `.aiadev/installed.yaml` — new file. Records one entry per installed preset: preset name, version at install time, resolved variable values, list of written files and their sha256.
- `CLAUDE.md` — created by the install (if not present) or merged into (if present).
- `constitution.md` — extended with preset articles if the preset provides one.
- `.claude/skills/<skill>/SKILL.md` — one per skill declared in `preset.yaml`.
- `.claude-plugin/plugin.json` — updated to register the installed skills (Claude Code target).

## Out-of-band effects

- None. The command writes only to the current working directory. No network, no external services.

## Open risks

- Risk: a user with a legacy project may already have a `CLAUDE.md` written by hand. Mitigation: merge-don't-overwrite behavior by default, with `--force` opt-in.
- Risk: placeholder collision — a user answers a variable value that itself contains `{{FOO}}`. Mitigation: single-pass substitution; the tool does not re-scan for placeholders in user-provided values.
- Risk: preset author forgets to declare a placeholder that appears in a file. Mitigation: `aiadev install` runs a dry pass first and lists any `{{...}}` that survived substitution; fails the install unless `--allow-unresolved` is set.

## Traceability

- Originating issue: milestone #1 from v0.2.0 post-release notes.
- Related specs: none yet.
- Constitution articles invoked: I (Spec-first), II (Test-first), III (Simplicity — Claude Code first, others later), IV (Evidence), VII (Attribution — none applies, this is original code).
