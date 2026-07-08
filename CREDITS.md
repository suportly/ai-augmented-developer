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

### [bmad-code-org/BMAD-METHOD](https://github.com/bmad-code-org/BMAD-METHOD)

A comparative analysis of BMAD-METHOD v6.6.0 (MIT license at time of adaptation) inspired the feature `0014-bmad-inspired-evolutions`, which introduces the `task-context` skill (Story 1) for per-task context composition before each implementer dispatch, the 3-tier customization resolver (Story 2) layering skill `customize.toml` (base) → `_aiadev/team.toml` (committed) → `_aiadev/user.toml` (gitignored), the zero-findings-halt review pattern (Story 3) requiring an explicit `### Why no issues` block + re-dispatch gate when reviewer subagents return APPROVED on a non-trivial diff, and the state-aware `help` skill (Story 4) via the new `pipeline_state` module. No code is copied verbatim; the framework adapts BMAD's design ideas to the existing Markdown-skill architecture.

### [Agent Skills open standard](https://agentskills.io) ([agentskills/agentskills](https://github.com/agentskills/agentskills))

Starting with feature `0016-agent-skills-interop`, every `SKILL.md`
frontmatter in this repo conforms at the top level to the open Agent
Skills standard published at agentskills.io (governed by the Agentic
AI Foundation) — `name`, `description`, `license`, `compatibility`,
`metadata`, `allowed-tools`, plus the two documented Claude Code
runtime extensions `disable-model-invocation` and `argument-hint`
(spec 0016 cl-7). The five proprietary aiadev pipeline fields
(`version`, `inputs`, `outputs`, `requires`, `handoffs`) that used to
live at the top level now nest under the single namespaced key
`metadata.aiadev`, so they no longer collide with the open standard or
with other frameworks' metadata.

We vendor a snapshot of the standard's conformance schema at
`schemas/agent-skills.schema.json` (snapshot dated 2025-12-18,
re-verified against the published spec and the `skills-ref` reference
validator on 2026-07-08 — see the `$comment` in that file for the
exact deviations recorded). No code from the reference implementation
is bundled; we only vendor the schema shape and validate against it in
`aiadev validate`. The `agentskills/agentskills` repository (verified
via the GitHub API at the time of this adaptation) licenses its code
under **Apache License 2.0** and its documentation under **CC-BY-4.0**;
we cite both here per Article VII rather than re-publish the license
text.

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
