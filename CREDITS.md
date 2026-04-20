# Credits

AI-Augmented Developer stands on the shoulders of several open-source projects and internal playbooks. This file records each debt explicitly.

## Direct inspirations

### [obra/superpowers](https://github.com/obra/superpowers)

The original source for the "skill-first, opinionated workflow" structure. Early versions of this repository were a fork; commits `ea7a5d6` ("add multi-platform support") and `d3a3470` ("parity with superpowers structure") acknowledge that lineage. Several skill names, the brainstorming → plan → subagent pipeline idea, and the overall README voice trace back to superpowers.

### [juliusbrussee/caveman](https://github.com/JuliusBrussee/caveman)

The terse-output contract for reviewer subagents (feature `0009-token-economy-terse-mode`) is adapted from caveman's one-line-per-finding output style — originally a Claude Code skill that compresses model output by roughly 22–87 % (MIT license at time of adaptation). We do not bundle caveman itself; we borrow the shape of its reviewer output and codify it in `schemas/terse-output.schema.json`. The meme/caveman-voice aesthetic and the companion `cavemem` / `cavekit` tools are out of scope for this framework.

### [github/spec-kit](https://github.com/github/spec-kit)

Starting in v0.2, this project adopts spec-kit's architecture for spec-driven development: the `constitution.md` contract, the command taxonomy (`specify`/`clarify`/`plan`/`tasks`/`analyze`/`checklist`/`implement`), the `[NEEDS CLARIFICATION]` marker convention, the per-branch `specs/<branch>/` artifact layout, and the template-based gate checks are all derived from spec-kit (MIT).

Where we copy verbatim (for example markdownlint config or template scaffolds), the original license notice is preserved alongside the file.

## Bundled catalogs

### [contains-studio/agents](https://github.com/contains-studio/agents) — not bundled

A widely-referenced community catalog of multi-discipline subagents (design, engineering, marketing, studio-operations, testing, project-management, product). We **do not bundle** it: the upstream has no visible license at the time of writing, and Article VII (Attribution) requires a citable license before redistribution. The catalog is documented in [`agents/README.md`](./agents/README.md) as an opt-in external catalog; a future extension (phase 7) will make it installable from a licensed fork.

### `presets/mobile-ops/` runbooks

The 11 operational skills in `presets/mobile-ops/` (deploy-backend,
deploy-admin, build-ios, build-android, submit-ios, submit-android,
ota-update, release-notes, bump-version, start-dev, run-tests) are
generic runbooks for the "Cloud Run backend + Expo mobile on EAS +
React admin" shape. They ship with placeholders (`{{BACKEND_DIR}}`,
`{{MOBILE_DIR}}`, `{{ADMIN_DIR}}`, `{{GCP_PROJECT}}`, `{{GCP_REGION}}`,
`{{ARTIFACT_REPO}}`, `{{BACKEND_SERVICE}}`, `{{ADMIN_SERVICE}}`,
`{{CLOUD_SQL_INSTANCE}}`, `{{BACKEND_ASGI_MODULE}}`, `{{CELERY_APP}}`,
`{{APP_NAME}}`, `{{PROD_API_URL}}`, `{{PROD_ADMIN_URL}}`) to be
substituted at `aiadev install --preset mobile-ops --interactive` time.
No project-specific domain, identifier, or path survives in the preset.

### Vendored MCP schemas (`schemas/vendor/`)

JSON Schemas extracted from the [`mcp`](https://pypi.org/project/mcp/) Python
SDK v1.26.0 (Anthropic, MIT license) via `pydantic` `model_json_schema()`.
Used for offline validation of aiadev's `tools/list` and `prompts/list`
responses in CI. See `schemas/vendor/README.md` for extraction details.

## Reporting attribution gaps

If you recognize material in this repository that should be credited here and isn't, open an issue — we will correct it.
