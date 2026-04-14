# Contributing to AI-Augmented Developer

Thanks for taking the time to contribute. This document explains how to propose changes to the framework.

## Ground rules

1. **Open an issue first** for anything larger than a typo or a one-line fix. Describe the problem and the intended outcome before writing code or new skills.
2. **One concern per PR.** A PR that fixes a bug and refactors unrelated skills is harder to review and more likely to regress things.
3. **Follow the constitution.** Once `constitution.md` lands in v0.2, every PR that affects skills, templates, or the CLI must either pass the constitution check or document the waiver in `Complexity Tracking`.
4. **Cite prior art.** If you adapt a skill or template from another project, update `CREDITS.md`.

## Types of contributions

### Bug reports

File an issue with:

- the platform (Claude Code / Cursor / Codex / OpenCode / Gemini CLI) and version,
- the skill, command, or template involved,
- the exact invocation and the observed vs expected behavior,
- if applicable, the minimum reproducer (a short `spec.md` or `plan.md` that triggers the bug).

### New or modified skills

Each skill lives under `skills/<name>/SKILL.md` with frontmatter that conforms to `schemas/skill-frontmatter.schema.json` (available from v0.2 onward).

Checklist for a skill PR:

- [ ] Frontmatter has `name`, `description`, `version`. From v0.2: `inputs`, `outputs`, `requires` as applicable.
- [ ] Body is under 100 lines unless there is a documented reason.
- [ ] If the skill prescribes a workflow, it is invokable from a fresh context without the agent needing to read any other file first.
- [ ] No contradictions with existing skills. In particular, `skills/using-ai-augmented-developer/SKILL.md` governs the meta-rules.
- [ ] At least one concrete example of usage.

### New templates or presets

Templates (`templates/*.md`) and presets (`presets/<name>/`) need:

- a rationale in the PR description (what gap does it fill?),
- for presets, a `preset.yaml` listing the variables to substitute during install,
- test coverage once the CLI ships: a round-trip that runs `aiadev install --preset <name>` in a throwaway directory and asserts the resulting structure.

### Bundled agents

The `agents/` catalog is imported from upstream projects (see `CREDITS.md`). **Do not** hand-edit files there; open an issue so we can track drift with the source.

## Local workflow

Until the CLI ships (see `CHANGELOG.md [Unreleased]`), validation is manual:

```bash
# List skills and their frontmatter (for smoke checking)
find skills -name "SKILL.md" -exec head -n 10 {} \;

# From v0.2: the CLI handles this
aiadev validate skills/
aiadev validate templates/
aiadev doctor
```

CI will run the same checks automatically once `.github/workflows/validate.yml` is in place.

## Commit messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` new skill, command, template, preset, or CLI feature.
- `fix:` bug fix.
- `docs:` README, CONTRIBUTING, CHANGELOG changes.
- `refactor:` renames, moves, or structural changes with no behavior change.
- `chore:` tooling, dependencies, CI config.

Breaking changes go in the footer: `BREAKING CHANGE: <description>`.

## Release process

Releases are cut from `main` after the CI workflow is green:

1. Update `VERSION` and move `[Unreleased]` entries to a new dated section in `CHANGELOG.md`.
2. Tag `vX.Y.Z` and create a GitHub release with the changelog excerpt.
3. If the CLI has shipped, `aiadev` is published to PyPI via the release workflow.

## Code of conduct

Be respectful. Assume good faith. If someone asks for context, give it. If something in a review feels unfair, say so and we will work through it.
