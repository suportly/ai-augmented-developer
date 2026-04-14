# Tasks: PyPI packaging and publish

**Branch:** `feature/pypi-packaging-and-publish`
**Plan:** [plan.md](./plan.md)
**Generated:** 2026-04-14

---

## Task list

### T001 — Bundle data dirs in the wheel

- **Status:** pending
- **Depends on:** —
- **Files:**
  - modify: `pyproject.toml`
  - create: `MANIFEST.in`
- **Spec scenarios:** Story 3 scenarios 1–2
- **Acceptance:**
  - [ ] `python -m build` produces both sdist and wheel without warnings about missing files.
  - [ ] The wheel contains `templates/`, `schemas/`, and `presets/` directories under the package.
  - [ ] In a fresh venv, `pip install <wheel>` then `aiadev --version` then `aiadev doctor` all succeed.
  - [ ] Commit: `feat(pypi): T001 bundle data dirs in the wheel`.

### T002 — Publish workflow

- **Status:** pending
- **Depends on:** T001
- **Files:**
  - create: `.github/workflows/publish.yml`
- **Spec scenarios:** Story 2 scenarios 1–2
- **Acceptance:**
  - [ ] `publish.yml` triggers on `release: published`.
  - [ ] Two jobs: `build` (artifact upload) and `publish` (download + `pypa/gh-action-pypi-publish@release/v1`).
  - [ ] `publish` job uses `environment: pypi` and `permissions.id-token: write` for OIDC trusted publishing.
  - [ ] Workflow YAML parses; documented as not yet exercised end-to-end (first real publish is the v0.7.0 release that ships this PR).
  - [ ] Commit: `feat(pypi): T002 publish workflow`.

### T003 — Release process docs + changelog

- **Status:** pending
- **Depends on:** T002
- **Files:**
  - modify: `CONTRIBUTING.md`
  - create: `docs/RELEASING.md`
  - modify: `CHANGELOG.md`
- **Acceptance:**
  - [ ] `CONTRIBUTING.md` release section points at `docs/RELEASING.md`.
  - [ ] `docs/RELEASING.md` covers: tagging, creating the GitHub release, the one-time pypi.org trusted-publisher setup, troubleshooting common failure modes.
  - [ ] CHANGELOG [Unreleased] documents PyPI installability and the workflow.
  - [ ] Commit: `docs(pypi): T003 release process and changelog`.
