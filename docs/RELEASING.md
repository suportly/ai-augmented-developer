# Releasing aiadev

The package is published to [PyPI](https://pypi.org/project/aiadev/) by
the `.github/workflows/publish.yml` workflow on every GitHub release
event. Authentication uses **OIDC trusted publishing** — no long-lived
API token lives in this repository.

This document covers the **one-time setup** (per-maintainer), the
**routine release flow** (every release), and the most common
**failure modes**.

## One-time setup

You only do this once for the lifetime of the package on PyPI.

### 1. Reserve the project name

If the package has never been uploaded:

1. Build a wheel locally (`python scripts/sync_assets.py && python -m build`).
2. Upload the very first release manually with a token to register the
   project name. Subsequent releases are automated.

```bash
pip install --upgrade twine
twine upload --repository pypi dist/aiadev-0.6.0-py3-none-any.whl dist/aiadev-0.6.0.tar.gz
```

(You will be prompted for a username `__token__` and an API token created
at <https://pypi.org/manage/account/token/>.)

If the project already exists on PyPI under a different owner, change
the package name in `pyproject.toml` (`name = "ai-augmented-developer"`
is the agreed fallback) and adjust this document plus the CHANGELOG
before continuing.

### 2. Configure the trusted publisher on pypi.org

On <https://pypi.org/manage/project/aiadev/settings/publishing/> click
**Add a new pending publisher** (or **trusted publisher** if the
project already exists) with:

| Field | Value |
|---|---|
| PyPI Project Name | `aiadev` |
| Owner | `suportly` |
| Repository name | `ai-augmented-developer` |
| Workflow name | `publish.yml` |
| Environment name | `pypi` |

### 3. Configure the GitHub environment

On <https://github.com/suportly/ai-augmented-developer/settings/environments>:

1. **New environment** -> name `pypi`.
2. (Optional) Add a deployment protection rule requiring an approver
   on every release; without it, every triggered release publishes.
3. Save.

The `pypi` environment name **must** match what you typed on pypi.org.

## Routine release

After the one-time setup is complete:

1. Make sure `main` is green and contains everything you want to ship.
2. Bump the version on `main`:

   ```bash
   git checkout main && git pull
   echo "0.7.0" > VERSION
   # Move the [Unreleased] CHANGELOG entries to a new [0.7.0] section.
   git add VERSION CHANGELOG.md
   git commit -m "chore(release): 0.7.0"
   ```

3. Tag and push:

   ```bash
   git tag -a v0.7.0 -m "Release 0.7.0 — <one line summary>"
   git push origin main
   git push origin v0.7.0
   ```

4. Create the GitHub release for the tag (this is what triggers the
   workflow):

   ```bash
   gh release create v0.7.0 --title "v0.7.0 — <one line>" \
     --notes "$(awk '/^## \[0\.7\.0\]/{flag=1; next} /^## \[/{flag=0} flag' CHANGELOG.md)"
   ```

5. Watch the publish workflow:

   ```bash
   gh run watch --exit-status $(gh run list --workflow publish.yml --limit 1 --json databaseId -q '.[0].databaseId')
   ```

   On success, `pip install aiadev==0.7.0` works for everyone.

## Failure modes

### `400 File already exists`

PyPI does not allow re-uploading the same version. Fix: bump the
version in `VERSION`, redo step 2 onward.

### `403 invalid-publisher`

Trusted publisher is not configured (or the workflow file path /
environment name does not match what you typed on pypi.org). Re-check
the **One-time setup** section, then re-run the workflow:

```bash
gh run rerun --failed
```

### Workflow does not start at all

Confirm the release was actually published (not "draft"):

```bash
gh release view v0.7.0 --json isDraft
```

If `isDraft: true`, the workflow does not run. Use
`gh release edit v0.7.0 --draft=false` to publish.

### Wheel is missing assets

If end users see `FrameworkNotFound` after `pip install aiadev`,
`scripts/sync_assets.py` did not run before `python -m build`. The CI
workflow runs it automatically; for local builds, run it manually
before invoking `build`.

## Verifying a release end-to-end

After publish, in any directory:

```bash
pipx install aiadev==0.7.0
aiadev --version
aiadev doctor
mkdir /tmp/smoke && cd /tmp/smoke
aiadev install --preset lean --non-interactive --vars PROJECT_NAME=Smoke
ls .aiadev/installed.yaml CLAUDE.md
```

If all four commands succeed, the release is healthy.
