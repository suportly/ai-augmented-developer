# Implementation plan: per-home install scope

**Branch:** `feature/scope-user-per-home-install`
**Date:** 2026-04-14
**Spec:** [spec.md](./spec.md)
**Plan version:** 1

---

## Summary

Add `--scope {user,project}` to `aiadev install`. Project scope is unchanged. User scope writes skills under `~/.<platform>/skills/` and tracks them in `~/.aiadev/installed.yaml`. Agent files and constitutions are intentionally skipped under user scope — they stay project-local. Three tasks, ~5 hours total.

## Technical context

| Field | Value |
|---|---|
| Language / runtime | Python 3.11+ |
| New deps | none |
| Storage | adds `~/.aiadev/installed.yaml` — same schema |
| Testing | existing test infra (pytest + CliRunner + tmp_path) |

## Constitution check

| Article | Applies? | Status | Evidence |
|---|---|---|---|
| I. Spec-first | Yes | PASS | `spec.md` approved, no markers |
| II. Test-first | Yes | PASS | unit tests precede engine + handler changes |
| III. Simplicity | Yes | PASS | no new abstraction beyond one extra kwarg |
| IV. Evidence | Yes | PASS | CI matrix + round-trip test |
| V. Provider pattern | No | N/A | no external dep |
| VI. Privacy | Yes | PASS | paths stay inside `$HOME`; user explicitly opts in |
| VII. Attribution | Yes | PASS | original code |

## Architecture decisions

**Decision:** Scope lives in the engine, not the handler. The engine picks `install_root` from the scope and passes it to the handler; the handler exposes `user_scope_supported(role)` to let the engine filter artifacts.
**Rationale:** Platforms differ in which roles make sense per scope (agent files never make sense at user scope); keeping that knowledge in the handler lets each platform evolve independently.

**Decision:** `~/.aiadev/installed.yaml` for user scope, `<project>/.aiadev/installed.yaml` for project. Separate manifests even when the same preset is installed at both scopes.
**Rationale:** Idempotency and uninstall rely on the manifest identifying only the files written by that scope. Mixing them would break drift detection.

**Decision:** Unsupported-at-user-scope artifacts are reported via a new `InstallReport.skipped_unsupported` list. Not an error.
**Rationale:** The user typed `--scope user` expecting skills; refusing the entire install because the preset also declares an agent file would be surprising. A clear note in the report covers it.

**Decision:** OpenCode user path is `~/.opencode/skills/` (not `~/.config/opencode/`).
**Rationale:** Consistency with the other four handlers' dot-prefix user-level convention. XDG devotees can symlink.

## Project structure changes

```text
src/aiadev/install_engine.py        (modified — scope kwarg, user manifest path)
src/aiadev/commands/install.py      (modified — --scope option)
src/aiadev/platforms/claude_code.py (modified — user_scope_supported + scope-aware resolve_target)
src/aiadev/platforms/cursor.py      (modified — same)
src/aiadev/platforms/codex.py       (modified — same)
src/aiadev/platforms/opencode.py    (modified — same)
src/aiadev/platforms/gemini.py      (modified — same)
tests/test_install_engine.py        (extended — user scope cases)
tests/test_install.py               (extended — CLI --scope cases)
tests/test_install_e2e.py           (extended — user-scope round-trip)
tests/test_install_<platform>.py    (extended — per-handler user paths)
```

No new modules.

## Phase breakdown

### Phase 1 — Handler contract + path updates

- Each platform handler gains `user_scope_supported(role)` (returns `role == "skill"`) and accepts `scope` on `resolve_target`.
- Per-user skill paths:
  - claude-code: `~/.claude/skills/<name>/SKILL.md`
  - cursor:      `~/.cursor/skills/<name>/SKILL.md`
  - codex:       `~/.codex/skills/<name>/SKILL.md`
  - opencode:    `~/.opencode/skills/<name>/SKILL.md`
  - gemini:      `~/.gemini/skills/<name>/SKILL.md`
- Unit tests per handler.

### Phase 2 — Engine + CLI

- `install_engine.install(...)` takes `scope: Literal["project","user"] = "project"`.
- `InstallReport.skipped_unsupported` records artifacts skipped because the handler reports the role as unsupported at user scope.
- `commands/install.py` adds `--scope {user,project}`; `--project-root` is ignored under `--scope user` (with a one-line warning).
- Engine picks `install_root = Path.home()` when scope is user; manifest path is `~/.aiadev/installed.yaml`.

### Phase 3 — E2E + docs + release

- One round-trip test under user scope in an isolated tmpdir acting as `$HOME` (via `monkeypatch.setenv("HOME", ...)` + tmp_path).
- CHANGELOG [Unreleased] Added entry.
- README install block documents `--scope user`.
- Release as v0.6.0.

## Risks and mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Test pollutes real `$HOME` | Medium | High | All user-scope tests monkeypatch `HOME` to a tmp_path. |
| User confuses scopes when project + user coexist | Medium | Low | Report header names the scope; uninstall refuses to delete files not in the requested scope's manifest. |
| Platform support for user-level skills differs | Low | Low | Paths mirror the per-project convention; IDE config may need a one-liner (documented). |

## Complexity tracking

Empty.

## Hand-off to `tasks`

- [x] Constitution Check populated.
- [x] Project structure delta accurate.
- [x] No waivers.
