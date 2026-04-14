# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Governance baseline: `CREDITS.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, `SECURITY.md`, `VERSION`, `.editorconfig`.
- Attribution to `obra/superpowers`, `github/spec-kit`, `contains-studio/agents`, and StriveX internal playbooks.
- `skills/implement/` — replaces `speckit` + `subagent-driven-development` with a single execution skill focused on plan + tasks already approved.
- `constitution.md` at the repo root: seven framework-level articles (Spec-first, Test-first, Simplicity, Evidence over claims, Provider pattern, Privacy by design, Attribution) with statement / rationale / test / waiver structure, plus amendment process.
- `templates/` directory with the canonical artifacts produced by the pipeline skills: `spec-template.md`, `plan-template.md`, `tasks-template.md`, `checklist-template.md`, `constitution-template.md`, `agent-file-template.md`, and `commands/command-template.md`. Placeholders use `{{UPPER_SNAKE}}`. Section headings are stable so validators can parse them.
- `[NEEDS CLARIFICATION: <question>]` marker documented in `CONTRIBUTING.md` and `spec-template.md`. Consumed by the upcoming `clarify` skill (phase 3) and enforced by CI from phase 6a.
- Optional `handoffs:` frontmatter schema documented in `templates/commands/command-template.md` — preserves the StriveX convention so Claude Code UIs can surface next-step buttons.
- Seven new pipeline skills: `specify`, `clarify`, `plan`, `tasks`, `analyze`, `checklist`, `constitution`. Structured frontmatter (`name`, `description`, `version`, `inputs`, `outputs`, `requires`, `handoffs`) common to all of them.
- `schemas/skill-frontmatter.schema.json` — provisional JSON Schema for the YAML frontmatter at the top of each `SKILL.md`. Accepts both array and comma-separated-string forms of `allowed-tools`.
- `scripts/validate_skills.py` + `scripts/validate-skills.sh` wrapper — validates every skill against the schema and checks that the frontmatter `name` matches its directory. Run locally with `python3 scripts/validate_skills.py`. Replaced by `aiadev validate` in phase 5.

### Changed

- `skills/implement/SKILL.md` frontmatter extended to the v0.2 structured format (`version`, `inputs`, `outputs`, `requires`, `handoffs`).
- `CLAUDE.md` "Start Here" table and workflow diagram now reflect the new pipeline (`specify → clarify → plan → tasks → implement`).
- `README.md` skills section re-organized into "Pipeline" and "Quality" groups with the new taxonomy.
- Platform docs (`docs/README.codex.md`, `docs/README.opencode.md`, `.opencode/INSTALL.md`) updated to use `specify` in their usage examples.

### Removed

- `skills/brainstorming/` and `skills/writing-plans/` — replaced by `specify`, `clarify`, `plan`, and `tasks`.

### CI and tooling

- `.github/workflows/validate.yml` — four jobs on every push and PR:
  - `skills`: runs `scripts/validate_skills.py` against the JSON Schema.
  - `markdown`: `markdownlint-cli2` over `**/*.md` with a lenient config (`.markdownlint-cli2.jsonc`) tuned for prose-heavy SKILL.md files.
  - `clarifications`: `git grep` that fails the build if any file under `specs/` still contains a `[NEEDS CLARIFICATION: …]` marker (Article I enforcement).
  - `links`: `lychee` checks internal and external links in every Markdown file.
- `.github/PULL_REQUEST_TEMPLATE.md` — PR template with the Constitution Check, Complexity Tracking, and explicit Test Plan with evidence (Article IV).
- `.markdownlint-cli2.jsonc` — project-wide markdownlint config.

### Generic / preset split (phase 4)

- `presets/` directory introduced. Six skills moved from `skills/` to `presets/django-drf-react/skills/` (`git mv` preserves history): `django-patterns`, `ai-integration`, `celery-async`, `autodev-pipeline`, `deploy`, `run-tests`.
- `presets/django-drf-react/CLAUDE.md` — stack-specific agent file rendered from the preset.
- `presets/django-drf-react/constitution.md` — five preset articles extending the root constitution (API-First, Async-First, Docker-native, Model→Serializer→Service→View, Encrypted fields) plus one tightening of Article II (integration tests required for endpoints and Celery tasks).
- `presets/django-drf-react/preset.yaml` — manifest with variables (`PROJECT_NAME`, `BACKEND_DIR`, `FRONTEND_DIR`, `GCP_PROJECT`, `GCP_REGION`) and provided artifacts.
- `presets/lean/` — minimal preset with pipeline only; no stack opinions.
- `presets/catalog.json` + `schemas/preset-catalog.schema.json` — machine-readable registry of presets.
- Root `CLAUDE.md` rewritten as stack-agnostic: it now links to `constitution.md` and the skill map, and explicitly defers stack conventions to the active preset.
- Root `skills/` now contains 14 generic skills; the Project Skills section of the README is replaced by a "Stack skills (via presets)" pointer.
- `scripts/validate_skills.py` now also walks `presets/*/skills/` so preset skills are validated alongside the root catalog.
- `scripts/migrate-to-0.2.sh` — dry-run-by-default helper that grep-detects references to removed v0.1 skills and proposes symlinks to install the `django-drf-react` preset for v0.1 consumers. Run with `--apply` to act.

BREAKING CHANGE: Projects that relied on importing the stack skills from `skills/django-patterns/` (and siblings) must either install the `django-drf-react` preset or move the files into their own project. The migration script covers the common case.

### Python CLI `aiadev` (phase 5)

- `pyproject.toml` declares the `aiadev` package (Python 3.11+) with dependencies on `click`, `pyyaml`, `jsonschema`, and `rich`. Version sourced dynamically from the root `VERSION` file. Console script entry point: `aiadev = aiadev.cli:main`.
- `src/aiadev/` package with four subcommands:
  - `aiadev validate [paths]` — runs the same schema check as `scripts/validate_skills.py` but with a richer UI and proper exit codes. Walks `skills/` and `presets/*/skills/`.
  - `aiadev init --feature <name>` — creates `specs/feature-<slug>/{spec,plan,tasks}.md` from the templates with placeholders substituted (feature name, branch, date, monotonic spec id). Creates the git branch by default; `--branch -` keeps the current branch, `--no-git` skips branching, `--dry-run` prints without acting.
  - `aiadev install --platform --preset` — stub for v0.2 that lists the preset contents it would install; real install lands in v0.3.
  - `aiadev doctor` — runs every validator in order (constitution presence, templates completeness, catalog resolution, skill validation) and returns a single verdict.
- `src/aiadev/paths.py` — framework-root detection (walks up looking for `constitution.md` + `templates/`, falls back to git toplevel).
- `src/aiadev/validate.py` — shared validation core returning a structured `ValidationReport`.
- `tests/` with 20 tests covering validator, init, install, doctor, and the CLI entry point. 84% line coverage of the package.
- Test fixtures under `tests/fixtures/` for the four validator failure modes (missing frontmatter, mismatched name, short description, valid).
- `.gitignore` updated to skip Python build artifacts (`*.egg-info/`, `.pytest_cache/`, `.coverage`, `htmlcov/`, `dist/`, `build/`).

### `mobile-ops` preset (phase 8b)

- `presets/mobile-ops/` — 11 operational runbook skills for the "Cloud Run backend + Expo mobile on EAS + React admin" shape. Skills adapted from internal StriveX playbooks but fully genericized: no project-specific name, domain, or path survives in the preset.
- Placeholders introduced for substitution at `aiadev install` time: `{{PROJECT_NAME}}`, `{{APP_NAME}}`, `{{BACKEND_DIR}}`, `{{MOBILE_DIR}}`, `{{ADMIN_DIR}}`, `{{BACKEND_ASGI_MODULE}}`, `{{CELERY_APP}}`, `{{GCP_PROJECT}}`, `{{GCP_REGION}}`, `{{ARTIFACT_REPO}}`, `{{BACKEND_SERVICE}}`, `{{ADMIN_SERVICE}}`, `{{CLOUD_SQL_INSTANCE}}`, `{{PROD_API_URL}}`, `{{PROD_ADMIN_URL}}`.
- `presets/mobile-ops/preset.yaml` declares the variables with prompts and defaults.
- `presets/mobile-ops/CLAUDE.md` describes the stack assumption, lists the skills, and reminds the reader that the preset is additive — it does not redefine the feature pipeline.
- `presets/catalog.json` registers the new preset at `beta` stability.
- `CREDITS.md` records the StriveX/Suportly lineage as origin-only: the preset itself is scrubbed of project-specific identifiers.
- `aiadev validate` now reports 31 skills (14 generic + 6 django-drf-react + 11 mobile-ops).

### Agents catalog strategy (phase 8a)

- `agents/README.md` documents the two-tier structure: framework-native agents at the top of `agents/` and preset-specific agents under `presets/<preset>/agents/`.
- **The contains-studio multi-discipline catalog is intentionally not bundled.** The upstream has no visible license; Article VII forbids redistribution without one. Users who want that catalog can fork upstream, author their own, or wait for the extensions system (phase 7) to install licensed forks.
- `CREDITS.md` updated to reflect reality: contains-studio listed as an opt-in external catalog rather than a bundled dependency; StriveX-origin subagents noted as destined for `presets/strivex-stack/agents/` in phase 8b (stack-specific, not framework-generic).

### Changed

- `skills/using-ai-augmented-developer/SKILL.md` rewritten: removed the "1% / ABSOLUTELY MUST / NOT NEGOTIABLE" tone, removed the directive that blocked clarifying questions, and clarified that the skill rule only gates **write actions** (not research or questions).
- README skills section and skill count (now 15) aligned with the new `implement` skill and the removal of the command wrappers.
- `CLAUDE.md` workflow diagram and "Start Here" table updated to point at `implement`.

### Removed

- `skills/speckit/` and `skills/subagent-driven-development/` (merged into `skills/implement/`).
- `commands/` directory and its five wrappers (`/brainstorm`, `/write-plan`, `/execute-plan`, `/speckit`, `/debug`) — they were one-line redirects to skills with no added behavior. Skills are invoked directly now.

### Planned for 0.2.0

See [implementation plan](https://github.com/alairjt/ai-augmented-developer/blob/main/docs/implementation-plan.md) for the full v0.2.0 roadmap:

- Constitution + templates + `[NEEDS CLARIFICATION]` marker.
- New command taxonomy: `specify`, `clarify`, `plan`, `tasks`, `analyze`, `checklist`, `implement`, `constitution`.
- Preset split: generic framework at root, Django/React preset in `presets/django-drf-react/`.
- Bundled agent catalog (36 agents across 7 disciplines).
- StriveX operational preset (`presets/strivex-stack/`).
- Python CLI `aiadev` with `init`, `validate`, `install`, `doctor` commands.
- Automated CI validation via `.github/workflows/validate.yml`.

### Planned breaking changes still on the v0.2.0 roadmap

- Bundled agent catalog import (phase 8a).
- Python CLI `aiadev` (phase 5) — will materialize preset installs that today still rely on the migration script.

A migration script (`scripts/migrate-to-0.2.sh`) will be provided to install the Django preset automatically for users on v0.1.

## [0.1.0] - 2026-03-16

Initial public release.

### Added

- 16 skills under `skills/` (brainstorming, writing-plans, speckit, subagent-driven-development, test-driven-development, systematic-debugging, requesting-code-review, finishing-a-branch, frontend-design, ai-integration, celery-async, django-patterns, autodev-pipeline, using-ai-augmented-developer, deploy, run-tests).
- 3 review agents under `agents/`: `code-reviewer`, `plan-document-reviewer`, `spec-document-reviewer`.
- 5 command wrappers under `commands/`: `/brainstorm`, `/write-plan`, `/execute-plan`, `/speckit`, `/debug`.
- Multi-platform install support via `.claude-plugin/`, `.cursor-plugin/`, `.codex/`, `.opencode/`, `gemini-extension.json`.
- `LICENSE` (MIT), `.gitignore`, `README.md`.

[Unreleased]: https://github.com/alairjt/ai-augmented-developer/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/alairjt/ai-augmented-developer/releases/tag/v0.1.0
