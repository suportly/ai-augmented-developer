# Implementation plan: PyPI packaging and publish

**Branch:** `feature/pypi-packaging-and-publish`
**Date:** 2026-04-14
**Spec:** [spec.md](./spec.md)
**Plan version:** 1

---

## Summary

Make `aiadev` installable via `pip install aiadev` and publish it via GitHub Actions on release. Three tasks, ~3 hours.

## Technical context

| Field | Value |
|---|---|
| Build backend | setuptools (already in `pyproject.toml`) |
| Python target | 3.11+ (already declared) |
| Asset bundling | `setuptools.package-data` + `MANIFEST.in` |
| Publish trigger | `release: published` (GitHub Actions) |
| Auth | OIDC trusted publishing (no API tokens) |

## Constitution check

| Article | Applies? | Status | Evidence |
|---|---|---|---|
| I. Spec-first | Yes | PASS | spec approved |
| II. Test-first | Yes | PASS | build verification covers each task |
| III. Simplicity | Yes | PASS | one workflow + one config change; no new abstraction |
| IV. Evidence | Yes | PASS | local `python -m build` + fresh-venv install transcripts |
| V. Provider pattern | No | N/A | no external runtime dep |
| VI. Privacy | Yes | PASS | no secrets stored in repo (OIDC) |
| VII. Attribution | Yes | PASS | original code |

## Architecture decisions

**Decision:** Bundle `templates/`, `schemas/`, and `presets/` inside the wheel.
**Rationale:** `aiadev` resolves these via `find_framework_root`'s package-location fallback (v0.3). Without bundling, `pip install aiadev` would produce a CLI that fails the moment a user runs `aiadev install --preset lean`.
**Trade-offs:** Wheel size grows to ~5 MB. Acceptable; can be split later if it becomes a problem.

**Decision:** Publish only on `release: published` (not on tag push).
**Rationale:** The release event is the deliberate, auditable action. Tags created during development should not publish.
**Trade-offs:** Maintainer must explicitly create the release after tagging. Documented.

**Decision:** Trusted publishing via PyPI's OIDC integration.
**Rationale:** Eliminates the need to store a long-lived API token in the repo. The first publish requires a one-time pypi.org configuration step (documented).
**Trade-offs:** First publish requires the maintainer to be logged into pypi.org and configure the publisher. Subsequent publishes are fully automated.

## Project structure changes

```text
pyproject.toml                       (modified — package-data, classifiers)
MANIFEST.in                          (new — include data dirs in sdist)
.github/workflows/publish.yml        (new — release-triggered publish)
CONTRIBUTING.md                      (modified — release process)
docs/RELEASING.md                    (new — step-by-step for maintainers)
```

## Phase breakdown

### Phase 1 — Packaging metadata + asset bundling

- Update `pyproject.toml` to declare `package-data` for `templates/`, `schemas/`, `presets/`.
- Add `MANIFEST.in` so the sdist includes the same dirs.
- Build locally with `python -m build`; install the wheel into a fresh venv; verify `aiadev doctor` works.

### Phase 2 — Publish workflow

- New `.github/workflows/publish.yml`:
  - `build` job: checkout, setup-python, `pip install build`, `python -m build`, upload artifact.
  - `publish` job: download artifact, publish via `pypa/gh-action-pypi-publish@release/v1` with `id-token: write` permission and the `pypi` environment.
- Trigger: `on: release: types: [published]`.

### Phase 3 — Docs + release prep

- `CONTRIBUTING.md`: release process subsection (tag → release → workflow runs).
- `docs/RELEASING.md`: detailed maintainer guide including the one-time pypi.org trusted-publisher config.
- CHANGELOG entry under [Unreleased].

## Risks and mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| `aiadev` name taken on PyPI | Medium | Medium | Spec lists fallback name; PR amends `pyproject.toml` if needed before merging |
| Trusted publisher misconfigured at first publish | Medium | Low | Workflow fails loud with the pypa action's clear error; docs guide the fix |
| Wheel missing data files | Low | High | Phase 1 verification step installs the wheel into a fresh venv and runs `aiadev doctor` before the workflow exists |

## Complexity tracking

Empty.
