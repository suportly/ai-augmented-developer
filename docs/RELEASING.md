# Releasing aiadev

The package is published to [PyPI](https://pypi.org/project/aiadev/) by
the `.github/workflows/publish.yml` workflow on every GitHub release
event. Authentication uses **OIDC trusted publishing** — no long-lived
API token lives in this repository.

Two more artefacts have their own release lanes, both driven by a version
bump in their `package.json` on `main`: the VS Code extension
(`.github/workflows/vscode-extension.yml`, Marketplace, `VSCE_PAT` secret)
and the npm package `@aiadev/smart-mcp-proxy`
(`.github/workflows/smart-mcp-proxy.yml`, npm registry, `NPM_TOKEN` secret;
see [npm: smart-mcp-proxy](#npm-smart-mcp-proxy) at the end).

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
| --- | --- |
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

## Releasing the VS Code extension

The `aiadev Spec Explorer` extension (`vscode-extension/`) auto-releases
whenever a new version lands on `main`. There is no manual tag step.

### Routine release

1. On a feature branch, edit `vscode-extension/package.json` to bump
   `version`, and add a matching `## [X.Y.Z] - YYYY-MM-DD` block to
   `vscode-extension/CHANGELOG.md`.
2. Open a PR, get review, merge to `main`.

That's it. The `vscode-extension` workflow on `main` push reads
`vscode-extension/package.json`, checks whether the tag
`vscode-extension-v<version>` already exists on origin, and if not:

- Builds and packages the VSIX.
- Creates and pushes the `vscode-extension-v<version>` tag.
- Publishes to the VS Code Marketplace (when `VSCE_PAT` is configured).
- Creates a GitHub release with the VSIX attached.

If the tag already exists, the workflow skips silently — every main
push is idempotent.

### Manual re-cut

Pushing a `vscode-extension-v*` tag directly still works, e.g. to
re-publish an existing version after a Marketplace outage:

```bash
git tag -a vscode-extension-v0.0.11 -m "re-cut 0.0.11"
git push origin vscode-extension-v0.0.11
```

### Why this matters

Until 2026-05-14 the workflow only fired on tag push. When PR #35
bumped to 0.0.11 without a matching tag (the bump was bundled inside
a feature PR), the Marketplace stayed on 0.0.10 and the gap was only
caught by a user report. The auto-release flow above eliminates that
failure mode.


## npm: smart-mcp-proxy

`packages/smart-mcp-proxy` ships to the npm registry as
`@aiadev/smart-mcp-proxy` through `.github/workflows/smart-mcp-proxy.yml`.
The lane mirrors the VS Code extension: every push and PR touching the
package builds, tests and packs it; a **main push whose `package.json`
version has no `smart-mcp-proxy-v<version>` tag yet** publishes and then
tags; a manual `smart-mcp-proxy-v*` tag push re-cuts a release.

### One-time setup

1. On [npmjs.com](https://www.npmjs.com/) make sure you own the `aiadev`
   scope: either create the **organization** `aiadev` (free for public
   packages) or rename the package in `packages/smart-mcp-proxy/package.json`
   to a scope you own (`@<your-user>/smart-mcp-proxy`) or to the unscoped
   `smart-mcp-proxy`. The workflow reads the name from `package.json`.
2. Create a **granular access token** (Access Tokens → Generate new token →
   Granular) with *Read and write* on packages, scoped to `@aiadev`, and
   with **bypass 2FA for automation** enabled, otherwise `npm publish` from
   CI fails on the 2FA prompt.
3. Store it in the repository:

   ```bash
   gh secret set NPM_TOKEN --repo suportly/ai-augmented-developer
   ```

Until `NPM_TOKEN` exists the workflow still runs build and tests but skips
the publish, the tag and the GitHub release with a warning, so nothing gets
marked as released without an actual publish.

### Routine release

1. Bump `version` in `packages/smart-mcp-proxy/package.json` (and note it in
   `CHANGELOG.md` under the framework version that ships alongside).
2. Merge to `main`. The workflow publishes with provenance
   (`npm publish --provenance --access public`), creates the
   `smart-mcp-proxy-v<version>` tag and attaches the tarball to a GitHub
   release named `smart-mcp-proxy <version>`.
3. Verify: `npm view @aiadev/smart-mcp-proxy version`.

### Retrying a failed publish

The tag is created only after a successful publish, so a failed run (expired
token, missing scope) can simply be re-run from the Actions tab or by pushing
`main` again. If a tag was pushed by hand before the publish succeeded,
delete it (`git push origin :refs/tags/smart-mcp-proxy-v<version>`) or push
the tag again to take the manual re-cut path.
