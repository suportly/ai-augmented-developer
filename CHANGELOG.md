# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

- `skills/test-driven-development/SKILL.md`, `presets/django-drf-react/skills/run-tests/SKILL.md`, and `presets/django-drf-react/skills/deploy/SKILL.md` had leftover project-specific path references. Replaced with the generic `<mobile-dir>` placeholder.
- `agents/README.md` and root `CLAUDE.md` referenced pre-rename preset names and "phase N of the v0.2 refactor" language no longer accurate after the release. Rewritten to point at the current preset names and to drop completed-phase callouts.
- Scrubbed residual project-specific attribution from `CREDITS.md`, `CHANGELOG.md`, `README.md`, and `schemas/skill-frontmatter.schema.json`. The framework is deliberately generic; prior internal work is acknowledged only as "prior internal playbooks" without naming a project.

## [0.2.0] - 2026-04-14

Framework rewrite around a spec-driven pipeline, a verifiable constitution, a
preset system, a Python CLI, and automated CI. See below for the full detail;
**BREAKING CHANGES** are listed up front.

### Breaking

- `skills/speckit/` and `skills/subagent-driven-development/` removed; merged into the new `skills/implement/`.
- `skills/brainstorming/` and `skills/writing-plans/` removed; replaced by `skills/specify/`, `skills/clarify/`, `skills/plan/`, and `skills/tasks/`.
- `commands/` directory removed. The five wrappers (`/brainstorm`, `/write-plan`, `/execute-plan`, `/speckit`, `/debug`) were one-line redirects with no added behavior; skills are invoked directly now.
- Six stack-specific skills moved out of `skills/` into `presets/django-drf-react/skills/`: `django-patterns`, `ai-integration`, `celery-async`, `autodev-pipeline`, `deploy`, `run-tests`. `git mv` preserves history; projects that imported them from the root must install the `django-drf-react` preset (or copy the files into their own project).

A migration script, `scripts/migrate-to-0.2.sh`, detects references to removed skills and proposes the preset-install actions for v0.1 consumers. `--apply` performs them.

### Added — pipeline skills (phase 3)

Seven new skills replacing the brainstorming/writing-plans/speckit cluster. All share structured frontmatter (`name`, `description`, `version`, `inputs`, `outputs`, `requires`, `handoffs`) and are validated against `schemas/skill-frontmatter.schema.json`.

- `specify` — demand → `specs/<branch>/spec.md` with `[NEEDS CLARIFICATION]` markers for ambiguity.
- `clarify` — walks markers one at a time, rewrites the file with answers.
- `plan` — spec → `plan.md` with the mandatory Constitution Check.
- `tasks` — plan → `tasks.md`; one task = one test + one implementation + one commit.
- `implement` — fresh subagent per task with two-stage review (spec compliance, then code quality); merged replacement for `speckit` and `subagent-driven-development`.
- `analyze` — drift report between spec / plan / tasks / code.
- `checklist` — focused category pass (security / performance / a11y / i18n / privacy / observability).
- `constitution` — amends `constitution.md` through the documented process (issue first, one article per PR, semver bump).

### Added — constitution and templates (phase 2)

- `constitution.md` at the repo root: seven framework-level articles (Spec-first, Test-first, Simplicity, Evidence over claims, Provider pattern, Privacy by design, Attribution) with statement / rationale / test / waiver structure, plus an amendment process.
- `templates/` directory with canonical artifacts: `spec-template.md`, `plan-template.md`, `tasks-template.md`, `checklist-template.md`, `constitution-template.md`, `agent-file-template.md`, and `commands/command-template.md`. Placeholders use `{{UPPER_SNAKE}}`; section headings are stable so validators can parse them. Optional `handoffs:` frontmatter schema documents the next-step-button convention.
- `[NEEDS CLARIFICATION: <question>]` marker documented in `CONTRIBUTING.md` and `spec-template.md`. CI (`clarifications` job) fails the build if any file under `specs/` still contains a marker.

### Added — preset system and generic/stack split (phases 4, 8a, 8b)

- `presets/` directory introduced with the new preset system (`preset.yaml` manifest, placeholders, variable prompts). Registered in `presets/catalog.json` + `schemas/preset-catalog.schema.json`.
- `presets/django-drf-react/` — full-stack Django + DRF + React preset:
  - `CLAUDE.md` with stack-specific agent guidance.
  - `constitution.md` adding five preset articles (API-First, Async-First, Docker-native, Model→Serializer→Service→View, Encrypted fields) plus a tightening of Article II (integration tests required for endpoints and Celery tasks).
  - `skills/` — the six stack skills moved from root `skills/`.
  - `preset.yaml` with five variables (`PROJECT_NAME`, `BACKEND_DIR`, `FRONTEND_DIR`, `GCP_PROJECT`, `GCP_REGION`).
- `presets/mobile-ops/` — 11 operational runbook skills for the "Cloud Run backend + Expo mobile on EAS + React admin" shape. Fully generic: every path, identifier, and endpoint is a placeholder substituted at install time. 15 placeholders in total.
- `presets/lean/` — minimal preset: pipeline skills only, no stack opinions.
- `CLAUDE.md` at the repo root rewritten as stack-agnostic — links to `constitution.md` and the skill catalog; stack conventions live in the active preset.
- `scripts/migrate-to-0.2.sh` — dry-run-by-default helper for v0.1 consumers.

### Added — Python CLI `aiadev` (phase 5)

- `pyproject.toml` declares the `aiadev` package (Python 3.11+) with `click`, `pyyaml`, `jsonschema`, `rich`. Version sourced dynamically from `VERSION`. Console script: `aiadev = aiadev.cli:main`.
- Four subcommands:
  - `aiadev validate [paths]` — schema-validates every SKILL.md under `skills/` and `presets/*/skills/`.
  - `aiadev init --feature <name>` — creates `specs/feature-<slug>/{spec,plan,tasks}.md` from templates, substitutes placeholders (feature name, branch, date, monotonic spec id), creates the git branch by default.
  - `aiadev install --platform --preset` — v0.2 stub listing preset contents; real install lands in v0.3.
  - `aiadev doctor` — runs every validator in order.
- 20 tests covering validator, init, install, doctor, CLI entry point. 84% package coverage; CI fails below 80%.
- Test fixtures under `tests/fixtures/` for the four validator failure modes.

### Added — governance and attribution (phase 0)

- `CREDITS.md` with explicit attribution to `obra/superpowers` and `github/spec-kit`. `contains-studio/agents` listed as opt-in external catalog (not bundled — see `agents/README.md` for the rationale).
- `CHANGELOG.md`, `CONTRIBUTING.md`, `SECURITY.md`, `VERSION` (single source of truth for semver), `.editorconfig`.
- `agents/README.md` documents the two-tier structure (framework-native + preset-specific) and the decision to not bundle unlicensed catalogs.

### Added — automated CI (phases 6a, 6b)

- `.github/workflows/validate.yml` with six jobs:
  - `skills` — `aiadev validate` on Python 3.11 and 3.12 (matrix).
  - `tests` — `pytest --cov=src/aiadev --cov-fail-under=80` on Python 3.11 and 3.12 (matrix).
  - `doctor` — `aiadev doctor` end-to-end.
  - `markdown` — `markdownlint-cli2` over `**/*.md` with lenient prose config.
  - `clarifications` — `git grep` for unresolved `[NEEDS CLARIFICATION]` markers (Article I enforcement).
  - `links` — `lychee` link checker.
- `.github/PULL_REQUEST_TEMPLATE.md` with Constitution Check grid, Complexity Tracking table, and explicit Test Plan section (Article IV).
- `.markdownlint-cli2.jsonc` — project-wide linter config.

### Changed

- `skills/using-ai-augmented-developer/SKILL.md` rewritten: removed the "1% / ABSOLUTELY MUST / NOT NEGOTIABLE" tone, removed the directive that blocked clarifying questions, and clarified that the skill rule only gates **write actions** (not research or questions).
- `README.md` skills section re-organized into "Pipeline" / "Quality" / "Stack skills (via presets)" groups.
- `.claude-plugin/plugin.json` and `.cursor-plugin/plugin.json` now both declare `skills/` and `agents/`; the `commands/` declaration was removed along with the directory.
- Platform docs (`docs/README.codex.md`, `docs/README.opencode.md`, `.opencode/INSTALL.md`) updated to use `specify` in their usage examples.

### Removed

- Everything listed under **Breaking** above.

### Not shipped in 0.2.0 (deferred to 0.3)

- `aiadev install --interactive` with full preset rendering (currently a stub).
- Extensions system (RFC, `aiadev extension install`) — documented intent, no code.
- Bundled multi-discipline agent catalog (contains-studio licensing unresolved).

## [0.1.0] - 2026-03-16

Initial public release.

### Added

- 16 skills under `skills/` (brainstorming, writing-plans, speckit, subagent-driven-development, test-driven-development, systematic-debugging, requesting-code-review, finishing-a-branch, frontend-design, ai-integration, celery-async, django-patterns, autodev-pipeline, using-ai-augmented-developer, deploy, run-tests).
- 3 review agents under `agents/`: `code-reviewer`, `plan-document-reviewer`, `spec-document-reviewer`.
- 5 command wrappers under `commands/`: `/brainstorm`, `/write-plan`, `/execute-plan`, `/speckit`, `/debug`.
- Multi-platform install support via `.claude-plugin/`, `.cursor-plugin/`, `.codex/`, `.opencode/`, `gemini-extension.json`.
- `LICENSE` (MIT), `.gitignore`, `README.md`.

[Unreleased]: https://github.com/alairjt/ai-augmented-developer/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/alairjt/ai-augmented-developer/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/alairjt/ai-augmented-developer/releases/tag/v0.1.0
