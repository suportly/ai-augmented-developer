# Slash commands

When you reference an `aiadev` pipeline command in a message to the user
— typically in hand-off lines like "next step: run …" — always use the
**namespaced** form.

## The rule

Use:

- `/aia:specify`
- `/aia:clarify`
- `/aia:plan`
- `/aia:tasks`
- `/aia:implement`
- `/aia:analyze`
- `/aia:checklist`
- `/aia:constitution`
- `/aia:systematic-debugging`
- `/aia:test-driven-development`
- `/aia:frontend-design`
- `/aia:requesting-code-review`
- `/aia:finishing-a-branch`
- `/aia:sync`
- `/aia:lang`

Never use the bare form (`/plan`, `/specify`, …) when talking to the
user. Since v0.2 every command lives under `.claude/commands/aiadev/`
(rendered by Claude Code as `/aia:<name>`); consumer projects never
install the bare variant, so `/plan` would simply not resolve.

## Scope

This applies to **user-facing prose** — anything the user sees in your
reply. It does **not** change:

- How you invoke skills programmatically (use the `Skill` tool with the
  bare skill name, e.g. `Skill(skill="plan")`).
- How skill frontmatter and hand-off sections refer to other skills
  internally (still by bare name — the namespace is a command-layer
  concern, not a skill-layer one).
- Documentation that discusses the framework as a topic rather than
  telling the user to run a command right now.

## Why

The agent's "next step" message is a concrete instruction the user is
meant to execute. Pointing them at `/plan` in an environment where only
`/aia:plan` exists produces a 404 and a confused user. The cost of
typing five extra characters is zero; the cost of a dead command is a
broken hand-off.
