# Implementation plan: aiadev install --interactive

**Branch:** `feature/install-interactive`
**Date:** 2026-04-14
**Spec:** [spec.md](./spec.md)
**Plan version:** 1

---

## Summary

Replace the v0.2 `aiadev install` stub with a working installer that renders a preset into the current project. Scope of this plan: Claude Code target only (the most common use case), interactive + non-interactive modes, idempotent re-install, and uninstall. Split into six phases, approximately 10–14 hours of work.

## Technical context

| Field | Value |
|---|---|
| Active preset | None (this work is on the framework itself) |
| Language / runtime | Python 3.11+ |
| Primary dependencies | existing (`click`, `pyyaml`, `jsonschema`, `rich`); new: none |
| Storage | `.aiadev/installed.yaml` at the consumer project root |
| Testing framework | pytest + `click.testing.CliRunner` |
| Target platform(s) | Claude Code (first release); Cursor/Codex/OpenCode/Gemini deferred to v0.4 |
| Performance budget | `aiadev install` under 2 seconds wall time on a warm filesystem |
| Security considerations | No network calls; variable values written to `.aiadev/installed.yaml` — users choose whether to commit |

## Constitution check

| Article | Applies? | Status | Evidence |
|---|---|---|---|
| I. Spec-first | Yes | PASS | `spec.md` in this directory; clarifications resolved with defaults |
| II. Test-first | Yes | PASS | every task below begins with a failing test; see `tasks.md` |
| III. Simplicity | Yes | PASS | single platform (Claude Code) in this release; no provider abstraction until a second platform is implemented |
| IV. Evidence over claims | Yes | PASS | CI runs the new tests on both Python 3.11 and 3.12 via the existing matrix |
| V. Provider pattern | No | N/A | no external network dependency is introduced |
| VI. Privacy by design | Yes | PASS | variable values (including GCP project ids) go to `.aiadev/installed.yaml`; gitignored by default, opt-in commit documented in CONTRIBUTING |
| VII. Attribution | Yes | PASS | all new code is original; `CREDITS.md` untouched |

## Architecture decisions

**Decision:** The install engine is a single module, `src/aiadev/install_engine.py`, with pure functions. The `install` command in `src/aiadev/commands/install.py` becomes a thin click wrapper around it.
**Rationale:** Pure functions are trivially testable; the command stays small; an eventual `aiadev install --preset <name> --platform cursor` only needs a new platform handler, not a CLI rewrite.
**Trade-offs:** Slightly more files than a single monolithic command module. Acceptable — the install logic deserves its own home.

**Decision:** Placeholders are substituted with a single, left-to-right `str.replace` pass per file. No Jinja2, no regex engines.
**Rationale:** YAGNI. Templates only need literal `{{KEY}}` replacement. Adding Jinja2 is an Article III violation without a real case for it.
**Trade-offs:** Users cannot escape a literal `{{FOO}}` in a variable value. Documented; if a real case arises, revisit.

**Decision:** The install manifest is YAML, committed by default, at `.aiadev/installed.yaml`. Schema mirrors `preset.yaml` but records resolved values and file SHA-256 hashes.
**Rationale:** Rebuilds the state needed by `doctor`, `--uninstall`, and future update flows. YAML for consistency; human-readable for review.
**Trade-offs:** Manifest grows proportional to skill count; acceptable (a few KB per preset).

**Decision:** Files written by the install carry an install marker comment in their trailing line (e.g. `<!-- aiadev-installed: preset=django-drf-react sha=... -->`) on markdown files, equivalent on others. Used for drift detection on re-install.
**Rationale:** Lets re-install detect user edits without storing entire file copies.
**Trade-offs:** Adds a one-line footer to installed files. Documented.

## Project structure changes

```text
src/aiadev/install_engine.py                 (new)
src/aiadev/install_manifest.py               (new)
src/aiadev/placeholders.py                   (new — pure substitution)
src/aiadev/platforms/__init__.py             (new)
src/aiadev/platforms/claude_code.py          (new)
src/aiadev/commands/install.py               (rewritten — thin wrapper)
tests/test_install_engine.py                 (new)
tests/test_install_manifest.py               (new)
tests/test_placeholders.py                   (new)
tests/test_install_claude_code.py            (new)
tests/fixtures/mini-preset/                  (new — tiny preset for tests)
schemas/install-manifest.schema.json         (new)
CHANGELOG.md                                 (updated — [Unreleased])
```

## Phase breakdown

### Phase 1 — Placeholder substitution (pure functions)

- `placeholders.py`: `substitute(text, values)` and `find_unresolved(text)`.
- Edge cases: repeated placeholders, placeholders inside code fences, values containing `{{`.
- Output: a module with 100% test coverage.

### Phase 2 — Manifest read/write

- `install_manifest.py`: dataclasses for `InstalledPreset` and `InstalledFile`.
- Read, write, validate against `schemas/install-manifest.schema.json`.
- Atomic write via `tempfile.NamedTemporaryFile` + `os.replace`.

### Phase 3 — Claude Code platform handler

- `platforms/claude_code.py`: resolves the target path for each artifact (agent file → `CLAUDE.md` at project root; skills → `.claude/skills/<name>/SKILL.md`; plugin manifest → `.claude-plugin/plugin.json`).
- Updates `.claude-plugin/plugin.json` to register newly-installed skills.
- Skips artifacts not relevant to Claude Code (e.g. Cursor-specific files when they arrive).

### Phase 4 — Install engine

- `install_engine.py`: orchestrates the pipeline — load preset, collect variables, substitute, write, update manifest.
- Modes: interactive, non-interactive, dry-run, uninstall, force.
- Returns a structured `InstallReport`.

### Phase 5 — CLI wiring

- `commands/install.py`: options `--preset`, `--platform`, `--vars`, `--non-interactive`, `--dry-run`, `--uninstall`, `--force`, `--allow-unresolved`.
- `rich` output: progress, diffs, success/failure summaries.

### Phase 6 — End-to-end smoke + CI

- Round-trip test: `install` → `doctor` → `uninstall` on a throwaway tmpdir.
- CI adds one job running the smoke test on Python 3.11.
- Dogfood: install `django-drf-react` into a generated demo project under `tests/fixtures/demo-project/` (gitignored post-test).

## Risks and mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| User already has `CLAUDE.md` from hand-editing | High | Medium | Merge-don't-overwrite by default; offer `--force`; show diff first |
| Preset author forgets a placeholder | Medium | High | `install` runs `find_unresolved` after substitution and fails unless `--allow-unresolved` |
| Variable value contains `{{` | Low | Low | Documented; single-pass substitution prevents accidental re-render |
| Manifest schema drift between versions | Medium | Medium | Manifest carries `aiadev_version`; re-install migrates older manifests via a one-shot upgrade step |

## Complexity tracking

Empty — no framework article is waived.

| Article waived | Reason | Alternatives considered | Reviewer |
|---|---|---|---|
| | | | |

## Hand-off to `tasks`

The next skill is `tasks`. It consumes this plan and produces `tasks.md`.
Pre-conditions before hand-off:

- [x] Constitution Check is fully populated, no blank rows.
- [x] Complexity tracking is filled or empty-and-justified.
- [x] Project structure delta is accurate.
