# Feature specification: Token economy & terse-mode (caveman-inspired)

> This file is produced by the `specify` skill. Keep it focused on **what** and **why** — planning and code belong in `plan.md` and `tasks.md`.

**Branch:** `feature/token-economy-terse-mode`
**Created:** 2026-04-20
**Status:** Draft
**Spec ID:** 0009
**Language:** en

---

<!-- section: Problem -->
## Problem

The AI-Augmented Developer pipeline dispatches many subagents per feature (spec-reviewer, plan-reviewer, per-task implementers, code-reviewer) and produces long Markdown artifacts (`spec.md`, `plan.md`, `tasks.md`, review reports). Every hop pays in output tokens, latency, and reader fatigue. The `juliusbrussee/caveman` project (~40k stars, a Claude Code skill that compresses model output 22–87 %) shows there is real headroom without sacrificing correctness. This framework has no opt-in compression, no terse-output contract for reviewer subagents, and no quick-reference surface for the pipeline commands — new users discover the skill graph by reading `CLAUDE.md` top-to-bottom.

<!-- section: Users and stakeholders -->
## Users and stakeholders

- **Framework users** running `/aiadev:*` commands on real features — pay subagent token bills, read the artifacts.
- **Subagent authors** (reviewers, implementers) — must follow the output contract.
- **Framework maintainers** — own the skill catalog, templates, and constitution; sign off on any article-touching change.
- **Consumer projects** (e.g. `django-drf-react` preset) — inherit whatever defaults ship here.

<!-- section: Success criteria -->
## Success criteria

- Running a representative pipeline (`specify → plan → tasks → implement` on a ≤ 5-task feature — exact fixture in `cl-4`, stored under `specs/0009-token-economy-terse-mode/benchmark/`) with terse-mode enabled produces ≥ 30 % fewer output tokens than the same run with it disabled, measured on reviewer + implementer subagent turns against a pinned model family. Baseline captured before merge.
- Reviewer subagents (`spec-document-reviewer`, `plan-document-reviewer`, `code-reviewer`) emit findings in a one-line-per-issue contract when terse-mode is on, and a schema validator rejects multi-paragraph findings in that mode.
- A `/aiadev:help` (or equivalent) quick-reference is reachable in ≤ 1 command and lists every pipeline skill with its one-line purpose, matching the table in root `CLAUDE.md`.
- Terse-mode is **off by default**. Enabling it is a single, discoverable switch (per-invocation flag or project setting) and the mechanism is documented in exactly one place.
- No regression in artifact schema validation: every existing `scripts/validate_skills.py` and schema check still passes with terse-mode on and off.

<!-- section: Non-goals -->
## Non-goals

- Porting caveman's meme/caveman-voice aesthetic into framework artifacts. Specs, plans, and reviews stay in normal prose.
- Compressing the **user-authored** content of `spec.md`, `plan.md`, `tasks.md`. Only agent-generated output (reviewer findings, implementer summaries, hand-off messages) is in scope.
- Replacing or rewriting the existing `requesting-code-review` / reviewer agents — terse-mode is an output contract they opt into, not a new reviewer.
- Shipping a separate "memory compression" tool (caveman's `cavemem`). Out of scope; revisit later if needed.
- Multi-language compression rules (caveman's 文言文 mode). The `Language:` header already governs artifact language.
- Terse commit-message / PR-description mode (caveman-commit analogue). `finishing-a-branch` and `git-workflow.md` already constrain commit subjects; revisit in a later spec if reviewer terse-mode proves its value.
- Non-Claude handlers (Codex, Gemini CLI, Cursor, Windsurf, Cline, Copilot, etc.) in v1. They inherit the terse contract in a follow-up once Claude Code has a working reference.

<!-- section: User stories -->
## User stories

### Story 1 — Terse reviewer output (P1)

As a **framework user** running `/aiadev:plan` on a mid-size feature, I want the plan-reviewer subagent to emit findings in a compact one-line-per-issue format when terse-mode is on, so that I spend less time reading and less money on output tokens.

**Acceptance scenarios:**

1. Given terse-mode is **off** (default), when `plan-document-reviewer` reports CHANGES_REQUESTED with two issues, then the output follows the current multi-paragraph format and the pipeline proceeds unchanged.
2. Given terse-mode is **on**, when the same reviewer reports the same two issues, then each issue appears on a single line prefixed with severity and location (e.g. `plan.md:42 🔴 missing Constitution Check`), and the response's output-token count (governing metric) is ≥ 30 % lower than the off-mode equivalent for the same findings.
3. Given terse-mode is **on** and a reviewer accidentally emits a multi-paragraph finding, when the output is validated against the terse schema, then validation fails with a clear message naming the offending block, and the pipeline does not silently accept the degraded format.

### Story 2 — Pipeline quick-reference (P1)

As a **new framework user** who just installed the preset, I want a single command that prints the pipeline skills and their one-line purpose, so that I can start without reading `CLAUDE.md` end-to-end.

**Acceptance scenarios:**

1. Given the framework is installed in a consumer project, when the user invokes the help command, then the output lists every `/aiadev:*` pipeline command with its one-line purpose and the expected predecessor/successor step.
2. Given the skill catalog changes (new skill added or renamed), when the help output is regenerated, then it stays in sync with the authoritative list in root `CLAUDE.md` — a CI check fails if they drift.
3. Given terse-mode is on, when the help command runs, then the output fits within the budget defined by `cl-1` (below) and a test enforces that budget on every change to the help artifact.

### Story 3 — Opt-in token-economy switch (P2)

As a **framework maintainer**, I want terse-mode to be a single documented switch that a consumer project or a one-off invocation can toggle, so that adoption is a one-line change and rollback is trivial.

**Acceptance scenarios:**

1. Given a consumer project with no terse-mode configuration, when any `/aiadev:*` command runs, then terse-mode is off and every artifact matches the pre-feature behaviour byte-for-byte on a recorded fixture.
2. Given a consumer project that has enabled terse-mode via the supported switch, when a pipeline command runs, then every reviewer subagent in scope for v1 (per `cl-3`) spawned by that command adopts the terse output contract, and the switch state is visible in the run's hand-off message.
3. Given terse-mode is enabled project-wide but a single invocation passes an explicit override, when the command runs, then the per-invocation override wins and a one-line note in the hand-off explains which level resolved.

<!-- section: Clarifications -->
## Clarifications

- **cl-1 — Help budget:** Both caps apply — **≤ 24 lines** (single-screen) **and ≤ 600 output tokens** against the pinned model family from `cl-4`. A single test enforces both; either violation fails. Applies only when terse-mode is on; off-mode help has no cap.
- **cl-2 — Switch location:** Project-level key in `.claude/settings.json` (e.g. `"aiadev.terseMode": true|false`, off by default) with a per-invocation env-var override (`AIADEV_TERSE=1` enables, `AIADEV_TERSE=0` disables). Env wins over settings; the resolved level is echoed in the skill's hand-off message. Aligned with the `update-config` skill; no new config file introduced.
- **cl-3 — Subagent scope:** Reviewers only in v1 (`spec-document-reviewer`, `plan-document-reviewer`, `code-reviewer`). Implementer subagents spawned by `/aiadev:implement` keep their current narrative output, because the two-stage review depends on the hand-off context. Extending terse-mode to implementers is a follow-up informed by v1 results.
- **cl-4 — Baseline fixture:** A synthetic 3-task micro-feature stored under `specs/0009-token-economy-terse-mode/benchmark/` that exercises `spec-document-reviewer`, `plan-document-reviewer`, and `code-reviewer` with realistic inputs. Runs pinned to the **Claude Sonnet 4.6** tokenizer (`claude-sonnet-4-6`). Captured twice (terse-mode on / off), checked into the repo, and re-executed by a CI job. Implementer turns are out of scope for this measurement per cl-3.
- **cl-5 — Commit-message analogue:** Deferred. `finishing-a-branch` and `.claude/rules/git-workflow.md` already cap commit subjects at 72 chars with imperative mood; the marginal token win does not justify forking the commit pipeline in v1. Added to the Non-goals list. Revisit only if reviewer terse-mode demonstrates the ≥ 30 % target and commit verbosity becomes the next bottleneck.
- **cl-6 — Handler reach:** Claude Code only in v1. Other handlers (Codex, Gemini CLI, Cursor, Windsurf, Cline, Copilot, etc.) inherit the terse contract in a follow-up once Claude Code has a working reference. Keeps the first iteration's scope tight and testable.

<!-- section: Data touched -->
## Data touched

- **Skill frontmatter** under `skills/` and `presets/*/skills/` — may gain a new `terse_output_contract` capability flag (names subject to plan).
- **Agent definitions** under `agents/` — the three reviewer agents gain a terse output section.
- **New quick-reference artifact** — either a skill (e.g. `skills/help/SKILL.md`) or a generated `docs/pipeline-reference.md`.
- **Schema / validator** under `schemas/` and `scripts/validate_skills.py` — adds terse-output schema + CI check for help/CLAUDE.md drift.
- **Project-level configuration** — one new opt-in switch; exact location is `cl-2`.

No runtime user data, no database, no PII.

<!-- section: Out-of-band effects -->
## Out-of-band effects

- CI jobs gain one new check (help/CLAUDE.md drift, terse-output schema validation).
- No external APIs, no notifications, no payments, no third-party writes. Consumer projects that run `aiadev sync` after upgrading will see the new skill/agent files land under their `.claude/` tree.

<!-- section: Open risks -->
## Open risks

- Terse reviewer output risks losing nuance that currently helps fixers act — a one-line "missing Constitution Check" may not tell the author which article. Mitigation is a plan-level decision, not a spec-level promise.
- Drift between root `CLAUDE.md`, the help output, and the skill catalog is a real maintenance cost; this spec adds a CI check rather than a manual process, but the check itself has to be maintained.
- Adoption risk: if terse-mode stays off by default and the switch is buried, the token-saving success criterion is never exercised in practice. Discoverability of the switch matters.
- Measurement risk: token counts depend on the model and tokenizer in use. The baseline fixture (`cl-4`) must pin a specific model family or the ≥ 30 % number becomes unfalsifiable.

<!-- section: Traceability -->
## Traceability

- Originating demand: user request 2026-04-20 — "analyze https://github.com/juliusbrussee/caveman and pull features that fit this project".
- Upstream project: [juliusbrussee/caveman](https://github.com/JuliusBrussee/caveman) (~40k stars, Apr 2026).
- Related specs: none.
- Constitution articles invoked: III (Simplicity — opt-in, off by default), IV (Evidence over claims — measurable ≥ 30 % target with a fixture), VII (Attribution — `CREDITS.md` gains an entry crediting `juliusbrussee/caveman` as the source of the terse-output concept).
