# Agent Skills interoperability

In December 2025 the Agent Skills spec ([agentskills.io](https://agentskills.io),
governed by the Agentic AI Foundation) became an open standard adopted
by Claude Code, Codex CLI, Cursor, Gemini CLI, Copilot, and other
tools — exactly the platforms `aiadev sync` already supports. This
page documents the four changes that align the framework with that
standard: the `metadata.aiadev` namespace, dual frontmatter
validation, conditional rule loading via `paths:`, the `AGENTS.md`
canonical agent file, and generated plugin manifests.

Spec: [`specs/0016-agent-skills-interop/spec.md`](../specs/0016-agent-skills-interop/spec.md).

## 1. The `metadata.aiadev` namespace

Before this feature, every `SKILL.md` frontmatter carried five
proprietary pipeline fields — `version`, `inputs`, `outputs`,
`requires`, `handoffs` — at the top level. Tools that validate
frontmatter against the open Agent Skills standard reject or silently
ignore unknown top-level fields, so those five fields now nest under a
single namespaced key:

```yaml
---
name: implement
description: Dispatches one fresh subagent per task with a two-stage review.
metadata:
  aiadev:
    version: "1.4.0"
    requires:
      - tasks.md
    handoffs:
      - analyze
      - requesting-code-review
---
```

Top level now contains only fields the open standard defines —
`name`, `description`, `license`, `compatibility`, `metadata`,
`allowed-tools` — plus two documented Claude Code runtime extensions
that intentionally stay at the top level: `disable-model-invocation`
and `argument-hint` (see [cl-7](#why-two-fields-stay-at-the-top-level)
below).

### Migration

- **New skills**: write `metadata.aiadev` directly; the old top-level
  shape is a hard validation error (no warning period — the framework
  is pre-1.0 and the spec's cl-5 decision favors a clean cut backed by
  automatic migration).
- **Already-installed skills in a consumer project**: run `aiadev
  sync`. The sync engine detects the legacy top-level shape and
  rewrites it into `metadata.aiadev` automatically — no manual editing
  required.

### Why two fields stay at the top level

Verifying the published spec and its reference validator (`skills-ref`)
during implementation surfaced that `disable-model-invocation` and
`argument-hint` are runtime extensions Claude Code reads from the top
level of the frontmatter — moving them under `metadata` would silently
break the runtime behavior they control (e.g.
`disable-model-invocation: true` guards several deploy skills from
accidental model invocation). The vendored schema
(`schemas/agent-skills.schema.json`) documents this as a deliberate,
recorded deviation in its `$comment` field rather than a silent
divergence from the standard.

## 2. Dual validation

`aiadev validate` (and its CI invocation) now checks every `SKILL.md`
frontmatter against **two** schemas:

1. **`schemas/agent-skills.schema.json`** — a vendorized snapshot of
   the open Agent Skills standard's conformance schema (snapshot dated
   2025-12-18, re-verified against the published spec and the
   `skills-ref` reference validator on 2026-07-08). This is the
   external conformance check: no unknown top-level field, `name`
   matching the containing directory, `description` present, and so
   on.
2. **`schemas/skill-frontmatter.schema.json`** — the internal schema
   that additionally validates the shape of whatever lives under
   `metadata.aiadev` (that `handoffs` is a list of strings, that
   `version` is semver, etc).

Both schemas run with the same error severity as before this feature —
nothing that used to be a validation error became a warning.

### Example error

Each error line is prefixed with its origin — `[agent-skills]` for the
vendored open-standard schema, `[aiadev]` for the internal schema — so
the author knows which contract was violated. A skill with a
`handoffs` value that isn't a list of strings still fails, and the
message points at the relocated field (jsonschema renders the nesting
as a slash-joined path):

```text
$ aiadev validate skills/bad-handoffs/SKILL.md
FAIL skills/bad-handoffs/SKILL.md: [aiadev] metadata/aiadev/handoffs: 'requesting-review' is not of type 'array'
1 skill(s) failed validation; 0 passed.
```

A skill written in the **old** top-level format (regression
protection) fails with a compound message on one line:

```text
$ aiadev validate skills/old-format/SKILL.md
FAIL skills/old-format/SKILL.md: [agent-skills] <root>: Additional properties are not allowed ('requires' was unexpected); [aiadev] requires: proprietary pipeline field at top level — move it to metadata.aiadev.requires (see spec 0016); [aiadev] <root>: Additional properties are not allowed ('requires' was unexpected)
1 skill(s) failed validation; 0 passed.
```

The compound message has three semicolon-separated parts: the raw
rejection from the vendored open-standard schema, a didactic `[aiadev]`
line naming the offending field and the exact destination
(`metadata.aiadev.requires`) with a pointer to spec 0016, and the raw
rejection from the internal schema — which also refuses the field at
the top level, so the two schemas never disagree about legacy shapes.

## 3. Conditional rule loading via `paths:`

Some platforms (Claude Code among them) now support loading a rule
only when files matching a glob are touched, instead of always
loading it into context. Rule frontmatter may declare an optional
`paths:` key to opt into that behavior:

```yaml
---
description: Test-first workflow, naming, and structure baseline for every stack.
paths:
  - "tests/**"
  - "**/*.test.*"
  - "**/*_test.*"
  - "conftest.py"
---
```

The first (and, as of this release, only) rule to declare `paths:` is
`rules/testing.md` (cl-6 — a deliberately minimal first wave). Every
other rule stays global; adding `paths:` to more rules is a follow-up
content change, not a mechanism change.

### Per-platform propagation

| Platform | Behavior when the rule has `paths:` | Behavior when it doesn't |
| --- | --- | --- |
| Claude Code | `.claude/rules/<name>.md` keeps the frontmatter's `paths:` key intact; no `alwaysApply: true` is added. | Installed exactly as before (always loaded). |
| Cursor | `paths:` is translated into the native `.cursor/rules/<name>.mdc` `globs` field (comma-joined). | Installed exactly as before — `.mdc` with no `globs`. |
| Codex, OpenCode, Gemini | `paths:` is stripped; the rule installs in the platform's current format (always loaded) — no error or false warning. | Installed exactly as before. |

Rules without `paths:` are byte-for-byte unaffected on every platform
— the feature is strictly opt-in per rule.

## 4. `AGENTS.md` as the canonical agent file

`AGENTS.md` has become the cross-tool convention for agent guidance
(60k+ repos on GitHub use it), and Claude Code itself now reads it
natively. `aiadev sync` treats `AGENTS.md` as the single canonical
agent file for a consumer project; `CLAUDE.md` and `GEMINI.md` become
thin wrappers that point at it instead of duplicating generated
content.

### Canonical layout

```text
your-project/
├── AGENTS.md        # canonical — full generated content + preserved manual sections
├── CLAUDE.md         # thin wrapper (~3 lines) pointing at AGENTS.md
└── GEMINI.md          # thin wrapper (~3 lines) pointing at AGENTS.md
```

Every managed block — including the `<!-- aiadev:auto-stack -->` stack
detection block introduced for `aiadev sync` — is generated into
`AGENTS.md` and **only** `AGENTS.md`. Cursor, Codex, and OpenCode read
the same physical `AGENTS.md`; there is nothing left for them to
diverge on.

### Legacy migration

Consumer projects that already had a `CLAUDE.md` or `GEMINI.md` with
manual, hand-written content (team conventions, project notes, etc.)
before this feature keep that content — it is not discarded. When
`aiadev sync` detects a legacy agent file with content outside the
previously-managed blocks, it:

1. Writes a `.bak` copy of the legacy file next to the original,
   preserving the pre-migration state for inspection or rollback.
2. Extracts the manual content and merges it into `AGENTS.md`'s own
   managed migration block, so it survives the transition to the
   canonical file instead of being silently dropped.
3. Rewrites `CLAUDE.md`/`GEMINI.md` as the thin wrapper pointing at
   `AGENTS.md`.

Re-running `aiadev sync` after the migration has already happened is a
no-op on the migrated content — only genuinely new manual edits to the
legacy files (if any are made after migration) would be picked up
again.

## 5. Generated and CI-verified plugin manifests

Three plugin manifest files in this repo — `.claude-plugin/plugin.json`,
`.claude-plugin/marketplace.json`, and `.cursor-plugin/plugin.json` —
used to be hand-maintained and had drifted from the `VERSION` file
(they said `1.0.0` while the framework had already reached `0.20.0`).
They are now derived from `VERSION` + `pyproject.toml` +
`presets/catalog.json`, and verified in CI.

```bash
# Read-only: fails naming the file and the two diverging values
# when a manifest has drifted from the derivation. This is the
# default mode.
aiadev manifests
aiadev manifests --check

# Regenerate all three manifests in place. Idempotent — running
# it twice in a row (or --check right after) reports no changes.
aiadev manifests --write
```

Every preset marked `stable` in `presets/catalog.json` gets a
corresponding plugin entry in `marketplace.json` automatically —
adding a new stable preset to the catalog produces its plugin entry
with zero manifest edits. Presets marked `beta` or `experimental` are
omitted from the marketplace listing until promoted to `stable`.

CI enforces this with the `manifests` job in
[`.github/workflows/validate.yml`](../.github/workflows/validate.yml),
which runs `aiadev manifests --check` on every push — no future
release should ship with a manifest as stale as the one this feature
fixed.

## See also

- [`CREDITS.md`](../CREDITS.md) — attribution for the Agent Skills
  open standard.
- [`CHANGELOG.md`](../CHANGELOG.md) — the `[Unreleased]` entry for
  this feature.
- [`schemas/agent-skills.schema.json`](../schemas/agent-skills.schema.json) —
  the vendored conformance schema, including the `$comment` recording
  the deliberate deviations.
- [`schemas/skill-frontmatter.schema.json`](../schemas/skill-frontmatter.schema.json) —
  the internal schema validating `metadata.aiadev`.
