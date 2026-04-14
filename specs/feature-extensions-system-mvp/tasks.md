# Tasks: extensions system MVP

**Branch:** `feature/extensions-system-mvp`
**Plan:** [plan.md](./plan.md)
**Generated:** 2026-04-14

---

## Task list

### T001 — Extensions module + schema

- **Status:** pending
- **Depends on:** —
- **Files:**
  - create: `src/aiadev/extensions.py`
  - create: `schemas/extension-manifest.schema.json`
  - create: `tests/test_extensions.py`
  - create: `tests/fixtures/extensions/sample-extension/extension.yaml`
  - create: `tests/fixtures/extensions/sample-extension/presets/sample/preset.yaml`
  - create: `tests/fixtures/extensions/sample-extension/presets/sample/CLAUDE.md`
- **Spec scenarios:** Story 1 scenarios 1–3, Story 3 scenarios 1–2
- **Acceptance:**
  - [ ] `add(url, *, registry_root=None)` clones the URL via `git clone --depth 1`, validates `extension.yaml`, registers; returns the registry entry.
  - [ ] `list_all(registry_root=None)` reads the registry.
  - [ ] `remove(name, registry_root=None)` deletes the clone + registry entry.
  - [ ] `find_preset(preset_name, registry_root=None)` returns `(extension_name, preset_path)` or `None`.
  - [ ] Tests use `tmp_path` as a fake `~/.aiadev/extensions/` and a local bare git repo as the source; no real network access.
  - [ ] 100% line coverage on the module.
  - [ ] Commit: `feat(extensions): T001 extensions module + schema`.

### T002 — CLI subcommand

- **Status:** pending
- **Depends on:** T001
- **Files:**
  - create: `src/aiadev/commands/extension.py`
  - modify: `src/aiadev/cli.py`
  - create: `tests/test_extension_command.py`
- **Spec scenarios:** Story 1 scenario 1, Story 2 scenarios 1–3
- **Acceptance:**
  - [ ] `aiadev extension add <url>` prints the registered entry and exits 0.
  - [ ] `aiadev extension list` prints a `rich.Table` with name / source / version / installed_at; "no extensions installed" + exit 0 when empty.
  - [ ] `aiadev extension remove <name>` removes; missing name -> exit 1.
  - [ ] All tests monkeypatch `HOME` so the real `~/.aiadev/` is never touched.
  - [ ] Commit: `feat(extensions): T002 CLI subcommand`.

### T003 — Engine integration

- **Status:** pending
- **Depends on:** T002
- **Files:**
  - modify: `src/aiadev/install_engine.py`
  - modify: `src/aiadev/commands/install.py`
  - extend: `tests/test_install_engine.py`
  - extend: `tests/test_install.py`
- **Spec scenarios:** Story 1 scenario 2, Story 1 scenario 3
- **Acceptance:**
  - [ ] `install(...)` falls back to `extensions.find_preset(name)` when no built-in matches.
  - [ ] On name collision, the built-in wins and the report includes a one-line note about the shadowed extension.
  - [ ] `aiadev install --preset <ext-only-preset>` succeeds end to end via an extension fixture.
  - [ ] Commit: `feat(extensions): T003 install engine integration`.

### T004 — E2E + docs + release prep

- **Status:** pending
- **Depends on:** T003
- **Files:**
  - extend: `tests/test_install_e2e.py`
  - modify: `CHANGELOG.md`
  - modify: `README.md`
  - modify: `CONTRIBUTING.md`
- **Acceptance:**
  - [ ] E2E round-trip: create a bare git repo in `tmp_path` containing a tiny extension, `aiadev extension add <bare-repo-url>`, `aiadev install --preset <ext-preset> --non-interactive --vars …`, assert files written and manifest entries; finally `aiadev extension remove`.
  - [ ] CHANGELOG [Unreleased] documents the new command, registry, and engine fallback.
  - [ ] README gains an "Extensions" section with one example.
  - [ ] CONTRIBUTING points at the extension authoring guide (placeholder OK in MVP).
  - [ ] Commit: `feat(extensions): T004 e2e + docs`.
