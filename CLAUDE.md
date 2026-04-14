# AI-Augmented Developer

You are working inside the **AI-Augmented Developer** framework repository itself. If you reached this file from a consumer project, its `CLAUDE.md` should link back here for the framework-level rules; the consumer's own preset file carries the stack-specific guidance.

## The rule

Invoke the appropriate skill **before any action that writes code or state**. Clarifying questions and exploration do not require a skill.

| What you're doing | Skill to invoke |
|---|---|
| User described a demand, no `spec.md` yet | `specify` |
| `spec.md` has `[NEEDS CLARIFICATION]` markers | `clarify` |
| Spec is clean, no `plan.md` yet | `plan` |
| Plan approved, no `tasks.md` yet | `tasks` |
| Tasks ready, time to build | `implement` |
| Drift suspected between spec / plan / code | `analyze` |
| Focused quality pass (security / perf / a11y / i18n / privacy / observability) | `checklist` |
| Amending `constitution.md` | `constitution` |
| Writing test-backed code inside `implement` | `test-driven-development` |
| Hit a bug or test failure | `systematic-debugging` |
| Ready to open a PR | `requesting-code-review` |
| Code review approved | `finishing-a-branch` |
| UI or component work | `frontend-design` |

## Constitution

See [`constitution.md`](./constitution.md) for the seven framework articles (Spec-first, Test-first, Simplicity, Evidence over claims, Provider pattern, Privacy by design, Attribution). Every plan ships with a Constitution Check; waivers go in the plan's Complexity Tracking table.

Consumer projects add preset-specific articles via their preset's `constitution.md` (see `presets/django-drf-react/constitution.md` for an example). Presets may tighten the framework rules but cannot weaken them.

## Workflow

```text
specify  ─(ambiguity?)→  clarify  ─→  plan  ─→  tasks  ─→  implement
                                                                │
                                                  test-driven-development (per task)
                                                  systematic-debugging (on failures)
                                                  checklist (per category)
                                                                ↓ (all tasks done)
                                                       analyze (drift check)
                                                                ↓
                                                  requesting-code-review
                                                                ↓ (review approved)
                                                         finishing-a-branch
```

## What lives where

- [`skills/`](./skills) — framework-generic skills that apply to any stack.
- [`presets/<preset>/skills/`](./presets) — stack-specific skills loaded only when that preset is active.
- [`templates/`](./templates) — canonical artifact shapes produced by the pipeline skills.
- [`schemas/`](./schemas) — JSON Schemas for skill frontmatter, preset catalog, and other machine-checkable contracts.
- [`scripts/`](./scripts) — provisional validators until `aiadev` ships (phase 5 of the v0.2 refactor).
- [`agents/`](./agents) — bundled subagent definitions.

## Repository-local commands

This repository is Markdown-heavy with Python-only tooling; it does not need the stack commands a Django or React project would. Everything below assumes a clean clone.

```bash
# Validate every SKILL.md against the schema
python3 scripts/validate_skills.py

# Lint the Markdown (install markdownlint-cli2 locally if you want
# to match CI; CI runs it on every push)
npx markdownlint-cli2 '**/*.md'
```

For stack-specific commands (`pytest`, `npm run dev`, `celery -A config worker`, `docker compose up`), switch to the consumer project and read its `CLAUDE.md`, which will have been rendered from a preset.

## When you change this file

Root `CLAUDE.md` edits are reviewed alongside `constitution.md` and `README.md` changes — the three should stay coherent. If a change is really about the Django stack, it belongs in `presets/django-drf-react/CLAUDE.md`, not here.
