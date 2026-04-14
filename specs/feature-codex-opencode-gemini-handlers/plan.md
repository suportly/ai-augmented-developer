# Implementation plan: Codex, OpenCode, Gemini handlers

**Branch:** `feature/codex-opencode-gemini-handlers`
**Date:** 2026-04-14
**Spec:** [spec.md](./spec.md)
**Plan version:** 1

---

## Summary

Three new platform modules, each about 30 lines, each satisfying the established `resolve_target` + `iter_preset_artifacts` contract. Register them in the engine's `_PLATFORMS` dict and the CLI's alias map. Add unit tests per module plus one e2e round-trip. Bundle documentation. Total scope: ~4 hours.

## Technical context

| Field | Value |
|---|---|
| Language / runtime | Python 3.11+ |
| New dependencies | none |
| Storage | same as v0.3/v0.4 |
| Testing | pytest + CliRunner |
| Performance budget | < 2s install, same as v0.4 |

## Constitution check

| Article | Applies? | Status | Evidence |
|---|---|---|---|
| I. Spec-first | Yes | PASS | `spec.md` approved |
| II. Test-first | Yes | PASS | unit tests precede each handler |
| III. Simplicity | Yes | PASS | no contract change; identical pattern to cursor.py |
| IV. Evidence | Yes | PASS | CI matrix + e2e covers each path |
| V. Provider pattern | No | N/A | no external service |
| VI. Privacy | Yes | PASS | no new data |
| VII. Attribution | Yes | PASS | original code |

## Architecture decisions

**Decision:** Three separate modules (`codex.py`, `opencode.py`, `gemini.py`) rather than one parameterised file.
**Rationale:** Each IDE may evolve independently; keeping handlers separate lets us diverge per platform without a mass refactor. The cost (duplication of the `iter_preset_artifacts` walker) is tiny.

**Decision:** Skills at `.{platform}/skills/<name>/SKILL.md`.
**Rationale:** Consistent with Claude Code and Cursor. If a specific IDE needs a different layout later, change that module.

## Project structure changes

```text
src/aiadev/platforms/codex.py         (new)
src/aiadev/platforms/opencode.py      (new)
src/aiadev/platforms/gemini.py        (new)
tests/test_install_codex.py           (new)
tests/test_install_opencode.py        (new)
tests/test_install_gemini.py          (new)
tests/test_install_e2e.py             (modified — one new round-trip)
src/aiadev/install_engine.py          (modified — register three platforms)
src/aiadev/commands/install.py        (modified — alias map)
```

## Phase breakdown

### Phase 1 — Three handler modules + wiring

- Copy-adapt `platforms/cursor.py` into `codex.py`, `opencode.py`, `gemini.py` with the per-platform targets.
- Register all three in `_PLATFORMS` and `_PLATFORM_ALIASES`.
- Add per-handler unit tests.

### Phase 2 — E2E + docs

- One e2e round-trip (pick Codex; OpenCode and Gemini are mechanically identical and covered by unit tests).
- CHANGELOG [Unreleased] Added entry.
- README install example mentions the three new `--platform` values.

## Complexity tracking

Empty.
