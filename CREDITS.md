# Credits

AI-Augmented Developer stands on the shoulders of several open-source projects and internal playbooks. This file records each debt explicitly.

## Direct inspirations

### [obra/superpowers](https://github.com/obra/superpowers)

The original source for the "skill-first, opinionated workflow" structure. Early versions of this repository were a fork; commits `ea7a5d6` ("add multi-platform support") and `d3a3470` ("parity with superpowers structure") acknowledge that lineage. Several skill names, the brainstorming → plan → subagent pipeline idea, and the overall README voice trace back to superpowers.

### [github/spec-kit](https://github.com/github/spec-kit)

Starting in v0.2, this project adopts spec-kit's architecture for spec-driven development: the `constitution.md` contract, the command taxonomy (`specify`/`clarify`/`plan`/`tasks`/`analyze`/`checklist`/`implement`), the `[NEEDS CLARIFICATION]` marker convention, the per-branch `specs/<branch>/` artifact layout, and the template-based gate checks are all derived from spec-kit (MIT).

Where we copy verbatim (for example markdownlint config or template scaffolds), the original license notice is preserved alongside the file.

## Bundled catalogs

### [contains-studio/agents](https://github.com/contains-studio/agents) — not bundled

A widely-referenced community catalog of multi-discipline subagents (design, engineering, marketing, studio-operations, testing, project-management, product). We **do not bundle** it: the upstream has no visible license at the time of writing, and Article VII (Attribution) requires a citable license before redistribution. The catalog is documented in [`agents/README.md`](./agents/README.md) as an opt-in external catalog; a future extension (phase 7) will make it installable from a licensed fork.

### StriveX / Suportly internal playbooks (origin of `presets/mobile-ops/`)

The 11 operational skills in `presets/mobile-ops/` (deploy-backend,
deploy-admin, build-ios, build-android, submit-ios, submit-android,
ota-update, release-notes, bump-version, start-dev, run-tests) started
life as internal runbooks inside the StriveX project at Suportly. They
have been:

- **Renamed** away from any StriveX-specific identifiers.
- **Parameterized** with placeholders (`{{BACKEND_DIR}}`, `{{MOBILE_DIR}}`,
  `{{ADMIN_DIR}}`, `{{GCP_PROJECT}}`, `{{GCP_REGION}}`,
  `{{ARTIFACT_REPO}}`, `{{BACKEND_SERVICE}}`, `{{ADMIN_SERVICE}}`,
  `{{CLOUD_SQL_INSTANCE}}`, `{{BACKEND_ASGI_MODULE}}`, `{{CELERY_APP}}`,
  `{{APP_NAME}}`, `{{PROD_API_URL}}`, `{{PROD_ADMIN_URL}}`) so any
  project with the same operational shape can use them.
- **Genericized** so nothing in the skills, CLAUDE.md, or preset manifest
  references StriveX, Suportly, nzrgym, or any other project-specific
  domain.

The preset carries no StriveX-specific subagents. The customized
subagents that exist inside the StriveX project are not bundled here —
see the `agents/README.md` note on why multi-discipline catalogs require
clearer licensing before they ship.

## Reporting attribution gaps

If you recognize material in this repository that should be credited here and isn't, open an issue — we will correct it.
