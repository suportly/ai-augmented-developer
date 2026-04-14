# Tasks: Cursor platform handler

**Branch:** `feature/cursor-platform-handler`
**Plan:** [plan.md](./plan.md)
**Generated:** 2026-04-14

---

## Task list

### T001 — Cursor platform handler + wiring

- **Status:** pending
- **Depends on:** —
- **Files:**
  - create: `src/aiadev/platforms/cursor.py`
  - modify: `src/aiadev/install_engine.py` (register `cursor`)
  - modify: `src/aiadev/commands/install.py` (alias `cursor`)
  - test: `tests/test_install_cursor.py`
  - test: `tests/test_install.py` (extend)
- **Spec scenarios:** Story 1 scenarios 1–3
- **Acceptance:**
  - [ ] `resolve_target` and `iter_preset_artifacts` behave like Claude Code but with Cursor targets (`AGENTS.md`, `.cursor/skills/`).
  - [ ] `aiadev install --platform cursor` works end to end against the lean preset.
  - [ ] 100% coverage on `platforms/cursor.py`.
  - [ ] No Claude Code regression.
  - [ ] Commit message: `feat(cursor): T001 platform handler + wiring`.

### T002 — End-to-end round-trip + docs

- **Status:** pending
- **Depends on:** T001
- **Files:**
  - modify: `tests/test_install_e2e.py`
  - modify: `CHANGELOG.md`
  - modify: `README.md`
- **Spec scenarios:** Story 1 scenarios 1–3, Story 2 scenarios 1–2
- **Acceptance:**
  - [ ] E2E test: install `mobile-ops` with `--platform cursor`, assert every skill at `.cursor/skills/<name>/SKILL.md`, `{{KEY}}` tokens resolved.
  - [ ] Uninstall cleans up.
  - [ ] CHANGELOG [Unreleased] Added: "Cursor platform handler".
  - [ ] README documents `--platform cursor` alongside `--platform claude-code`.
  - [ ] Commit message: `feat(cursor): T002 e2e and docs`.
