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

### StriveX / Suportly internal playbooks

The operational skills in `presets/strivex-stack/` (deploy-backend, build-ios, build-android, submit-*, ota-update, release-notes, bump-version) are generalized versions of runbooks originally written inside the StriveX project at Suportly. They have been parameterized (`{{BACKEND_DIR}}`, `{{GCP_PROJECT}}`, etc.) so they can be reused outside that codebase.

The StriveX project also ships heavily-customized subagents (backend-architect, frontend-developer, mobile-app-builder, etc.) based on the contains-studio format but rewritten for the StriveX stack (Django 5.2, Cloud Run, Gemini API, SimpleJWT). Those land in `presets/strivex-stack/agents/` in phase 8b of the v0.2 refactor — not at the framework root, because they are stack-specific by construction.

## Reporting attribution gaps

If you recognize material in this repository that should be credited here and isn't, open an issue — we will correct it.
