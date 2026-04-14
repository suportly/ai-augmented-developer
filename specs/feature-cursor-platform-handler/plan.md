# Implementation plan: Cursor platform handler

**Branch:** `feature/cursor-platform-handler`
**Date:** 2026-04-14
**Spec:** [spec.md](./spec.md)
**Plan version:** 1

---

## Summary

Add a second platform module (`platforms/cursor.py`) next to `platforms/claude_code.py`, wire it into the install engine's `_PLATFORMS` dict and the CLI's alias map, and prove round-trip behaviour with unit + e2e tests. Total scope: ~6 hours.

## Technical context

| Field | Value |
|---|---|
| Language / runtime | Python 3.11+ |
| Primary dependencies | existing only |
| Storage | no new files beyond what v0.3 already writes |
| Testing | pytest + CliRunner |
| Target platform | Cursor IDE |
| Performance budget | same as v0.3 (< 2s) |

## Constitution check

| Article | Applies? | Status | Evidence |
|---|---|---|---|
| I. Spec-first | Yes | PASS | `spec.md` approved |
| II. Test-first | Yes | PASS | every task starts with a failing test |
| III. Simplicity | Yes | PASS | no new abstraction beyond the existing platform contract |
| IV. Evidence over claims | Yes | PASS | CI matrix covers the new tests |
| V. Provider pattern | No | N/A | no external service |
| VI. Privacy by design | Yes | PASS | no new data classes or logs |
| VII. Attribution | Yes | PASS | original code |

## Architecture decisions

**Decision:** Cursor reuses the exact same two-function contract as Claude Code (`resolve_target` + `iter_preset_artifacts`).
**Rationale:** The contract was designed to be platform-agnostic in v0.3. If Cursor exposes anything requiring more surface, extend the contract before adding a third platform; do not one-off it.

**Decision:** Agent file is `AGENTS.md` at project root. Skills at `.cursor/skills/<name>/SKILL.md`.
**Rationale:** `CLAUDE.md` + `AGENTS.md` lets a project configure both IDEs side by side.

## Project structure changes

```text
src/aiadev/platforms/cursor.py                    (new)
tests/test_install_cursor.py                      (new)
src/aiadev/install_engine.py                      (modified — register cursor)
src/aiadev/commands/install.py                    (modified — add alias)
tests/test_install_e2e.py                         (modified — add cursor round-trip)
```

## Phase breakdown

### Phase 1 — Platform handler

- Create `platforms/cursor.py` with `resolve_target` + `iter_preset_artifacts`.
- 100% coverage on the new module.

### Phase 2 — Engine / CLI wiring

- Add `cursor` to `_PLATFORMS` in `install_engine.py` and `_PLATFORM_ALIASES` in `commands/install.py`.
- CLI accepts `--platform cursor`.

### Phase 3 — End-to-end smoke + docs

- Extend `tests/test_install_e2e.py` with a Cursor round-trip.
- Update CHANGELOG [Unreleased] + README.

## Complexity tracking

Empty.
