# Tasks: per-home install scope

**Branch:** `feature/scope-user-per-home-install`
**Plan:** [plan.md](./plan.md)
**Generated:** 2026-04-14

---

## Task list

### T001 — Handler scope support

- **Status:** pending
- **Depends on:** —
- **Files:**
  - modify: `src/aiadev/platforms/claude_code.py`
  - modify: `src/aiadev/platforms/cursor.py`
  - modify: `src/aiadev/platforms/codex.py`
  - modify: `src/aiadev/platforms/opencode.py`
  - modify: `src/aiadev/platforms/gemini.py`
  - extend: `tests/test_install_claude_code.py`
  - extend: `tests/test_install_cursor.py`
  - extend: `tests/test_install_codex.py`
  - extend: `tests/test_install_opencode.py`
  - extend: `tests/test_install_gemini.py`
- **Spec scenarios:** Story 1 scenario 1, Story 3 scenario 1
- **Acceptance:**
  - [ ] Each handler has `user_scope_supported(role)` returning `True` only for `skill`.
  - [ ] `resolve_target(role, name, install_root, *, scope="project")` returns correct paths for both scopes. Under `scope="user"`, `install_root` is `Path.home()`; under `scope="project"` it's the project dir (current behaviour).
  - [ ] Unit tests cover both scopes per handler.
  - [ ] 100% coverage on the per-handler scope logic.
  - [ ] Commit: `feat(scope): T001 per-handler user-scope support`.

### T002 — Engine + CLI scope

- **Status:** pending
- **Depends on:** T001
- **Files:**
  - modify: `src/aiadev/install_engine.py`
  - modify: `src/aiadev/commands/install.py`
  - extend: `tests/test_install_engine.py`
  - extend: `tests/test_install.py`
- **Spec scenarios:** Story 1 scenarios 1–3, Story 2 scenarios 1–2, Story 3 scenario 1
- **Acceptance:**
  - [ ] Engine `install(...)` accepts `scope` kwarg; derives `install_root` from scope.
  - [ ] `InstallReport` gains `skipped_unsupported: list[Path]`.
  - [ ] Under `scope="user"`, artifacts whose role returns `user_scope_supported=False` are added to `skipped_unsupported` with a one-line reason and not written/recorded.
  - [ ] User scope manifest at `~/.aiadev/installed.yaml`; project scope unchanged.
  - [ ] Tests (engine + CLI) use `monkeypatch.setenv("HOME", ...)` to isolate; NO real `$HOME` mutation.
  - [ ] CLI `--scope` flag documented; `--project-root` is ignored with warning under user scope.
  - [ ] Commit: `feat(scope): T002 engine + CLI scope`.

### T003 — E2E + docs + release

- **Status:** pending
- **Depends on:** T002
- **Files:**
  - extend: `tests/test_install_e2e.py`
  - modify: `CHANGELOG.md`
  - modify: `README.md`
- **Acceptance:**
  - [ ] E2E round-trip under `--scope user` installs `mobile-ops` into a fake `$HOME` (tmp_path), asserts skills at `~/.codex/skills/`, no agent files at home, uninstall clean.
  - [ ] Project-scope e2e tests still pass.
  - [ ] CHANGELOG [Unreleased] Added entry.
  - [ ] README documents `--scope user` with an example.
  - [ ] Commit: `feat(scope): T003 e2e + docs`.
