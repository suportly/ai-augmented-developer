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

- **Status:** pending
- **Depends on:** T001, T002, T003
- **Files:**
  - create: `src/aiadev/install_engine.py`
  - test: `tests/test_install_engine.py`
- **Spec scenarios:** Story 1 scenarios 1–3, Story 2 scenarios 1–3, Story 3 scenario 1, Story 4 scenario 1
- **Acceptance:**
  - [ ] `install(preset_path, project_root, variables, platform, mode, force)` returns `InstallReport`.
  - [ ] Report contains: files written, files skipped (already present and unchanged), files conflicting (edited since last install).
  - [ ] Conflict policy: refuse unless `force=True`; conflicts are detected by comparing current sha256 against manifest.
  - [ ] Dry-run mode returns the same report without writing.
  - [ ] Uninstall mode removes every file listed in the manifest for that preset; refuses if any file has been edited unless `force=True`.
  - [ ] Re-install preserves previously-answered variable values when the new call passes none for those keys.
  - [ ] Commit message: `feat(install): T004 install engine`.

### T005 — Variable collection (interactive + non-interactive)

- **Status:** pending
- **Depends on:** T002
- **Files:**
  - create: `src/aiadev/variable_prompt.py`
  - test: `tests/test_variable_prompt.py`
- **Spec scenarios:** Story 1 scenario 1, Story 3 scenarios 1–2
- **Acceptance:**
  - [ ] `collect(preset_vars, defaults, non_interactive, cli_vars)` returns a resolved dict.
  - [ ] Non-interactive mode errors if any required variable is missing from `cli_vars + defaults`; the error names the missing variable.
  - [ ] Interactive mode uses `click.prompt` with `default=` from either `preset.yaml` or the previous manifest entry.
  - [ ] `--vars KEY=VAL,KEY2=VAL2` parsing: tolerates spaces, rejects duplicate keys.
  - [ ] Commit message: `feat(install): T005 variable collection`.

### T006 — CLI command wiring

- **Status:** pending
- **Depends on:** T001, T002, T003, T004, T005
- **Files:**
  - modify: `src/aiadev/commands/install.py`
  - test: `tests/test_install.py` (extend)
- **Spec scenarios:** Story 1 scenarios 1–3, Story 3 scenarios 1–3, Story 4 scenarios 1–2
- **Acceptance:**
  - [ ] Options: `--preset`, `--platform` (default `claude-code`), `--vars`, `--non-interactive`, `--dry-run`, `--uninstall`, `--force`, `--allow-unresolved`.
  - [ ] Output: `rich` table showing actions (write / skip / conflict / remove).
  - [ ] Exit codes: 0 success, 1 install error (missing var, conflict without `--force`), 2 usage error (invalid preset name).
  - [ ] The v0.2 stub behavior (`install` prints a list) is replaced; no regression tests on that behavior.
  - [ ] Commit message: `feat(install): T006 CLI command wiring`.

### T007 — End-to-end smoke test and CI job

- **Status:** pending
- **Depends on:** T006
- **Files:**
  - create: `tests/test_install_e2e.py`
  - modify: `.github/workflows/validate.yml`
- **Spec scenarios:** Story 1 scenario 3, Story 2 scenario 2
- **Acceptance:**
  - [ ] Round-trip test: install `django-drf-react` into a tmpdir with fixed variables, run `aiadev doctor` against that tmpdir, expect exit 0.
  - [ ] Re-install the same preset in the same tmpdir; expect no-op (zero files written, zero conflicts).
  - [ ] Uninstall and verify the tmpdir has no leftover files outside what the test itself created.
  - [ ] CI adds a job `install-e2e` on Python 3.12 only (no need for a matrix).
  - [ ] Commit message: `feat(install): T007 end-to-end smoke and CI`.

### T008 — CHANGELOG and docs

- **Status:** pending
- **Depends on:** T007
- **Files:**
  - modify: `CHANGELOG.md`
  - modify: `README.md`
  - modify: `CONTRIBUTING.md`
- **Spec scenarios:** all
- **Acceptance:**
  - [ ] CHANGELOG `[Unreleased]` gains an `Added` entry describing the new `aiadev install` behavior with a CLI example.
  - [ ] README Installation section updated to prefer `aiadev install` over `scripts/migrate-to-0.2.sh`.
  - [ ] CONTRIBUTING gains a note on how to test the install command locally (`python -m aiadev install --preset lean --dry-run`).
  - [ ] Commit message: `docs(install): T008 release notes and usage docs`.

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
