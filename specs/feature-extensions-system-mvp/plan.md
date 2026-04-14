# Implementation plan: extensions system MVP

**Branch:** `feature/extensions-system-mvp`
**Date:** 2026-04-14
**Spec:** [spec.md](./spec.md)
**Plan version:** 1

---

## Summary

Add `aiadev extension <add|list|remove>` and teach the install engine to pick presets up from `~/.aiadev/extensions/<name>/presets/`. Three modules + one new schema + one new command file. Four tasks, ~6 hours.

## Technical context

| Field | Value |
|---|---|
| Language / runtime | Python 3.11+ |
| New dependencies | none (stdlib `subprocess` for git) |
| Storage | `~/.aiadev/extensions/<name>/` (clones) + `~/.aiadev/extensions/registry.yaml` |
| Testing | pytest + CliRunner + monkeypatched HOME |

## Constitution check

| Article | Applies? | Status | Evidence |
|---|---|---|---|
| I. Spec-first | Yes | PASS | spec approved |
| II. Test-first | Yes | PASS | each task starts with a failing test |
| III. Simplicity | Yes | PASS | no dependency resolver, no signing — git clone + registry |
| IV. Evidence | Yes | PASS | round-trip test installs an extension from a tmpdir-served git remote and asserts the engine resolves its preset |
| V. Provider pattern | No | N/A | no external API |
| VI. Privacy | Yes | PASS | clone targets are explicit user input; no automatic background fetches |
| VII. Attribution | Yes | PASS | original code |

## Architecture decisions

**Decision:** Extensions are git URLs; we clone with `git clone --depth 1`. No remote registry server.
**Rationale:** Extension authors already publish on GitHub/GitLab/etc. A central registry adds operational burden without solving a problem the MVP needs.

**Decision:** Schema-validate `extension.yaml` at install time, again at registry load time.
**Rationale:** Bad manifests should fail loudly during `extension add` (so the author hears about it), and never crash unrelated commands later.

**Decision:** Built-in presets win over extension presets on name collision.
**Rationale:** A user installing the framework expects the bundled `lean` and `django-drf-react` to behave as documented. Extensions can shadow the bundled list only by being explicitly preferred via a future flag (out of MVP).

**Decision:** Storage under the existing `~/.aiadev/` directory.
**Rationale:** Already created by v0.6 for the user-scope manifest. Reusing it keeps the user's home tidy.

## Project structure changes

```text
src/aiadev/extensions.py                          (new)
src/aiadev/commands/extension.py                  (new)
schemas/extension-manifest.schema.json            (new)
tests/test_extensions.py                          (new)
tests/test_extension_command.py                   (new)
tests/fixtures/extensions/sample-extension/       (new — tiny extension used by the tests)

src/aiadev/cli.py                                 (modified — register the extension subcommand)
src/aiadev/install_engine.py                      (modified — fall back to extension presets)
src/aiadev/commands/install.py                    (modified — preset path resolution)
.github/workflows/validate.yml                    (no change; existing pytest job covers the new tests)
```

## Phase breakdown

### Phase 1 — Extensions module

- `extensions.py`: `add(url)`, `list_all()`, `remove(name)`, `find_preset(preset_name)`.
- Registry IO with atomic write (mirroring `install_manifest.py`'s pattern).
- Manifest schema validation with a clear error class.

### Phase 2 — CLI subcommand

- `commands/extension.py`: `aiadev extension add|list|remove`.
- `cli.py` registers the new command group.

### Phase 3 — Engine integration

- `install_engine.install(...)` (and the install command's preset resolution) consult `extensions.find_preset(name)` after looking under the framework's `presets/`. Built-in wins on collision; report a one-line note when an extension preset is shadowed.

### Phase 4 — Tests + docs + release prep

- Round-trip test using a tmpdir-served bare git repo as the extension source (no internet needed).
- CHANGELOG [Unreleased] entry; README documents `aiadev extension`.

## Risks and mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| `git` not on PATH in some environments | Low | Medium | Detect and fail with a clear message naming the missing tool |
| Concurrent `aiadev extension add` corrupts the registry | Low | Low | Atomic write (tempfile + os.replace); same pattern as install_manifest |
| Extension contains malicious skill content | Real | Out of scope for MVP — the user accepts content the moment they `aiadev extension add`. Documented in the spec's "Open risks". |

## Complexity tracking

Empty.
