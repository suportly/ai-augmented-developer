# Agents

Agents are subagent definitions invoked by skills. They fall into two
groups in this repository:

- **Framework-native agents** live at the top of this directory. They
  are written for the framework itself and are used by the pipeline
  skills regardless of the active preset.
- **Preset-specific agents** live under `presets/<preset>/agents/`. They
  assume a particular stack and load only when that preset is active.

## Framework-native agents

| Agent | Used by | Purpose |
|---|---|---|
| [`spec-document-reviewer`](./spec-document-reviewer.md) | `specify`, `clarify` | Reviews `spec.md` for completeness, clarity, testability. |
| [`plan-document-reviewer`](./plan-document-reviewer.md) | `plan` | Reviews `plan.md` for TDD compliance, exact file paths, and step granularity. |
| [`code-reviewer`](./code-reviewer.md) | `implement`, `requesting-code-review` | Reviews code for security, spec alignment, and quality. |

These three are the only agents guaranteed to exist on every install.

## The multi-discipline catalog (design / engineering / marketing / …)

A popular community catalog of subagents organized by discipline
(`design/`, `engineering/`, `marketing/`, `studio-operations/`,
`testing/`, `project-management/`, `product/`) is widely referenced —
notably at [contains-studio/agents](https://github.com/contains-studio/agents).

**We do not bundle that catalog in this repository.** The upstream has
no visible license at the time of writing, and redistributing unlicensed
content is not something we do (Article VII — Attribution requires the
source to be citable, which in turn requires the source to grant
redistribution rights). If upstream adopts a clear permissive license,
the catalog can be imported in a future release.

In the meantime, projects that want those agents can either:

1. Fork the upstream into their own repository and reference it as an
   external tool.
2. Author their own discipline-specific agents under
   `presets/<preset>/agents/<discipline>/` (the StriveX preset, shipped
   via phase 8b of the v0.2 refactor, takes this route — its agents are
   heavily tailored to the StriveX stack and are not generic).
3. Wait for the extensions system (phase 7 of the v0.2 refactor) to
   make third-party catalogs installable via
   `aiadev extension install contains-studio-agents`.

## Stack-specific agents

Stack-specific agents live with their preset. At the time of writing:

- `presets/strivex-stack/agents/` (introduced in phase 8b) will ship
  Django + React Native + Expo agents tailored to the StriveX stack.

## Contributing

See the project's [CONTRIBUTING.md](../CONTRIBUTING.md). Highlights for
agent authors:

- One agent per file; filename matches the first-line declared name.
- Keep agents under 150 lines; anything longer usually means the agent
  is trying to be two agents.
- Document in the frontmatter (or the first paragraph) which skill
  invokes this agent. An agent no skill calls is dead code.
