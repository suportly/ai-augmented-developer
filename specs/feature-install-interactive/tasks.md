# Tasks: aiadev install --interactive

**Branch:** `feature/install-interactive`
**Plan:** [plan.md](./plan.md)
**Generated:** 2026-04-14

---

## How to read this file

- Tasks are ordered. `implement` runs them top-to-bottom.
- One task = one commit. The commit message starts with the task id.
- Each task links back to the spec acceptance scenarios it exercises.
- `Status` is one of: `pending`, `in_progress`, `blocked`, `done`. Only `implement` mutates it.

## Task list

### T001 — Placeholder substitution module

- **Status:** done
- **Depends on:** —
- **Files:**
  - create: `src/aiadev/placeholders.py`
  - test: `tests/test_placeholders.py`
- **Spec scenarios:** Story 1 scenario 1, Story 3 scenario 3
- **Acceptance:**
  - [x] `substitute(text, {"FOO": "bar"})` replaces every `{{FOO}}` with `bar`.
  - [x] `substitute` is a pure function (no IO, no mutation of inputs).
  - [x] `find_unresolved(text)` returns a sorted list of `{{KEY}}` tokens that remain.
  - [x] Edge tests: repeated placeholder, empty values dict, values containing `{{` literal, nested placeholders (`{{{{FOO}}}}`) left alone.
  - [x] 100% line coverage for this module (19 tests, all passing).
  - [x] Commit message: `feat(install): T001 placeholder substitution`.

### T002 — Manifest schema and IO

- **Status:** done
- **Depends on:** —
- **Files:**
  - create: `src/aiadev/install_manifest.py`
  - create: `schemas/install-manifest.schema.json`
  - test: `tests/test_install_manifest.py`
  - test: `tests/fixtures/manifest/valid.yaml`
  - test: `tests/fixtures/manifest/invalid_missing_preset_name.yaml`
  - test: `tests/fixtures/manifest/invalid_bad_sha.yaml`
- **Spec scenarios:** Story 2 scenario 1, Story 4 scenario 1
- **Acceptance:**
  - [x] `InstalledPreset` dataclass with fields: `name`, `version`, `variables` (dict), `files` (list of `InstalledFile`), `installed_at`.
  - [x] `InstalledFile` dataclass: `path`, `sha256`, `role` (`agent_file` / `constitution` / `skill` / `plugin_manifest`).
  - [x] `load(path)` reads YAML and validates against the schema.
  - [x] `save(manifest, path)` writes YAML atomically (tempfile + os.replace).
  - [x] Round-trip test: save then load returns equivalent object.
  - [x] Commit message: `feat(install): T002 install manifest read/write`.

### T003 — Claude Code platform handler

- **Status:** done
- **Depends on:** T001, T002
- **Files:**
  - create: `src/aiadev/platforms/__init__.py`
  - create: `src/aiadev/platforms/claude_code.py`
  - test: `tests/test_install_claude_code.py`
  - test: `tests/fixtures/mini-preset/preset.yaml`
  - test: `tests/fixtures/mini-preset/CLAUDE.md`
  - test: `tests/fixtures/mini-preset/skills/hello-world/SKILL.md`
- **Spec scenarios:** Story 1 scenario 2
- **Acceptance:**
  - [x] `resolve_target(role, name, project_root)` returns the correct destination path for `agent_file`, `constitution`, and `skill` roles.
  - [x] `iter_preset_artifacts(preset_root)` enumerates files this platform installs from a preset, sorted deterministically.
  - [x] Unknown roles and empty skill names are rejected with `ValueError`.
  - [x] Plugin manifest (`.claude-plugin/plugin.json`) management is deliberately deferred — Claude Code auto-discovers `.claude/skills/`. Documented in the module docstring.
  - [x] 100% line coverage (30/30 stmts).
  - [x] Commit message: `feat(install): T003 Claude Code platform handler`.

### T004 — Install engine orchestration

- **Status:** done
- **Depends on:** T001, T002, T003
- **Files:**
  - create: `src/aiadev/install_engine.py`
  - test: `tests/test_install_engine.py`
- **Spec scenarios:** Story 1 scenarios 1–3, Story 2 scenarios 1–3, Story 3 scenario 1, Story 4 scenarios 1–2
- **Acceptance:**
  - [x] `install(preset_path, project_root, variables, *, platform, mode, force, allow_unresolved, now)` returns `InstallReport`.
  - [x] Report fields: `written`, `skipped`, `conflicts`, `removed`, `unresolved`, plus `ok` property.
  - [x] Conflict detection: file present whose sha256 is not the one recorded in the manifest. Refuse unless `force=True`.
  - [x] Dry-run mode returns the same report without writing files or manifest.
  - [x] Uninstall removes files whose current sha still matches the manifest; blocks on edited files unless `force=True`; cleans up empty skill directories and `.aiadev/` when the last preset is gone.
  - [x] Re-install merges variables: existing values preserved, new keys override.
  - [x] Unresolved placeholders reported; hard error unless `allow_unresolved=True`.
  - [x] 98% coverage on the engine (142 stmts, 3 uncovered are edge-cases inside rare error paths).
  - [x] Commit message: `feat(install): T004 install engine`.

### T005 — Variable collection (interactive + non-interactive)

- **Status:** done
- **Depends on:** T002
- **Files:**
  - create: `src/aiadev/variable_prompt.py`
  - test: `tests/test_variable_prompt.py`
- **Spec scenarios:** Story 1 scenario 1, Story 3 scenarios 1–2
- **Acceptance:**
  - [x] `collect(preset_vars, *, previous, cli_vars, non_interactive, prompt_func)` returns a resolved dict.
  - [x] Non-interactive mode errors if any required variable is missing from every source; the error names the missing variable.
  - [x] Interactive mode uses the injected `prompt_func` (defaults to `click.prompt`) with `default=` from the previous install or the preset.
  - [x] `parse_cli_vars` / `merge_vars_strings`: whitespace-tolerant, duplicate-rejecting, supports repeated `--vars`.
  - [x] 100% coverage (58/58 stmts, 23 tests).
  - [x] Commit message: `feat(install): T005 variable collection`.

### T006 — CLI command wiring

- **Status:** done
- **Depends on:** T001, T002, T003, T004, T005
- **Files:**
  - modify: `src/aiadev/commands/install.py`
  - modify: `src/aiadev/paths.py` (AIADEV_ROOT + package-location fallback)
  - modify: `tests/test_install.py` (rewritten for the real CLI)
  - modify: `tests/test_doctor.py` (pin AIADEV_ROOT when asserting the failure case)
- **Spec scenarios:** Story 1 scenarios 1–3, Story 3 scenarios 1–3, Story 4 scenarios 1–2
- **Acceptance:**
  - [x] Options wired: `--preset`, `--platform` (default `claude-code`), `--vars` (multiple), `--non-interactive`, `--dry-run`, `--uninstall`, `--force`, `--allow-unresolved`, `--project-root`.
  - [x] Output via `rich.Table` with colored Action column (write/skip/remove/conflict) and relative Path column; unresolved placeholders and conflict hints printed below the table.
  - [x] Exit codes: 0 success / ok report; 1 install error (missing var, unresolved, conflict); 2 usage error (bad preset name, malformed --vars, framework not found).
  - [x] v0.2 stub tests replaced; 12 new cases cover validation, non-interactive, re-install, conflict/force, uninstall.
  - [x] Framework-root resolution now supports AIADEV_ROOT env var and package-location fallback so the CLI works from anywhere once installed.
  - [x] Manual smoke: `aiadev install --preset lean --non-interactive --vars PROJECT_NAME=SmokeDemo` in `/tmp/install-smoke` wrote CLAUDE.md and `.aiadev/installed.yaml`.
  - [x] Commit message: `feat(install): T006 CLI command wiring`.

### T007 — End-to-end smoke test and CI job

- **Status:** done
- **Depends on:** T006
- **Files:**
  - create: `tests/test_install_e2e.py`
  - modify: `.github/workflows/validate.yml`
- **Spec scenarios:** Story 1 scenario 3, Story 2 scenario 2
- **Acceptance:**
  - [x] Round-trip: install `lean` into a tmpdir with fixed variables, run `aiadev doctor`, expect exit 0 (lean used instead of django-drf-react for MVP smoke; multi-skill flow covered by the mobile-ops variant below).
  - [x] Re-install: identical variables yield no writes (`"write"` absent from the output).
  - [x] Uninstall: CLAUDE.md and `.aiadev/` both removed.
  - [x] `mobile-ops` smoke installs 11 skills with 15 placeholders substituted; no `{{KEY}}` survives.
  - [x] Module entry point: `python -m aiadev install ...` works as a subprocess (uses `sys.executable`).
  - [x] CI adds `install-e2e` job on Python 3.12.
  - [x] Commit message: `feat(install): T007 end-to-end smoke and CI`.

### T008 — CHANGELOG and docs

- **Status:** done
- **Depends on:** T007
- **Files:**
  - modify: `CHANGELOG.md`
  - modify: `README.md`
  - modify: `CONTRIBUTING.md`
- **Spec scenarios:** all
- **Acceptance:**
  - [x] CHANGELOG `[Unreleased]` documents every `aiadev install` capability, the new modules, the schema, the CI job, and the fallback resolution.
  - [x] README Installation section now leads with the `aiadev install` workflow (editable install, interactive / non-interactive / dry-run / uninstall examples). Platform plugins kept as "unchanged from v0.2" alternatives.
  - [x] CONTRIBUTING gained a "Testing the install command locally" subsection showing the `AIADEV_ROOT=... python -m aiadev install --preset lean` pattern against a tmpdir.
  - [x] Commit message: `docs(install): T008 release notes and usage docs`.

## Parallelization hints

- Parallel group A: T001, T002 — independent, both under `src/aiadev/` but different files.
- Parallel group B: T003, T005 — independent, each depends on earlier groups.
- Serial after that: T004 → T006 → T007 → T008.

## Post-task checklist

After every task:

- [ ] Commit message references the task id.
- [ ] Status in this file updated.
- [ ] `aiadev validate` passes locally.

After all tasks:

- [ ] Full test suite passes (`pytest --cov=src/aiadev --cov-fail-under=85`). Coverage target bumped from 80% to 85% because the install paths are newly covered.
- [ ] `analyze` skill runs and reports no drift vs spec / plan.
- [ ] `checklist` security pass (user-supplied variables reach file content; verify no shell injection paths).
- [ ] Hand off to `requesting-code-review` to open the PR.
