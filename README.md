# AI-Augmented Developer

AI-Augmented Developer is a complete software development workflow for your coding agents, built on top of a set of composable "skills" and some initial instructions that make sure your agent uses them.

## How it works

It starts from the moment you fire up your coding agent. As soon as it sees that you're building something, it *doesn't* just jump into trying to write code. Instead, it steps back and asks you what you're really trying to do.

Once it's teased a spec out of the conversation, it shows it to you in chunks short enough to actually read and digest.

After you've signed off on the design, your agent puts together an implementation plan that's clear enough for an enthusiastic junior engineer with poor taste, no judgement, no project context, and an aversion to testing to follow. It emphasizes true red/green TDD, YAGNI (You Aren't Gonna Need It), and DRY.

Next up, once you say "go", the `implement` skill takes over: it dispatches one fresh subagent per task, runs a spec compliance review and a code quality review after each, and moves forward only when both pass. The agent can run through several tasks unattended as long as the plan stays accurate — your job is to check in, not to babysit every step.

There's a bunch more to it, but that's the core of the system. And because the skills trigger automatically, you don't need to do anything special. Your coding agent just has AI-Augmented Developer superpowers.

## Installation

### Recommended — via the `aiadev` CLI

From v0.3 onward the supported path is the Python CLI, which renders a
preset (variables substituted, files placed) into the current project:

```bash
# 1. Install the CLI (editable install from a clone, or a release tag)
pip install -e git+https://github.com/suportly/ai-augmented-developer.git#egg=aiadev

# 2. Install a preset into your project
cd your-project
aiadev install --preset lean              # framework-only pipeline
# or
aiadev install --preset django-drf-react  # full-stack web preset
# or
aiadev install --preset mobile-ops        # operational runbooks for Cloud Run + Expo

# Pick your coding IDE with --platform. All five are wired:
#   claude-code (default), cursor, codex, opencode, gemini.
aiadev install --preset lean --platform cursor
aiadev install --preset lean --platform codex
aiadev install --preset lean --platform gemini

# CI-friendly variant: every variable on the command line, no prompts.
aiadev install --preset lean --non-interactive --vars PROJECT_NAME=MyApp

# Re-run to update; drift from hand-edits is flagged as conflict
# unless you pass --force.
aiadev install --preset lean

# Preview without writing.
aiadev install --preset lean --dry-run

# Remove everything the install wrote.
aiadev install --preset lean --uninstall

# User-scope install: skills land under ~/.codex/skills/, etc. so every
# project on this machine can pick them up. Agent files and constitutions
# stay project-local (they carry project-specific variables) and are
# reported as skipped.
aiadev install --preset mobile-ops --platform codex --scope user \
    --non-interactive --vars PROJECT_NAME=Demo,APP_NAME=Demo,...
```

`aiadev doctor` then verifies the repo is in good shape.

### Extensions (third-party presets)

Install presets that live in any git repo:

```bash
# Add an extension once. The repo must contain an `extension.yaml`
# at its root and a `presets/<preset-name>/` tree.
aiadev extension add https://github.com/example/rails-preset.git

# `aiadev install --preset rails` now works in any project. Built-in
# presets win on name collision; a yellow "note" reports the shadow.
aiadev install --preset rails --non-interactive --vars PROJECT_NAME=Demo

# Inspect or clean up.
aiadev extension list
aiadev extension remove rails-preset
```

Extensions are git URLs only — no central registry, no signing, no
auto-update. Each `extension add` runs one `git clone --depth 1` into
`~/.aiadev/extensions/<name>/`. Inspect any third-party extension
before installing it: it can ship arbitrary skill content.

To **author** an extension, see the format documented in
[`schemas/extension-manifest.schema.json`](./schemas/extension-manifest.schema.json)
and the `tests/fixtures/extensions/sample-extension/` reference.

### Platform-specific plugins (unchanged from v0.2)

The legacy plugin install paths still work; they drop the skills catalog
into your agent without creating an install manifest.

#### Claude Code

```bash
/plugin marketplace add suportly/ai-augmented-developer
/plugin install ai-augmented-developer@ai-augmented-developer-marketplace
```

### Cursor

```text
/add-plugin https://github.com/suportly/ai-augmented-developer
```

### Gemini CLI

```bash
gemini extensions install https://github.com/suportly/ai-augmented-developer
```

To update:

```bash
gemini extensions update ai-augmented-developer
```

### Codex

Tell Codex:

```
Fetch and follow instructions from https://raw.githubusercontent.com/suportly/ai-augmented-developer/refs/heads/main/.codex/INSTALL.md
```

**Detailed docs:** [docs/README.codex.md](docs/README.codex.md)

### OpenCode

Tell OpenCode:

```
Fetch and follow instructions from https://raw.githubusercontent.com/suportly/ai-augmented-developer/refs/heads/main/.opencode/INSTALL.md
```

**Detailed docs:** [docs/README.opencode.md](docs/README.opencode.md)

### Verify Installation

Start a new session in your chosen platform and ask for something that should trigger a skill (for example, "help me plan this feature" or "let's debug this issue"). The agent should automatically invoke the relevant skill.

### `AGENTS.md` — the canonical agent file

`aiadev sync` writes a single canonical `AGENTS.md` at your project
root — the cross-tool convention that Claude Code, Cursor, Codex, and
OpenCode all read natively (Gemini CLI keeps its own `GEMINI.md`, also
generated as a thin wrapper). `CLAUDE.md`/`GEMINI.md` become ~3-line
pointers instead of duplicating generated content, so the five
platforms can no longer silently diverge. Any manual content you
already had in those files is preserved and merged into `AGENTS.md`'s
migration block the first time `aiadev sync` runs against it (a
`.bak` copy of the original is kept alongside). See
[docs/agent-skills-interop.md](docs/agent-skills-interop.md) for the
full migration walkthrough.

## Inspecting your audit trail with `aiadev metrics`

Every feature you run through the pipeline leaves a structured trail
(`.review-log.jsonl`, `tasks.md` statuses, spec headers). The
`aiadev metrics` subcommand aggregates that trail into the indicators
a tech lead actually needs — first-pass approval rate per reviewer,
tasks that needed rework, coverage of the post-`0014` cutoff, time
from `specify` to last commit, and unresolved clarification markers.

```bash
# Saúde de uma feature em andamento
aiadev metrics --feature 0015-aiadev-metrics

# Visão agregada (default: últimos 90 dias)
aiadev metrics

# Para CI / scripts (schema estável, sem timestamp de execução)
aiadev metrics --format json --since 2026-01-01

# Detalhe por task (Story 3)
aiadev metrics --feature 0015-aiadev-metrics --tasks
```

Nada é enviado pela rede; o comando é read-only. A prosa livre dos
reviewers fica fora da saída padrão (Article VI) — use
`--show-bodies` se precisar inspecionar.

Detalhes: [docs/metrics.md](docs/metrics.md).

## Keeping plugin manifests in sync with `aiadev manifests`

`.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, and
`.cursor-plugin/plugin.json` are generated from `VERSION` +
`pyproject.toml` + `presets/catalog.json` — no more hand-edited
manifests drifting from the release version.

```bash
# Read-only check (default); fails naming the file and the
# diverging values when a manifest is out of sync.
aiadev manifests

# Regenerate all three in place. Idempotent.
aiadev manifests --write
```

Every `stable` preset in `presets/catalog.json` gets a corresponding
marketplace plugin entry automatically. Details:
[docs/agent-skills-interop.md](docs/agent-skills-interop.md).

## Use as LLM tools

The 8 pipeline skills can be invoked programmatically by any LLM agent, outside of Claude Code or other IDE harnesses.

### Python library (in-process)

```python
from aiadev.tools import specify, clarify, plan, tasks

# 1. Generate a spec
payload = specify(demand="Add user authentication", workspace_path="/path/to/project")
# payload["prompt"]      → SKILL.md content + template + constitution excerpt
# payload["target_path"] → /path/to/project/specs/0001-add-user-authentication/spec.md
# Your LLM follows the prompt and creates the file at target_path.

# 2. Resolve clarifications
result = clarify(
    spec_path="/path/to/project/specs/0001-add-user-authentication/spec.md",
    workspace_path="/path/to/project",
    answers=[{"id": "cl-1", "answer": "Use JWT with httpOnly cookies."}],
)

# 3. Generate plan and tasks
plan_result = plan(spec_path="...", workspace_path="...")
tasks_result = tasks(plan_path="...", workspace_path="...")
```

All functions return a `ToolPayload` dict (see `specs/0008-llm-tool-integration/contracts/tool-payload.schema.json` for the schema). The payload contains the skill prompt, template, context, and a computed `target_path` — the caller LLM follows the instructions to create the artifact.

### MCP stdio server

Add to your MCP configuration (e.g. `.mcp.json`):

```json
{
  "mcpServers": {
    "aiadev": {
      "command": "aiadev-mcp-server",
      "args": []
    }
  }
}
```

The server exposes the same 8 skills as both MCP `prompts` and `tools`. Requires `pip install 'aiadev[mcp]'`.

## The Basic Workflow

1. **specify** — Activates first. Turns a natural-language demand into a `spec.md` under `specs/<branch>/`, surfacing any ambiguity as `[NEEDS CLARIFICATION: …]` markers instead of guessing.

2. **clarify** — Walks the user through the clarification markers one at a time and rewrites the spec with the answers. The spec stays unapproved while any marker is unresolved.

3. **plan** — Turns the clean spec into a `plan.md` that fills the Constitution Check table, maps project structure changes, and splits the work into phases.

4. **tasks** — Decomposes the plan into an ordered `tasks.md` where each task = one failing test + one implementation + one commit, with dependencies declared.

5. **implement** — Dispatches one fresh subagent per task with a two-stage review (spec compliance, then code quality) before advancing. One task per commit; never skip either review.

6. **analyze**, **checklist** — Cross-checks. `analyze` reports drift between spec, plan, tasks, and actual code. `checklist` runs a category pass (security, performance, accessibility, i18n, privacy, observability).

7. **test-driven-development**, **systematic-debugging** — Invoked inside `implement`. RED-GREEN-REFACTOR for new work; four-phase root-cause investigation for failures.

8. **requesting-code-review**, **finishing-a-branch** — Pre-PR review and merge hygiene. Close the loop back to the spec.

**The agent checks for relevant skills before any task.** These are mandatory workflows, not suggestions.

## What's Inside

### Skills (14 generic + preset)

**Pipeline**
- **specify** — Natural-language demand → numbered `spec.md` with `[NEEDS CLARIFICATION]` markers for ambiguity.
- **clarify** — Surfaces those markers one at a time and rewrites the spec with the answers.
- **plan** — Turns an approved spec into `plan.md` with a mandatory Constitution Check.
- **tasks** — Ordered `tasks.md`; one task = one test + one implementation + one commit.
- **implement** — Fresh subagent per task with two-stage review (spec compliance, then code quality).
- **analyze** — Gap report between spec, plan, tasks, and code.
- **checklist** — Category pass: security, performance, accessibility, i18n, privacy, observability.
- **constitution** — Amend the framework/preset/project constitution through the documented process.

**Quality**
- **using-ai-augmented-developer** — Meta-skill that orients the agent to the catalog and skill rule.
- **test-driven-development** — RED-GREEN-REFACTOR cycle, strictly enforced.
- **systematic-debugging** — 4-phase root-cause investigation before any fix.
- **requesting-code-review** — Pre-PR checklist and reviewer agent dispatch.
- **finishing-a-branch** — PR creation, merge decision, cleanup.
- **frontend-design** — Production-grade UI with distinctive, non-generic aesthetics.

**Stack skills (via presets)**

Stack-specific skills live under `presets/<preset>/skills/` and load only when that preset is active. The bundled `django-drf-react` preset ships:

- **django-patterns** — App / model / serializer / view / URL conventions.
- **ai-integration** — LiteLLM + Claude Agent SDK providers.
- **celery-async** — Background task patterns, scheduling, retries.
- **autodev-pipeline** — Proactive auto-development pipeline.
- **deploy** — Cloud Run + EAS deployment runbooks.
- **run-tests** — pytest backend + Jest frontend entry point.

A minimal `lean` preset is also available for projects with an exotic stack. There is also an experimental, opt-in `knowledge-graph` preset (spec 0017) that declares an optional knowledge-graph context provider so the `analyze` skill can ground its drift gaps in cited graph facts (`arquivo:símbolo` with a confidence label) instead of inference alone; it ships nothing mandatory and `analyze` degrades to its provider-free behaviour when no provider is configured. See `presets/catalog.json` for the full list.

### Commands

Skills are invoked directly by name — there are no thin command wrappers in v0.2. Earlier versions shipped `/brainstorm`, `/write-plan`, `/execute-plan`, `/speckit`, `/debug`; these redirected to skills with no added behavior and were removed. Call the skills themselves instead.

### Agents (3 total)

- **spec-document-reviewer** — Validates specs for completeness, clarity, and testability
- **plan-document-reviewer** — Validates plans for TDD compliance, exact file paths, and step granularity
- **code-reviewer** — Reviews code for security, spec alignment, and quality

### VS Code extension

The repo also ships **aiadev Spec Explorer**, a VS Code extension that renders the `specs/` tree (with pipeline state, task rollups, clarification markers, and current-branch highlight) directly in the activity bar. See [`vscode-extension/README.md`](./vscode-extension/README.md) for install instructions and configuration.

## Philosophy

- **Test-Driven Development** — Write tests first, always
- **Design before code** — No implementation without an approved spec
- **Systematic over ad-hoc** — Process over guessing
- **Complexity reduction** — Simplicity as primary goal
- **Evidence over claims** — Verify before declaring success

## Updating

```bash
/plugin update ai-augmented-developer
```

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for the full workflow (issue-first, one concern per PR, skill frontmatter rules). Bug reports and security issues follow [SECURITY.md](./SECURITY.md). Changes are logged in [CHANGELOG.md](./CHANGELOG.md).

## Credits

This framework builds on prior work from `obra/superpowers` and `github/spec-kit`. See [CREDITS.md](./CREDITS.md) for the full attribution list.

## License

MIT License — see LICENSE file for details

## Support

- **Issues**: https://github.com/suportly/ai-augmented-developer/issues
