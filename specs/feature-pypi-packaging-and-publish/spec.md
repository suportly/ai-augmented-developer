# Feature specification: PyPI packaging and publish

**Branch:** `feature/pypi-packaging-and-publish`
**Created:** 2026-04-14
**Status:** Draft
**Spec ID:** 0005

---

## Problem

`aiadev` is only installable today through `pip install -e git+https://github.com/suportly/ai-augmented-developer.git#egg=aiadev`. Users without the framework checked out cannot install it; CI bootstrap pipelines pay the git-clone cost on every run. There is no `pip install aiadev`.

## Users and stakeholders

- End users who want a one-line install (`pip install aiadev` / `pipx install aiadev`).
- CI authors who want a fixed, cached wheel.
- Framework maintainers — completing the distribution story.

## Success criteria

- `python -m build` produces a valid sdist (`.tar.gz`) and wheel (`.whl`) for `aiadev` from the current source tree.
- A consumer in a fresh venv runs `pip install <built-wheel>` and `aiadev --version` succeeds.
- The wheel ships `templates/`, `schemas/`, and `presets/` so `aiadev install` works without a framework checkout (these are required for `find_framework_root` to succeed via package fallback).
- A GitHub Actions workflow publishes the artifacts to PyPI on every `release: published` event using OIDC trusted publishing — no API tokens stored in the repo.
- The release process is documented in `CONTRIBUTING.md`.

## Non-goals

- Publishing the framework's Markdown (skills, presets, templates) as a separate package or registry. They ship inside the `aiadev` wheel.
- Automating the trusted-publisher configuration on pypi.org — that requires an interactive browser session by the package owner. Documented as a one-time prerequisite.
- Publishing to TestPyPI on every commit. The publish workflow runs only on real release events.
- Pre-1.0 stability guarantees beyond what the changelog already promises.

## User stories

### Story 1 — Install from PyPI (P1)

As a developer who wants the framework on my machine,
I want `pipx install aiadev` (or `pip install aiadev` in a venv)
so that the CLI works without cloning the repo.

**Acceptance scenarios:**

1. Given the wheel published to PyPI, When I run `pipx install aiadev` in a clean shell, Then `aiadev --version` prints the installed version.
2. Given the same install, When I run `aiadev install --preset lean --non-interactive --vars PROJECT_NAME=Demo` in any directory, Then it succeeds and writes a manifest under `.aiadev/`.

### Story 2 — Maintainer cuts a release (P1)

As the framework maintainer,
I want the GitHub Actions workflow to publish to PyPI when I create a GitHub release
so that I do not handle API tokens or run `twine upload` locally.

**Acceptance scenarios:**

1. Given trusted publishing is configured on pypi.org for this repo, When I create a release on GitHub for tag `v0.7.0`, Then the `publish` workflow runs and uploads the wheel + sdist for `aiadev==0.7.0` to pypi.org/project/aiadev/.
2. Given a release with no version bump (tag matches an already-published version), When the workflow runs, Then PyPI rejects the upload and the workflow fails loudly. (PyPI prevents version reuse.)

### Story 3 — Build verifiable locally (P2)

As a contributor,
I want `python -m build` to succeed from a clean checkout
so that I can sanity-check the artifacts before opening a PR.

**Acceptance scenarios:**

1. Given a fresh clone, When I run `pip install build && python -m build`, Then `dist/aiadev-<version>-py3-none-any.whl` and `dist/aiadev-<version>.tar.gz` are produced without warnings about missing files.
2. Given the built wheel, When I `pip install` it into an empty venv and run `aiadev doctor`, Then it succeeds (templates, schemas, and presets are inside the wheel).

## Design decisions (resolved during spec)

- **Trusted publishing only.** No `PYPI_API_TOKEN` secret. Setup steps for the maintainer to configure trusted publishing on pypi.org are documented but not automated.
- **Trigger:** `release: published` on GitHub. Tagging alone does not publish — explicitly creating a GitHub release is the deliberate action.
- **Bundled assets:** `templates/`, `schemas/`, and `presets/` are declared via `setuptools.package-data` so they ship inside the wheel. `find_framework_root`'s package-location fallback (added in v0.3) already covers the runtime resolution.
- **Wheel name and version:** `aiadev` (already declared in `pyproject.toml`); version sourced from `VERSION` (already wired).
- **Python support:** 3.11+ (already declared). No 3.10 backport.

## Data touched

- `pyproject.toml` — extended with `setuptools.package-data` to ship non-Python assets and any missing classifiers.
- `MANIFEST.in` — new (or `pyproject.toml`-only equivalent) to include `templates/`, `schemas/`, `presets/` in the sdist.
- `.github/workflows/publish.yml` — new workflow.
- `CONTRIBUTING.md` — release process documented.

## Out-of-band effects

- A GitHub release event triggers an upload to PyPI. After v0.7's first release, all subsequent tagged releases publish automatically. The maintainer must do the trusted-publisher configuration on pypi.org **once** before the first publish (otherwise the workflow fails with an actionable error).

## Open risks

- The `aiadev` name on PyPI may be taken. If so, the package becomes `ai-augmented-developer` (or another fallback) and we update `pyproject.toml` + docs in this PR.
- Including 4 MB of presets/templates in the wheel may surprise users — wheel size is ~5 MB upper bound. Acceptable for v0.7; future work may split into a thin runtime + optional content packages.
- Trusted publishing requires the workflow file path on the default branch to match the configured publisher. Documented in the release process.

## Traceability

- Originating issue: v0.6.0 release notes "what's next".
- Related specs: `specs/feature-install-interactive/` (CLI lives here, including the `find_framework_root` package-location fallback that makes the wheel runtime work).
