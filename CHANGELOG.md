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

- Root `CLAUDE.md` rewritten as stack-agnostic; Django-specific content moved to `presets/django-drf-react/` (phase 4).

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
