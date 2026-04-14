# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Governance baseline: `CREDITS.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, `SECURITY.md`, `VERSION`, `.editorconfig`.
- Attribution to `obra/superpowers`, `github/spec-kit`, `contains-studio/agents`, and StriveX internal playbooks.

### Planned for 0.2.0

See [implementation plan](https://github.com/alairjt/ai-augmented-developer/blob/main/docs/implementation-plan.md) for the full v0.2.0 roadmap:

- Constitution + templates + `[NEEDS CLARIFICATION]` marker.
- New command taxonomy: `specify`, `clarify`, `plan`, `tasks`, `analyze`, `checklist`, `implement`, `constitution`.
- Preset split: generic framework at root, Django/React preset in `presets/django-drf-react/`.
- Bundled agent catalog (36 agents across 7 disciplines).
- StriveX operational preset (`presets/strivex-stack/`).
- Python CLI `aiadev` with `init`, `validate`, `install`, `doctor` commands.
- Automated CI validation via `.github/workflows/validate.yml`.

### Planned breaking changes in 0.2.0

- `skills/speckit/` and `skills/subagent-driven-development/` merged into `skills/implement/`.
- `skills/brainstorming/` and `skills/writing-plans/` replaced by `skills/specify/` + `skills/plan/`.
- `commands/` wrappers removed; skills invoked directly.
- Root `CLAUDE.md` rewritten as stack-agnostic; Django-specific content moved to `presets/django-drf-react/`.

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
