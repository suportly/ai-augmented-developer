# AI-Augmented Developer: the framework that turns your AI agent into a disciplined engineer

> In 48 hours, from v0.3 to v0.11 — nine releases, five platforms, PyPI distribution, an extensions system and MCP support.

## The problem nobody wants to admit

If you build with AI, you know the loop: you describe a feature, the agent jumps straight into writing code before understanding the problem, skips the tests, invents context, and three hours later you're reviewing an 800-line diff only to find half of it doesn't do what you asked.

That isn't (only) the model's fault. It's the absence of process. Senior engineers don't open the editor first — they specify, plan, test, review. The agent was missing that same method.

That's exactly what **AI-Augmented Developer** delivers.

## What it is

AI-Augmented Developer (`aiadev`) is a complete workflow framework for coding agents. It installs a set of **composable skills** and bootstrap instructions that make sure the agent uses them **automatically** — you don't have to remember anything.

The philosophy is blunt:

- **Spec-first**: no code without an approved spec.
- **Test-first**: RED-GREEN-REFACTOR is a contract, not a suggestion.
- **Evidence over claims**: verify before declaring success.
- **Simplicity as primary goal**: YAGNI and DRY are laws, not tips.

The standard pipeline has eight stages:

```text
specify → clarify → plan → tasks → implement
                                       │
                          test-driven-development (per task)
                          systematic-debugging (on failures)
                          checklist (security, perf, a11y, i18n…)
                                       ↓
                               analyze → requesting-code-review → finishing-a-branch
```

Each stage is a skill that fires on its own at the right moment. The agent doesn't skip steps. It doesn't invent context. It shows you the spec before writing the first test.

## The constitution: seven non-negotiable articles

The heart of the framework is [`constitution.md`](../../constitution.md), with seven principles every technical decision must honor:

1. **Spec-first** — no approved spec, no code.
2. **Test-first** — failing test before implementation.
3. **Simplicity** — the simplest thing that works.
4. **Evidence over claims** — run it, prove it, show it.
5. **Provider pattern** — external dependencies behind interfaces.
6. **Privacy by design** — sensitive data never leaks to LLMs.
7. **Attribution** — credit every derivative work.

Every plan produced by the `plan` skill carries a **Constitution Check** table. Broke an article? It goes into the Complexity Tracking section with a justification. Without that discipline, the framework refuses to move forward.

## The recent evolution: two days that changed the game

Between **April 14 and 15, 2026**, the project shipped from v0.3 to v0.11. Each release tackled a real friction point for daily users.

### v0.3 — Interactive `aiadev install`

The Python CLI finally replaces ad-hoc scripts. A single command renders a preset (variables substituted, files placed) into your project, with `--dry-run`, `--uninstall` and drift detection against hand edits.

### v0.4 — Cursor

First platform handler beyond Claude Code. Full end-to-end round-trip, with docs.

### v0.5 — Codex, OpenCode, Gemini

Three more platforms in a single release. The five major AI development tools are now covered: **Claude Code, Cursor, Codex, OpenCode and Gemini CLI**. Each handler is a self-contained ~30-line module with 100% test coverage.

### v0.6 — User scope

`--scope user` installs skills once per machine, under `~/.<platform>/skills/`. Every project on your workstation inherits the same catalog, with no repeated setup. Files with project-specific variables (CLAUDE.md, constitution.md) stay project-local.

### v0.7 — PyPI

`pip install aiadev` now works. The wheel bundles `constitution.md`, `templates/`, `schemas/`, `skills/`, `presets/` and `agents/` — no repo clone required. Publish via OIDC trusted publishing, no tokens stored in the repo.

### v0.8 — Extensions system

`aiadev extension add <git-url>` lets anyone ship third-party preset catalogs. Community catalogs, private corporate presets, experimental presets — anyone can publish. Built-ins win on name collisions, with a yellow note when an extension is shadowed.

### v0.9 — Full install + `aiadev sync`

Maybe the biggest turn. `install` now equips a project with the **entire pipeline** in one go: 14 slash commands, 3 agents, 5 coding rules and the full catalog of generic skills. The new `aiadev sync` pulls framework updates into already-installed projects and regenerates an `<!-- aiadev:auto-stack -->` block inside `CLAUDE.md` from project introspection (package.json, pyproject.toml, Cargo.toml, go.mod, pubspec.yaml, docker-compose, Makefile, GitHub workflows).

### v0.10 — Namespacing and sequential specs

Slash commands gain a namespace: `/aia:specify`, `/aia:plan`, `/aia:implement`. Specs leave the `feature-<slug>/` scheme behind for zero-padded sequential IDs: `specs/0001-<slug>/`, `0002-…`. Plus: `aiadev init --language pt-BR` makes the whole pipeline (clarify, plan, tasks, implement, analyze, checklist) speak the chosen language.

### v0.11 — MCP across every platform

The **Model Context Protocol** becomes a first-class citizen. You declare servers once in `mcps.yaml` and `aiadev install` translates them to each platform's native format:

- Claude Code → `.mcp.json`
- Cursor → `.cursor/mcp.json`
- Gemini CLI → `.gemini/settings.json`
- Codex → `.codex/config.toml`
- OpenCode → `opencode.json`

Forty tests cover the loader, per-platform translation and preset pickup. MCP stops being repetitive setup and becomes a configuration detail.

## Why it matters

Look at the curve: nine releases in 48 hours, each one solving a concrete pain — without regressions, without breaking existing users, with tests and docs in every step. That's the framework applying itself to itself. Specs live under [`specs/`](../../specs/), the plans were generated by the `plan` skill, the commits follow the `feat(<area>): T<N> <title>` pattern from the `tasks` skill.

For anyone building with AI, `aiadev` solves four problems at once:

| Pain | Framework answer |
|---|---|
| Agent codes without understanding | `specify` skill forces specification first |
| Code without tests / tests after | `test-driven-development` skill enforces RED-GREEN-REFACTOR |
| Forgotten decisions / drift | `analyze` skill reports divergence between spec/plan/tasks/code |
| Manual setup per project | `aiadev install` + `--scope user` + extensions cover all of it |

Best of all: you don't need to remember to invoke anything. Skills fire by themselves at the right moment, on all five supported platforms, with a single MCP server declaration, with clean PRs at the end.

## How to start

```bash
# 1. Install the CLI
pip install aiadev

# 2. Enter a project and install the preset that fits
cd your-project
aiadev install --preset lean              # generic pipeline
aiadev install --preset django-drf-react  # full-stack web
aiadev install --preset mobile-ops        # Cloud Run + Expo

# 3. Pick the platform (default: claude-code)
aiadev install --preset lean --platform cursor

# 4. Working in another language? Initialize with the language flag
aiadev init --language en

# 5. Verify
aiadev doctor
```

Start a fresh session, ask for a feature in natural language, and watch the agent reach for `specify` before the first line of code.

## Who should use it

- **Solo devs** who want productivity without losing quality.
- **Teams** that need consistent process across multiple contributors and agents.
- **Companies** that need to standardize AI usage without locking into a single tool.
- **Maintainers of internal presets** — the extensions system covers corporate distribution.

## What comes next

The pipeline is complete, the five platforms are wired, MCP is integrated. The natural next steps are themed presets (data, ML, infra), opt-in telemetry to understand which skills produce the most value, and tooling to validate specs through specialized agents.

But the most important point is already there: the framework is **complete** enough for daily use, **disciplined** enough for serious projects, and **open** enough for the community to evolve.

---

**Repository:** <https://github.com/suportly/ai-augmented-developer>
**Current version:** 0.11.0 (Apr 15, 2026)
**License:** MIT
**Install:** `pip install aiadev`
