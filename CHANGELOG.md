# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

Spec **0016 — agent-skills-interop**. In December 2025 the Agent
Skills spec (agentskills.io, governed by the Agentic AI Foundation)
became an open standard adopted by Claude Code, Codex CLI, Cursor,
Gemini CLI, Copilot, and others — the same platforms `aiadev sync`
already targets. Four stories: this release aligns the framework's
skill frontmatter with that standard (Story 1) and closes the three
adjacent gaps surfaced by the same ecosystem review — conditional rule
loading, a canonical `AGENTS.md`, and generated plugin manifests
(Stories 2-4).

### Added

- **Frontmatter conformance with the open Agent Skills standard**
  (Story 1). Every `SKILL.md` (16 in the root catalog + 6 in
  `presets/django-drf-react/`) now uses only standard top-level fields
  (`name`, `description`, `license`, `compatibility`, `metadata`,
  `allowed-tools`) plus the two documented Claude Code runtime
  extensions (`disable-model-invocation`, `argument-hint` — cl-7). The
  5 proprietary aiadev pipeline fields (`version`, `inputs`, `outputs`,
  `requires`, `handoffs`) now nest under the single namespaced key
  `metadata.aiadev` instead of living at the top level (cl-1).
  `schemas/agent-skills.schema.json` vendors a snapshot of the open
  standard's conformance schema (snapshot dated 2025-12-18, cl-2) and
  `aiadev validate` runs dual validation — the vendored open-standard
  schema plus the internal `schemas/skill-frontmatter.schema.json` —
  with the same error severity as before; nothing became a warning.
  The old top-level shape is now a hard validation error (cl-5); `aiadev
  sync` auto-migrates skills already installed in a consumer project to
  the new shape with no manual intervention required (Story 1 sc4).
- **Conditional rule loading via `paths:`** (Story 2). Rule frontmatter
  may now declare an optional `paths:` (glob list); `aiadev sync`
  propagates the conditionality to every platform that supports it and
  falls back to the current always-loaded behaviour, without error,
  on platforms that don't. First (minimal) wave: `rules/testing.md`
  only (cl-6), with `paths: ["tests/**", "**/*.test.*", "**/*_test.*",
  "conftest.py"]`. Claude Code keeps the rule's `paths:` intact in
  `.claude/rules/testing.md`; Cursor translates it into the native
  `.mdc` `globs` field; platforms without conditional loading strip
  `paths:` and install the rule exactly as before. Rules without
  `paths:` are untouched — the feature is strictly opt-in per rule.
- **`AGENTS.md` as the sync-managed canonical agent file** (Story 3).
  `aiadev sync` now generates a single `AGENTS.md` at the project root;
  `CLAUDE.md` and `GEMINI.md` become thin wrappers (~3 lines) pointing
  at it instead of duplicating the generated content (cl-3). Every
  managed block (including the `<!-- aiadev:auto-stack -->` block)
  exists in exactly one physical file. Pre-existing manual content in a
  consumer's `CLAUDE.md`/`GEMINI.md` is preserved by the migration path
  and merged into `AGENTS.md`'s own managed block — see
  [docs/agent-skills-interop.md](docs/agent-skills-interop.md) for the
  full migration walkthrough, including the `.bak` backup the migration
  writes alongside each legacy agent file it rewrites.
- **`aiadev manifests --check|--write`** (Story 4). `.claude-plugin/plugin.json`,
  `.claude-plugin/marketplace.json`, and `.cursor-plugin/plugin.json`
  are now derived from `VERSION` + `pyproject.toml` + `presets/catalog.json`
  instead of hand-maintained. `--check` (the default) fails naming the
  file and the two diverging values when a manifest drifts from the
  derivation (e.g. a stale `version`); `--write` regenerates all three
  and is idempotent. Every `stable` preset in `presets/catalog.json`
  gets a corresponding entry in `marketplace.json` automatically (cl-4);
  `beta`/`experimental` presets are omitted until promoted. A new CI job
  (`manifests` in `.github/workflows/validate.yml`) runs
  `aiadev manifests --check` so no future release ships with an
  out-of-sync manifest like the `1.0.0` one this feature found and
  fixed.
- [docs/agent-skills-interop.md](docs/agent-skills-interop.md) —
  consolidated reference for all four stories: the `metadata.aiadev`
  namespace and migration, dual validation (with a worked error
  example), the per-platform `paths:` propagation table, the
  `AGENTS.md` canonical layout and legacy migration, and `aiadev
  manifests` usage.
- Attribution for the [Agent Skills open standard](https://agentskills.io)
  in `CREDITS.md` per Article VII.

## [0.20.0] - 2026-07-08

### Added

- **`aiadev metrics` subcommand** ([spec 0015](specs/0015-aiadev-metrics/spec.md))
  aggregating the audit trail produced by every pipeline run. Reads
  `.review-log.jsonl` (introduced by 0014), `tasks.md` statuses, spec
  headers, and `git log` to emit first-pass approval rate per
  reviewer, tasks with rework, post-cutoff coverage, `specify→merge`
  median, and unresolved-clarification counts. Two output formats:
  `text` (default) and `--format json` with stable `schema_version: 1`.
  Privacy by design — reviewer prose is off by default and only
  exposed via `--show-bodies` (cl-3). Single-repo MVP; cross-repo
  aggregation is deferred to a future spec (cl-2). Default time
  window is last 90 days (cl-4). Read-only, no network, no new
  abstractions beyond `MetricsReport`. See
  [docs/metrics.md](docs/metrics.md).

## [0.19.0] - 2026-05-13

Spec **0014 — bmad-inspired-evolutions**. Comparative analysis with
`bmad-code-org/BMAD-METHOD` v6.6.0 inspired four additive evolutions:
opt-in per-task context composition, a 3-tier TOML customization
resolver, a zero-findings-halt rule for reviewer subagents, and a
state-aware `help` surface. Every change is opt-in or backwards
compatible — existing pipelines run byte-for-byte unchanged.

### Added

- **`task-context` skill** (`skills/task-context/SKILL.md`) and
  template (`templates/task-context-template.md`) producing a
  per-task context file at `specs/<branch>/task-context/<TID>-<slug>.md`
  before each implementer dispatch. Slices the spec acceptance
  scenarios, the plan task block, and ≤ 40-line excerpts of the
  files to modify, plus a TDD checklist and a pointer back to the
  previous task context. Staleness check via `mtime` vs the last
  `git log` of the referenced files. Opt-in via preset.yaml
  `task_context: true` (enabled by default in
  `presets/django-drf-react/`) or the new
  `aiadev preflight implement --task-context` flag. When inactive,
  the existing inline implementer prompt is preserved byte-for-byte.
  (specs/0014 Story 1)
- **3-tier customization resolver** (`src/aiadev/customization.py`)
  merging skill `customize.toml` (base) → `_aiadev/team.toml`
  (committed) → `_aiadev/user.toml` (gitignored). Scalars follow
  layer precedence; tables deep-merge; arrays of tables match by
  `code` / `id` and replace-or-append; parse errors abort with
  `ERROR: <path> line <N>: <parse-error>`. Performance budget
  ≤ 50 ms for typical merges. (specs/0014 Story 2)
- **Zero-findings-halt rule** for the three reviewer subagents
  (`code-reviewer`, `spec-document-reviewer`, `plan-document-reviewer`):
  APPROVED on a non-trivial change (> 10 LOC after
  `.md/.json/.lock/.toml/docs/` exclusions, or any spec/plan
  creation) MUST include a `### Why no issues` block with ≥ 3
  citable verifications. The orchestrator re-dispatches the
  reviewer with reinforced adversarial framing on violation
  (hard limit 2 re-dispatches per reviewer per task). New
  `src/aiadev/review_log.py` provides the non-trivial detector
  and JSONL log at `specs/<branch>/.review-log.jsonl`; new
  `aiadev preflight requesting-code-review --feature <slug>`
  validator gates `requesting-code-review` and
  `finishing-a-branch`. (specs/0014 Story 3)
- **State-aware `help` skill** prepends a `Próximo passo: <command>`
  line by inspecting `specs/<branch>/` via the new
  `aiadev.pipeline_state.recommend_next_command(workspace_path) -> dict`
  helper. The `--plain` flag and the `AIADEV_HELP_PLAIN=1` env
  preserve the legacy verbatim output byte-for-byte. Performance
  budget ≤ 200 ms across a 50-spec workspace. (specs/0014 Story 4)
- **`🟢 verification` variant** in `schemas/terse-output.schema.json`
  for terse-mode reviewer "Why no issues" lines. Existing
  `🔴`/`🟡`/`🟢` (nit) variants remain valid.
- **`aiadev install`** now emits `_aiadev/team.toml` (commit-ready,
  with a header explaining the merge rules) and adds
  `_aiadev/user.toml` to the project's `.gitignore` when
  `--scope project`. Idempotent across re-installs.
- **`docs/customization.md`** documents the 3-tier resolver merge
  rules with three worked examples (override of a skill menu, of
  an agent's `principles[]` array, and of a scalar `default_model`).
- Comparative analysis with `bmad-code-org/BMAD-METHOD` v6.6.0
  inspired this feature — see [CREDITS.md](./CREDITS.md).

### Fixed

- **VS Code extension parser** (released as `aiadev-spec-explorer`
  0.0.11): `parser/tasks.ts` now accepts paragraph-style task
  fields without the leading `- ` list bullet. Real trigger:
  nzr-kdp specs `032-shop-print-order-lifecycle` (17 tasks) and
  `034-shop-public-checkout-overhaul` (41 tasks) wrote each task
  block as `**Status**: done` (paragraph form, every field on its
  own line). The previous regex required the leading `- `, so all
  58 tasks rendered as `?` instead of green checks. Canonical
  `- **Status:** done` keeps working unchanged. The Python parser
  in `src/aiadev/tasks_status.py` is intentionally left strict —
  the `implement` orchestrator round-trips that file and requires
  the canonical shape.

## [0.18.1] - 2026-05-06

Docs/prompt clarification in the `implement` skill. The implementer
subagent contract now states explicitly that per-task test runs are
scoped to the changed code (the new test plus module-level or
related-file tests), and the full suite is the `finishing-a-branch`
gate, not a per-task gate. Removes ambiguity that could push large
codebases into running the entire suite after every task.

### Changed

- **`skills/implement/SKILL.md`** implementer prompt: workflow line
  now specifies "Run only the tests that exercise the changed code"
  and points to `finishing-a-branch` as the full-suite gate. `DONE`
  status reworded from `all tests passing` to
  `task-scoped tests passing`.

## [0.18.0] - 2026-05-06

Spec **0013 — implement-task-status-tracking**. Closes issue #33: the
`implement` skill now flips `**Status:** pending` → `**Status:** done`
on each task's `### TNNN` block atomically, inside the same commit as
the task's code change. Resume after a crash is now safe — the
orchestrator skips tasks already marked `done`, treats `in_progress`
as a re-dispatch target, and halts on out-of-order or malformed state
with the verbatim error string from the spec.

### Added

- **`aiadev.tasks_status`** new helper module: `parse(path) ->
  list[TaskRow]`, `validate(rows)` (raises `TasksMdError` on
  malformed rows or `done`-prefix violations), `mark_done(path,
  task_id)` (idempotent single-line rewrite). 12 unit tests cover
  Story 1 sc2 + Story 2 sc1–sc4 against five `tasks_md_samples`
  fixtures (clean / malformed / out-of-order / in-progress /
  all-done).
- **`tests/test_implement_skill_drift.py`** content assertion that
  pins the loop section against accidental regression — required
  phrases include the literal `**Status:**` strings, the
  `git restore --staged tasks.md && git checkout -- tasks.md`
  rollback commands, and the word `orchestrator`.

### Changed

- **`skills/implement/SKILL.md`** loop step 5 rewritten into a
  9-step procedure with explicit orchestrator ownership of every
  `tasks.md` read/mutate, idempotency guard for `done` rows, the
  `in_progress`-as-pending re-dispatch rule, the prefix-invariant
  abort, and the `git restore --staged tasks.md` rollback on
  commit failure.
- **`templates/tasks-template.md`** `Status` ownership note
  strengthened: `Status` is owned by the `implement` skill, which
  flips `pending → done` inside each task's commit; manual edits
  are overwritten on the next run.
- **`vscode-extension/media/aiadev.svg`** activity-bar icon
  redrawn from the existing `icon.png` (document + circuit-tree
  motif, monochrome with `currentColor`). The previous SVG was a
  generic 18×18 rectangle.

### Fixed

- Issue #33 — `tasks.md` no longer remains `Status: pending` after
  shipped commits. Existing consumer projects with pre-issue-#33
  inconsistencies will surface as halts on the new prefix
  invariant; the `sed` workaround in issue #33's body remains the
  one-shot fix.

## [0.17.1] - 2026-05-02

VS Code Marketplace publication of `aiadev-spec-explorer` v0.0.4 under
publisher `alairjoaotavares` (also published to Open VSX).

### Changed

- **vscode-extension publisher:** `aiadev` → `alairjoaotavares` (MS
  Marketplace publisher of record). Open VSX namespace
  `alairjoaotavares` also created; legacy `ai-augmented-developer`
  namespace on Open VSX remains for back-compat.
- **vscode-extension manifest:** added required `categories`
  (`Other`, `AI`, `Visualization`) and `keywords` — without
  `categories`, MS Marketplace was accepting the publish but hiding
  the listing page (404).
- **vscode-extension icon:** replaced placeholder with the final
  256×256 PNG (document + circuit-tree motif).

### Fixed

- VS Code Marketplace listing now resolves at
  `marketplace.visualstudio.com/items?itemName=alairjoaotavares.aiadev-spec-explorer`
  (previous 0.0.1–0.0.3 attempts under publishers `aiadev` /
  `ai-augmented-developer` were silently hidden by MS).

## [0.17.0] - 2026-04-29

Spec **0012 — vscode-spec-explorer**. Native VS Code tree view that
surfaces pipeline artifacts (`spec.md`, `plan.md`, `tasks.md`, research,
contracts) under each `specs/<NNNN-slug>/` directory, with one-click
open and live refresh on file changes.

### Added

- **aiadev Spec Explorer** VS Code extension (#29). Tree view in the
  Explorer sidebar lists every numbered spec directory and its
  artifacts; clicking a node opens the file in the editor. Auto-refresh
  on workspace file events.
- **Extension Host integration tests** (#30, T029) covering tree
  population, refresh on file changes, and click-to-open behavior.

### Changed

- Specs **0008**, **0009**, **0010**, **0011** marked as `Implemented`
  (status was stale — code already merged via PRs #11, #25, #28, #27).

## [0.16.0] - 2026-04-27

Spec **0010 — pipeline-preflight-checks**. Read-only `aiadev preflight`
checker that aborts pipeline skills when upstream artifacts are missing,
malformed, or incoherent. Same diagnostics in CI and in-skill.

### Added

- **Specify reconnaissance step (#26).** `specify` now requires a
  Reconnaissance pass that records the entry point, auth/session module,
  and integration points of every surface mentioned in the demand —
  before any user story is drafted. The `<!-- section: Reconnaissance -->`
  block in `templates/spec-template.md` and a new bullet micro-format
  give authors a copy-paste-passing shape, and `aiadev validate
  <spec.md>` enforces the rule for specs whose `Spec ID > 10` (earlier
  specs are grandfathered). When recon contradicts the demand's
  premise, the skill instructs the agent to pause and surface the
  mismatch instead of drafting analogy-driven user stories. Schema:
  `schemas/spec-recon.schema.json`. Spec: [0011](specs/0011-specify-reconnaissance/spec.md).
- **`aiadev.preflight.check(skill, feature_dir, …)`** + dataclass
  `PreflightIssue`. Verifies artifact presence, `<!-- section: ... -->`
  anchors, `**Language:**` and `**Branch:**` header coherence, current
  git branch / feature-dir alignment, unresolved
  `[NEEDS CLARIFICATION]` markers, and `.aiadev/review.yaml` approval
  for `finishing-a-branch`.
- **`aiadev preflight <skill> --feature <slug>`** CLI subcommand plus
  `aiadev preflight --all` for one-shot migration sweeps.
- Migration article `docs/articles/preflight.md`.

### Changed

- Pipeline `SKILL.md` files (`clarify`, `plan`, `tasks`, `implement`,
  `analyze`, `requesting-code-review`, `finishing-a-branch`) now call
  `aiadev preflight` in their Preconditions section and abort on
  non-zero unless `AIADEV_PREFLIGHT=warn` is set.
- `requesting-code-review` writes `.aiadev/review.yaml` (`status`,
  `timestamp`, optional `reason`) so the next stage can verify approval.

### Breaking

- In-flight feature directories that lack required `<!-- section: ... -->`
  anchors, drifted `**Language:**` headers, or branch / feature-dir
  mismatches now fail pre-flight on the next pipeline invocation. Run
  `aiadev preflight --all` to discover which branches need attention.
- `finishing-a-branch` aborts unless `.aiadev/review.yaml` records
  `status: approved`. Existing branches that completed review before
  this change need a manual stub.

## [0.15.0] - 2026-04-20

Spec **0009 — token-economy-terse-mode** (caveman-inspired). Opt-in terse
output contract for reviewer subagents, a generated pipeline quick-reference,
and a shorter `/aia:` command prefix. Phase 4 (Sonnet 4.6 benchmark) is
deferred to a follow-up release; every other phase lands here.

### Added

- **Terse-output contract** for `spec-document-reviewer`,
  `plan-document-reviewer`, and `code-reviewer`. One line per finding,
  severity glyph + `file:line` + ≤ 140-char message; schema at
  `schemas/terse-output.schema.json`. Off by default.
- **`aiadev.terseMode`** setting in `.claude/settings.json` with
  `AIADEV_TERSE` env override (env wins). Resolved via
  `aiadev.config.resolve_terse_mode()`, returning `(enabled, source)`
  where source is `default`, `settings`, or `env`.
- **`/aia:help`** — a generated, drift-checked pipeline quick-reference
  (`docs/pipeline-reference.md`) listing every pipeline command with
  one-line purpose and hand-off link. Pre-commit hook and CI workflow
  fail on drift. Pointer added to root `CLAUDE.md`.
- **Terse-mode rule** (`rules/terse-mode.md`) shipped to consumer
  projects via `aiadev sync`; documents the switch, the echo template
  `terse-mode: <on|off> (<source>)`, and the one-line-per-finding
  contract.
- Attribution for [`juliusbrussee/caveman`](https://github.com/JuliusBrussee/caveman)
  in `CREDITS.md` per Article VII.

### Changed

- **BREAKING:** slash-command prefix renamed from `/aiadev:` to `/aia:`
  across Claude Code, Codex, Cursor, Gemini CLI, and OpenCode. Consumer
  projects must re-run `aiadev sync` (or re-install) after upgrading.
  Old `/aiadev:*` commands will not resolve.

### Deferred

- Phase 4 live Sonnet 4.6 benchmark (T013–T016). Off-mode golden files
  are hand-crafted representatives today; the benchmark runner will
  overwrite them with real transcripts when Phase 4 lands.

## [0.14.2] - 2026-04-18

Hardening pass that closes the remaining edges of the v0.14.1
payload-contract work (issues #14–#22). No breaking changes to the
`ToolPayload` shape; everything is additive.

### Added

- **`payload["recommended_max_tokens"]`** — every `ToolPayload` now
  carries the minimum safe output-token budget for the skill so SDK
  callers can size the Anthropic `max_tokens` parameter without reading
  the docs. Values: 32,768 for `plan` / `tasks` / `implement`; 16,384
  for `specify` / `clarify` / `constitution`; 8,192 for `analyze` /
  `checklist`. Also documented in `tool-payload.schema.json` (#20).
- **HTML section anchors in `templates/spec-template.md`** —
  `<!-- section: Problem -->` anchors now precede every required
  heading. `_validate_spec_sections` reads the anchors first and the
  heading text second, so non-English specs are free to translate the
  `## <Section>` text without failing validation (#15).

### Changed

- **`skills/plan/SKILL.md`** — reframed the auxiliary outputs
  (`research.md`, `data-model.md`, `contracts/`) as *next-invocation
  hints* rather than optional deliverables. The frontmatter now lists
  only `plan.md`; the skill body tells the LLM to honour the
  orchestrator's *Single required artifact* directive. Prevents the
  failure mode where `aiadev.tools.tasks(...)` burns budget writing
  `contracts/` before producing `tasks.md` (#18).
- **Non-English language guard in `payload.build()`** — now tells the
  LLM to preserve the template's HTML anchors verbatim instead of
  forcing English headings. Heading text may be translated; the
  anchors carry the schema (#15).

## [0.14.1] - 2026-04-18

Closes the `aiadev.tools` payload-contract gaps surfaced by the first
live skill-as-prompt-loader run against the Anthropic API (issues #14–#21).

### Fixed

- **`specify(demand=...)`** now embeds the demand verbatim inside
  `payload['prompt']` under a canonical *User demand* block. Previously
  the demand only influenced the slug and the LLM saw a generic prompt
  (#14).
- **`clarify(answers=...)`** injects a *Resolved answers (batch mode)*
  block that explicitly overrides the skill's interactive "wait for the
  user's answer" branch. Callers can now resolve every `cl-N` marker in
  a single turn (#16).
- **Non-English `language`** now stamps a *Language and schema
  invariant* block that pins the canonical `## <Section>` headings in
  English so `_validate_spec_sections` still recognises the artifact
  written by the LLM (#15).
- **Skill template body** is now inlined in `payload['prompt']` as a
  fenced markdown block, so LLMs no longer have to read
  `templates/<skill>-template.md` from disk (the workspace initializer
  only drops `spec-template.md`). Fixes the silent failure where `tasks`
  wrote `contracts/` and `data-model.md` but never produced `tasks.md`
  (#17).
- **`target_path` is now flagged authoritative** in the prompt. Added a
  new `slug=` kwarg on `specify()` so callers can pin the slug when the
  demand is shorter than what the LLM will invent. Added
  `aiadev.tools.locate_latest_artifact(workspace_path, artifact=...)`
  as a fallback helper for callers whose prediction diverged (#19).

### Added

- **Single-artifact directive** — every skill prompt now carries a
  *Single required artifact* line naming the sole required output and
  explicitly forbidding auxiliary files (`contracts/`, `data-model.md`,
  `research.md`, …) in the same invocation. Reduces the failure mode
  where a `tasks` run burns budget writing the wrong artifact (#18).
- **Payload contract documentation** (`docs/articles/llm-tool-integration.md`)
  — table of which payload fields are already embedded in `prompt`
  vs which are exposed only in `context`, plus a recommended wrapper
  flow for new integrators (#21).
- **Minimum `max_tokens` per skill** documented in the integration
  guide (plan/tasks need 32k; 8k is unsafe) (#20).

## [0.14.0] - 2026-04-17

Ships the LLM tool integration (Spec 0008) and adds framework overview articles.

### Added

- **`aiadev.tools`** — Python library exposing the 8 pipeline skills (`specify`, `clarify`, `plan`, `tasks`, `implement`, `analyze`, `checklist`, `constitution`) as in-process tool functions. Each returns a `ToolPayload` dict containing the skill prompt + template + context + computed `target_path`.
- **`aiadev.mcp_server`** — MCP stdio server (via FastMCP) that exposes the same 8 skills as both `prompts` and `tools`. Run with `aiadev-mcp-server` or `python -m aiadev.mcp_server`.
- **`aiadev._tooling`** — shared core: workspace validation, skill loading, marker generation (`cl-N`), payload assembly, and JSON-lines telemetry.
- **`docs/articles/ai-augmented-developer-en.md`** and **`ai-augmented-developer-pt-br.md`** — framework overview articles (English and Brazilian Portuguese) introducing the pipeline, philosophy, and v0.3 → v0.11 release history.

### Changed

- **Marker format** — `[NEEDS CLARIFICATION]` markers now require a stable id: `[NEEDS CLARIFICATION:cl-N <question>]`. Legacy markers (without `cl-N`) are accepted with a warning for back-compat. Affects `templates/spec-template.md`, `skills/specify/SKILL.md`, `skills/clarify/SKILL.md`.
- **`.gitignore`** — ignore local `.aiadev/` install state and project-level `.mcp.json` so they stay out of framework history.

## [0.13.0] - 2026-04-17

New `aiadev lang` command (exposed as `/aia:lang`) — swap the `**Language:**` header in an in-progress feature's spec/plan/tasks without hand-editing three files.

### Added

- **`aiadev lang <bcp-47>`** (`src/aiadev/commands/lang.py`) — rewrites the `**Language:**` header in `spec.md`, `plan.md`, and `tasks.md` under the active feature directory. Feature is inferred from the current git branch slug; `--feature <dir>` overrides. `--dry-run` previews without writing. Only the header is touched — existing prose is not translated.
- **`commands/lang.md`** — slash-command wrapper rendered as `/aia:lang` in consumer projects; propagates through `iter_framework_artifacts` like the other commands.
- **`rules/slash-commands.md`** — `lang` added to the list of namespaced slash commands the agent must use in user-facing prose.

## [0.12.1] - 2026-04-16

Hand-off messages were pointing users at bare slash commands like `/plan`, which don't resolve in consumer projects — since v0.10 every command lives under the `aiadev/` namespace.

### Fixed

- **New `rules/slash-commands.md`** — cross-cutting rule that tells the agent to use the namespaced form (`/aia:plan`, `/aia:clarify`, …) whenever it references a pipeline command in user-facing prose. Skill invocation (the `Skill` tool) and internal skill-to-skill hand-off references stay on the bare name; the rule only governs what the user sees.
- The file propagates to every consumer project through `framework_artifacts.iter_framework_artifacts` and loads automatically from `.claude/rules/` on each Claude Code session.

## [0.12.0] - 2026-04-15

Two skill UX fixes: `constitution` now bootstraps from existing project context, and `clarify` always marks its recommended option.

### Changed

- **`skills/constitution`** (v0.2.0 → v0.3.0) — adds a Mode detection step that runs before the amendment loop. When invoked on a project without a `constitution.md`, the skill now enters bootstrap mode: it reads `CLAUDE.md`, `.claude/rules/*`, package files, and `README.md`, then renders `templates/constitution-template.md` with values inferred from that context, instead of asking the user generic "what change do you want?" questions. When invoked on a project with a constitution but without amendment text, it lists the current articles and asks which one to amend.
- **`skills/clarify`** (v0.2.0 → v0.3.0) — when offering multiple-choice answers for a `[NEEDS CLARIFICATION]` marker, the skill must now mark the recommended option (e.g., `★ Option A (recommended)`) with a one-line rationale grounded in the spec, the codebase, or the project conventions. New rule: making the user pick blind is laziness — the agent has enough context to commit to a recommendation.

## [0.11.1] - 2026-04-15

Hotfix: `commands/`, `rules/`, and `mcps.yaml` were missing from the published wheel, so `aiadev install` produced an empty `.claude/commands/` directory in consumer projects.

### Fixed

- **`scripts/sync_assets.py`** now copies `commands/`, `rules/`, and `mcps.yaml` into `src/aiadev/_assets/` before the wheel is built. Without them, `iter_framework_artifacts()` found nothing to install under those roles and slash commands (`/specify`, `/plan`, `/tasks`, `/implement`, etc.) silently never landed in the target project.
- **`MANIFEST.in`** declares the same trees + `mcps.yaml` + `constitution.md` so the sdist matches the wheel.

## [0.11.0] - 2026-04-15

MCP (Model Context Protocol) support: declare servers once in `mcps.yaml`, `aiadev install` writes the native config for every target platform.

### Added

- **New `mcp` install role** — seventh citizen alongside `agent_file`, `constitution`, `skill`, `command`, `agent`, `rule`. Manifest literal, JSON schema, role priority, uninstall cleanup, and user-scope eligibility all updated.
- **Canonical `mcps.yaml`** at the framework root (and optionally at `presets/<preset>/mcps.yaml`) declaring `servers: <name>: {command, args, env}`. Preset servers win on name collision.
- **`src/aiadev/mcp.py`** loader (`load_servers`, `load_servers_from_text`) with validation that surfaces bad entries instead of silently dropping them.
- **Per-platform MCP translation** via `render_target` in every handler:
  - Claude Code → `.mcp.json` (`mcpServers` key).
  - Cursor → `.cursor/mcp.json` (`mcpServers` key).
  - Gemini CLI → `.gemini/settings.json` (`mcpServers` key).
  - Codex → `.codex/config.toml` (`[mcp_servers.<name>]` tables, hand-rolled TOML to avoid adding a writer dependency).
  - OpenCode → `opencode.json` (`mcp.<name>` with `type: "local"`, `command: [exe, ...args]`, `environment`, `enabled: true`).
- **`schemas/mcps.schema.json`** — JSON Schema for the canonical declaration.
- **`tests/test_mcp.py`** — 40 tests covering the loader, per-platform `resolve_target`, `user_scope_supported`, `render_target`, and preset-scan pickup.

### Changed

- Framework-level `mcps.yaml` now ships empty (`servers: {}`) — aiadev is infrastructure-only for MCPs; teams add the servers they want and re-run `aiadev install`.

## [0.10.0] - 2026-04-15

Namespaced slash commands, numbered spec directories, and a `--language` flag for `aiadev init`.

### Added

- **`aiadev init --language/-L <BCP-47>`** stamps a `**Language:**` header into `spec.md`, `plan.md`, and `tasks.md` via a new `{{DOC_LANGUAGE}}` placeholder. Downstream skills (`clarify`, `plan`, `tasks`, `implement`, `analyze`, `checklist`) read that header and continue in the same language. Default: `en`.

### Changed

- **Slash commands are namespaced under `aiadev/`** across every platform (`.claude/commands/aiadev/<name>.md`, `.codex/`, `.cursor/`, `.opencode/` equivalents, and `.gemini/commands/aiadev/<name>.toml`). Claude Code and Gemini CLI render them as `/aia:specify`, `/aia:plan`, etc. Consumer projects must run `aiadev sync` to migrate; the old flat layout leaves orphan files until cleaned up.
- **Spec directories carry the zero-padded `SPEC_ID` prefix** (`specs/0001-<slug>/`, `specs/0002-<slug>/`, …) instead of the legacy `specs/feature-<slug>/`. `aiadev init` computes the next id monotonically from existing specs. Skills and the `specify` command doc updated to reflect the `specs/<NNNN-slug>/` convention.

## [0.9.0] - 2026-04-15

Full-install and sync. `aiadev install` now equips a project with the complete pipeline (slash commands + agents + framework-generic skills + coding rules) out of the box, across all 5 platforms. A new `aiadev sync` command pulls framework updates into installed projects and regenerates a detected-stack block inside `CLAUDE.md`.

### Added

- **Three new artifact roles** — `command`, `agent`, `rule` — alongside the existing `agent_file`, `constitution`, and `skill`. `FileRole` in `src/aiadev/install_manifest.py` and the JSON schema at `schemas/install-manifest.schema.json` are both extended; the manifest stays forward-compatible.
- **Framework-generic scan** (`src/aiadev/framework_artifacts.py`). Every install now also copies the commands/agents/rules/skills that ship with `aiadev` itself, not just the preset's own. Preset artifacts win on `(role, name)` collision.
- **14 pipeline slash commands** under `commands/` — one per skill (`specify`, `clarify`, `plan`, `tasks`, `implement`, `analyze`, `checklist`, `constitution`, `finishing-a-branch`, `frontend-design`, `requesting-code-review`, `systematic-debugging`, `test-driven-development`, `using-ai-augmented-developer`) plus `sync`.
- **3 agents** with proper Claude Code frontmatter (`code-reviewer`, `plan-document-reviewer`, `spec-document-reviewer`).
- **5 coding rules** under `rules/`: `code-style`, `testing`, `api-conventions`, `security`, `git-workflow`.
- **`aiadev sync`** command. Re-runs every installed preset (pulling framework updates into the project) and regenerates a `<!-- aiadev:auto-stack:start -->` block inside the agent file from a project introspection (package.json, pyproject.toml, Cargo.toml, go.mod, pubspec.yaml, docker-compose, Makefile, .github/workflows). Flags: `--dry-run`, `--force`, `--skip-artifacts`, `--skip-stack`, `--platform`.
- **`src/aiadev/project_introspect.py`** with a deterministic `StackReport` dataclass and `apply_stack_block` marker-aware replacer. Content outside the markers is preserved byte-for-byte; when markers are missing, a fresh block is appended and the user is warned.
- **Platform-specific layouts** for the new roles:
  - `.claude/commands/*.md`, `.claude/agents/*.md`, `.claude/rules/*.md`.
  - `.cursor/commands/*.md`, `.cursor/agents/*.md`, `.cursor/rules/*.mdc` (Cursor native rules extension).
  - `.codex/` and `.opencode/` mirror the Claude Code layout.
  - `.gemini/commands/*.toml` (Gemini CLI reads TOML — the handler converts markdown via the new `render_target` hook), `.gemini/agents/*.md`, `.gemini/rules/*.md`.
- Spec `specs/feature-full-install-and-sync/spec.md` captures the feature requirements.

### Changed

- Framework-generic artifacts are copied **verbatim** (no variable substitution, no unresolved-placeholder check). Skills like `specify/SKILL.md` intentionally carry runtime markers such as `{{BRANCH}}` and `{{TEST_COMMAND}}` that the AI fills in at runtime, not at install time. Preset-owned artifacts still pass through `substitute()`.
- Uninstall climbs empty directories for `skill`, `command`, `agent`, and `rule` roles so `.claude/commands/`, `.claude/rules/`, etc., vanish cleanly when the last file is removed.
- Platform handlers gain an optional `render_target(role, name, text)` hook; only Gemini overrides it today (to emit TOML commands).
- User scope now supports `skill`, `command`, `agent`, and `rule` (all shareable, no project-specific variables). `agent_file` and `constitution` remain project-only.

## [0.8.0] - 2026-04-14

Extensions system MVP. Third-party preset catalogs become installable.

### Added

- **`aiadev extension <add|list|remove>`** lets users install third-party preset catalogs from any git URL. Extensions land at `~/.aiadev/extensions/<name>/`; the registry at `~/.aiadev/extensions/registry.yaml` records each install. `aiadev install --preset <name>` falls back to extension-provided presets when no built-in matches; built-in presets win on name collision and the user is told when an extension is shadowed.
- `src/aiadev/extensions.py` (~140 stmts, 89% coverage): `add(url)`, `list_all()`, `remove(name)`, `find_preset(preset_name)`, `load_extension_manifest(dir)`. Atomic registry write mirrors the install manifest pattern.
- `src/aiadev/commands/extension.py`: click group with `add URL`, `list`, `remove NAME` subcommands; rich.Table output for `list`.
- `schemas/extension-manifest.schema.json`: declared shape of the `extension.yaml` an extension repo must ship at its root (name, version, optional description / homepage / presets list).
- `tests/fixtures/extensions/sample-extension/`: tiny extension fixture (extension.yaml + presets/sample/{preset.yaml, CLAUDE.md, skills/hello/SKILL.md}).
- E2E round-trip test exercises `extension add` -> `install --preset` -> `install --uninstall` -> `extension remove` against a fake `$HOME`. The real home is never touched.
- README gains an "Extensions (third-party presets)" subsection with one example and a security caveat.

### Changed

- `src/aiadev/commands/install.py` resolves `--preset <name>` against built-ins first and registered extensions second; reports a one-line note when an extension preset is shadowed by a built-in.

## [0.7.0] - 2026-04-14

PyPI distribution. `pip install aiadev` works after the v0.7.0 release event triggers the new publish workflow.

### Added

- **PyPI distribution.** Wheel ships the framework's `constitution.md`, `templates/`, `schemas/`, `skills/`, `presets/`, and `agents/` so the CLI runs anywhere — no checkout required. `aiadev doctor` resolves the framework root from the bundled `_assets/` directory.
- `scripts/sync_assets.py` copies the source-of-truth dirs into `src/aiadev/_assets/` before `python -m build`. The destination is gitignored; run it whenever the source dirs change.
- `MANIFEST.in` ships the same trees in the sdist.
- `pyproject.toml` declares the new `package-data`, `include-package-data`, and `[project.optional-dependencies].dev` now includes `build`.
- `__init__.__version__` resolves via `importlib.metadata` first, falling back to the repo-root `VERSION` file. Installed wheels report the real version instead of `0.0.0+unknown`.
- `.github/workflows/publish.yml` triggered by `release: published`. Two jobs (build → publish) using OIDC trusted publishing — no API tokens stored in the repo. The `pypi` GitHub environment must be configured once; see `docs/RELEASING.md`.
- `docs/RELEASING.md` covers the one-time pypi.org trusted-publisher setup, the routine release flow, common failure modes, and a post-publish smoke test.
- `CONTRIBUTING.md` release section condensed to a pointer at `docs/RELEASING.md` plus a four-line cheat sheet.

### Changed

- `find_framework_root` gained a final fallback: `aiadev/_assets/` adjacent to the installed package. Previous fallbacks (env var, parent walk, git toplevel, `parents[2]` editable install) are preserved.

### Fixed

- `.github/workflows/validate.yml` link-check now excludes `https://pypi.org/manage/` URLs (they require auth and 404 to anonymous probes; they appear in `docs/RELEASING.md` as instructions for the maintainer).

## [0.6.0] - 2026-04-14

Per-home install scope: install a preset's skills once for the current user instead of repeating it per project.

### Added

- **`aiadev install --scope user`** — install a preset's skills at the current user's home directory so every project picks them up without per-project symlinks. Skills go to `~/.<platform>/skills/<name>/SKILL.md` for each wired platform (`.claude`, `.cursor`, `.codex`, `.opencode`, `.gemini`). Manifest lives at `~/.aiadev/installed.yaml`, separate from any project-scope manifest so idempotency and uninstall stay correct under mixed installs.
- `InstallReport.skipped_unsupported` — list of human-readable notes covering artifacts the platform refuses to install under the current scope. Under `--scope user` this flags every preset-declared agent file (`CLAUDE.md`, `AGENTS.md`, `GEMINI.md`) and `constitution.md`, which carry project-specific variables and stay project-local.
- Each platform handler grew a `user_scope_supported(role)` predicate. `resolve_target` now takes `install_root` (instead of the old `project_root`) plus a `scope=` keyword so the engine can route paths from either `$HOME` or the project directory.
- End-to-end user-scope round-trip test (`test_user_scope_round_trip_with_fake_home`) installs the 11-skill `mobile-ops` preset against a `monkeypatch`-ed fake `$HOME`, asserts no project-side writes and no real-home pollution, then uninstalls clean.
- CLI `--project-root` is documented as ignored under `--scope user`.

### Changed

- `install_engine.install(...)` takes a new `scope: str = "project"` keyword. Default preserves v0.5 behaviour exactly.
- `_perform_uninstall` and all internal helpers use `install_root` instead of `project_root` so the same code path covers both scopes.
- Report header in the CLI now shows the scope alongside the mode (`install (scope: user)`).
- README install block documents the user-scope variant.

## [0.5.0] - 2026-04-14

Final three platform handlers: Codex, OpenCode, Gemini. All five advertised platforms are now wired.

### Added

- **Three new platform handlers** wired into `aiadev install`:
  - `--platform codex` — `AGENTS.md` + `.codex/skills/<name>/SKILL.md`.
  - `--platform opencode` — `AGENTS.md` + `.opencode/skills/<name>/SKILL.md`.
  - `--platform gemini` — `GEMINI.md` + `.gemini/skills/<name>/SKILL.md` (distinct agent-file name so it does not collide with Cursor/Codex/OpenCode's `AGENTS.md`).
- Each platform module is self-contained at ~30 lines with 100% unit coverage (11 cases each).
- Coexistence tested: installing multiple IDEs against the same project sees `AGENTS.md` as a skip on every run after the first (sha256 match), while the per-platform skills directories stay isolated.
- End-to-end round-trip for Codex mirrors the Claude Code and Cursor e2e tests (11-skill `mobile-ops` preset, 15 placeholders, uninstall hygiene).
- README documents the five-value `--platform` option with per-platform install examples.

### Caveats

- Per-home install flows (symlinks under `~/.codex/`, `~/.config/opencode/`, `gemini extensions install`) are still documented in the platform-specific `INSTALL.md` files. `aiadev install` writes the per-project layout; some IDEs may need one-line configuration to discover `.codex/skills/` or `.opencode/skills/` depending on the user's setup. A unified per-home install path is v0.6 scope.

## [0.4.0] - 2026-04-14

Second install target: Cursor.

### Added

- **Cursor platform handler** (`aiadev install --platform cursor`). Drops `AGENTS.md` at the project root (so Cursor and Claude Code can coexist without clashing on their agent-file names) and writes skills under `.cursor/skills/<name>/SKILL.md`. The `constitution.md` file is shared — both handlers read the same file at project root.
- End-to-end round-trip test for the Cursor target (`test_cursor_platform_round_trip`): installs the 11-skill mobile-ops preset with 15 placeholders, verifies every skill lands at the Cursor path, no `{{UPPER_SNAKE}}` token survives, and uninstall leaves the project clean.

### Changed

- `_perform_uninstall` in `install_engine.py` now walks up each skill's path and removes ancestor directories when empty, so `aiadev install --uninstall` leaves the project free of stray `.claude/`, `.cursor/`, or `.aiadev/` directories.
- README install example documents the `--platform cursor` variant.

## [0.3.0] - 2026-04-14

Working `aiadev install` shipped. Replaces the v0.2 stub end to end.

### Added

- `aiadev install --preset <name>` now renders a preset into the consumer project. Replaces the v0.2 stub. Features:
  - **Interactive prompts** for every variable declared by `preset.yaml` (uses `click.prompt`). Previous values from the install manifest become the prompt's default on re-installs; preset-declared defaults fill in for new installs.
  - **Non-interactive mode** (`--non-interactive`) fails loudly if a required variable is missing. Accepts `--vars KEY=VAL,KEY2=VAL2` (multiple invocations allowed; later overrides earlier; commas-in-values handled by repeating `--vars`).
  - **Idempotent re-install**: sha256 of every installed file is recorded in `.aiadev/installed.yaml`. Re-running the command skips files that are still identical, rewrites files when variables change, and flags drift (hand-edited files) as conflicts unless `--force` is passed.
  - **Dry run** (`--dry-run`) prints the planned actions without touching the filesystem.
  - **Uninstall** (`--uninstall`) removes every file listed in the manifest for that preset. Drifted files block the uninstall unless `--force`.
  - **`--allow-unresolved`** escape hatch for partially-declared presets: writes files with literal `{{KEY}}` tokens still in them and surfaces the missing keys in the output.
  - **Rich output**: coloured table with `write / skip / remove / conflict` columns, plus a conflict hint pointing at `--force`.
- `AIADEV_ROOT` environment variable + package-location fallback so the CLI works from any directory once `pip install -e .` (or a PyPI release, future) has been done. Before v0.3 the CLI required the user to `cd` into the framework tree.
- New modules:
  - `src/aiadev/placeholders.py` — single-pass substitution with regex (no Jinja2); 100% covered.
  - `src/aiadev/install_manifest.py` — atomic YAML IO, sha256 helpers, schema-validated.
  - `src/aiadev/platforms/claude_code.py` — target-path policy for Claude Code (`.claude/skills/<name>/`, `CLAUDE.md` at root, etc). Cursor/Codex/OpenCode/Gemini to follow in v0.4 with the same two-function contract.
  - `src/aiadev/install_engine.py` — orchestrator. 98% covered.
  - `src/aiadev/variable_prompt.py` — collection + `--vars` parsing. 100% covered.
- `schemas/install-manifest.schema.json` — JSON Schema for the per-project manifest.
- `tests/fixtures/mini-preset/` — one-skill fixture driving the engine round-trip tests.
- CI workflow gains an `install-e2e` job on Python 3.12 running the round-trip suite.

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

[Unreleased]: https://github.com/suportly/ai-augmented-developer/compare/v0.8.0...HEAD
[0.8.0]: https://github.com/suportly/ai-augmented-developer/compare/v0.7.0...v0.8.0
[0.7.0]: https://github.com/suportly/ai-augmented-developer/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/suportly/ai-augmented-developer/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/suportly/ai-augmented-developer/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/suportly/ai-augmented-developer/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/suportly/ai-augmented-developer/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/suportly/ai-augmented-developer/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/suportly/ai-augmented-developer/releases/tag/v0.1.0
