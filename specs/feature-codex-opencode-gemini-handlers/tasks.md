# Tasks: Codex, OpenCode, Gemini handlers

**Branch:** `feature/codex-opencode-gemini-handlers`
**Plan:** [plan.md](./plan.md)
**Generated:** 2026-04-14

---

## Task list

### T001 — Three platform modules + unit tests

- **Status:** pending
- **Depends on:** —
- **Files:**
  - create: `src/aiadev/platforms/codex.py`
  - create: `src/aiadev/platforms/opencode.py`
  - create: `src/aiadev/platforms/gemini.py`
  - create: `tests/test_install_codex.py`
  - create: `tests/test_install_opencode.py`
  - create: `tests/test_install_gemini.py`
- **Spec scenarios:** Story 1 scenarios 1–3, Story 2 scenarios 1–3, Story 3 scenarios 1–3
- **Acceptance:**
  - [ ] Each handler exposes `resolve_target` + `iter_preset_artifacts` matching its platform's target paths.
  - [ ] 100% line coverage on each new module.
  - [ ] Commit: `feat(multi): T001 codex/opencode/gemini platform handlers`.

### T002 — Engine and CLI wiring

- **Status:** pending
- **Depends on:** T001
- **Files:**
  - modify: `src/aiadev/install_engine.py`
  - modify: `src/aiadev/commands/install.py`
  - modify: `tests/test_install.py` (extend)
- **Spec scenarios:** Story 1–3 scenario 1, Story 4 scenario 1
- **Acceptance:**
  - [ ] `aiadev install --platform codex|opencode|gemini` accepted by the CLI.
  - [ ] Each produces the expected agent file + skills layout for the lean preset.
  - [ ] Co-installation test: running Cursor then Codex with same vars → `AGENTS.md` is `skip` on the second call.
  - [ ] Commit: `feat(multi): T002 engine + CLI wiring for codex/opencode/gemini`.

### T003 — E2E round-trip + docs + release

- **Status:** pending
- **Depends on:** T002
- **Files:**
  - modify: `tests/test_install_e2e.py`
  - modify: `CHANGELOG.md`
  - modify: `README.md`
- **Acceptance:**
  - [ ] E2E: install `mobile-ops` with `--platform codex`; every skill at `.codex/skills/`; no `{{KEY}}` survives; uninstall clean.
  - [ ] CHANGELOG [Unreleased] Added entry for the three new handlers.
  - [ ] README install block updated with the five platform options.
  - [ ] Commit: `feat(multi): T003 e2e, docs, release notes`.
