# Customization

The AI-Augmented Developer framework supports per-team and per-user
configuration overrides on top of the base settings shipped with each
skill. This page describes the layer precedence, merge rules, and
file locations consumers need to know to extend the framework without
forking it.

The resolver lives in [`src/aiadev/customization.py`](../src/aiadev/customization.py)
and is exercised by [`tests/test_customization.py`](../tests/test_customization.py)
plus the fixtures under [`tests/fixtures/customization/`](../tests/fixtures/customization/).

## Layer precedence

Three TOML layers are merged in this fixed order. The rightmost layer
wins on every conflict.

1. **Base** — shipped by the skill itself (the file the skill author
   wrote). Treated as read-only by the resolver.
2. **Team** — `_aiadev/team.toml`, committed at the project root.
   Created as an empty stub by `aiadev install`. Use it for
   conventions the whole team must agree on.
3. **User** — `_aiadev/user.toml`, gitignored at the project root.
   Reserved for personal preferences (preferred model, debug toggles)
   that should not leak into the shared repo.

The precedence is therefore `user > team > base`. A missing team or
user layer is treated as an empty mapping; nothing else changes.

The resolver is pure: inputs are never mutated, and `copy.deepcopy`
is used for any value the result borrows from a layer. Calling
`merge_layers` twice with the same inputs always returns equal — and
independent — results.

## Merge rules

The resolver in [`src/aiadev/customization.py`](../src/aiadev/customization.py)
(`merge_layers`) honors three shape-specific rules plus a uniform
error-handling contract.

### Scalars

A scalar value (string, number, boolean) at any key is replaced by
the rightmost layer that provides it. Last writer wins, with no
attempt to interpret the value.

```toml
# base.toml
default_model = "sonnet"

# team.toml
default_model = "opus"

# user.toml
default_model = "haiku"
```

Merged result: `default_model = "haiku"`.

### Tables

A nested table (TOML `[section]`) is deep-merged. Keys present only
in an override are added; keys present in both are recursively merged
using the same rules (tables stay tables, scalars get replaced,
arrays-of-tables follow the rule below).

A table override never wholesale-clears the base table — to remove a
key, the resolver expects the base to omit it. Setting the key to
`""`, `0`, or `false` only replaces the scalar.

### Arrays of tables

An array of tables (TOML `[[section]]`) is matched by either the
`code` or the `id` field, in that order. The matcher picks the first
key name that appears in **both** sides; if neither key is present on
both sides, the override list wholesale-replaces the base list (this
is the safe escape hatch for arrays whose entries have no stable
identity).

When a match key is detected:

- Override entries with the same `code`/`id` REPLACE the
  corresponding base entry **in place** (the position in the merged
  list follows the base). The replacement is itself a recursive
  deep-merge, so partial overrides preserve untouched fields.
- New entries (those whose key is not in the base) are APPENDED to
  the end, in the order they appear in the override.

This rule lets a team override a single menu entry without having to
re-list the others, and lets a user append a personal entry without
disturbing the team's curated order.

### Errors

A parse error in any TOML layer aborts the resolver with a clear
diagnostic. `load_layer` wraps `tomllib.TOMLDecodeError` as
`ValueError` annotated with `<filename>:<line> — <reason>` so the
offending file and line stay visible to the caller. The resolver
never silently falls back to base; the failure is surfaced and the
process is expected to halt.

Example diagnostic:

```text
team.toml:3 — Unclosed inline table (at line 3, column 1)
```

The original `tomllib` message is preserved verbatim so substring
checks downstream (e.g. "table") keep working.

## Examples

The three examples below mirror the fixtures under
[`tests/fixtures/customization/`](../tests/fixtures/customization/),
so the merged result for each one is the value the public API
actually returns.

### Example 1 — override scalar `default_model`

A skill ships with a default model; the team standardizes on `opus`
for cost reasons, then a single developer drops down to `haiku` while
debugging locally.

```toml
# base.toml — shipped by skill
default_model = "sonnet"
```

```toml
# _aiadev/team.toml — committed
default_model = "opus"
```

```toml
# _aiadev/user.toml — gitignored
default_model = "haiku"
```

Merged result:

```toml
default_model = "haiku"
```

The user layer wins because precedence is `user > team > base`.
Removing `_aiadev/user.toml` would yield `"opus"`; removing both
would yield `"sonnet"`.

### Example 2 — override skill menu by `code`

A skill ships with two menu entries (`A`, `B`). The team rewrites the
description of `B` and adds `C`; a single developer adds `D` for
themselves.

```toml
# base.toml — shipped by skill
[[skill.menu]]
code = "A"
description = "first"

[[skill.menu]]
code = "B"
description = "second"
```

```toml
# _aiadev/team.toml — committed
[[skill.menu]]
code = "B"
description = "second-overridden-by-team"

[[skill.menu]]
code = "C"
description = "appended-by-team"
```

```toml
# _aiadev/user.toml — gitignored
[[skill.menu]]
code = "D"
description = "appended-by-user"
```

Merged result:

```toml
[[skill.menu]]
code = "A"
description = "first"

[[skill.menu]]
code = "B"
description = "second-overridden-by-team"

[[skill.menu]]
code = "C"
description = "appended-by-team"

[[skill.menu]]
code = "D"
description = "appended-by-user"
```

`A` is untouched, `B` is replaced in place (position is preserved),
`C` and `D` are appended in the order they were declared by their
respective layers.

### Example 3 — override agent `principles[]` by `id`

A subagent ships with two principles (`p1`, `p2`). The team tightens
the wording of `p2` and adds `p3`; a developer adds a personal `p4`.
Arrays of tables in the `principles` slot are matched by `id`
because the entries do not carry a `code` field.

```toml
# base.toml — shipped by skill
[[agent.principles]]
id = "p1"
text = "Prefer evidence over claims"

[[agent.principles]]
id = "p2"
text = "Test before implementation"
```

```toml
# _aiadev/team.toml — committed
[[agent.principles]]
id = "p2"
text = "Test before implementation; the test must fail first"

[[agent.principles]]
id = "p3"
text = "Cite the spec section in every PR"
```

```toml
# _aiadev/user.toml — gitignored
[[agent.principles]]
id = "p4"
text = "Always reproduce the bug locally before fixing"
```

Merged result:

```toml
[[agent.principles]]
id = "p1"
text = "Prefer evidence over claims"

[[agent.principles]]
id = "p2"
text = "Test before implementation; the test must fail first"

[[agent.principles]]
id = "p3"
text = "Cite the spec section in every PR"

[[agent.principles]]
id = "p4"
text = "Always reproduce the bug locally before fixing"
```

`p1` is untouched, `p2` is replaced in place, and `p3` / `p4` are
appended. The same machinery that handles `skill.menu` (matched by
`code`) handles `agent.principles` (matched by `id`) — the resolver
auto-detects which key name to use.

## File locations

- **Project root:** `_aiadev/team.toml` (committed) and
  `_aiadev/user.toml` (gitignored — `aiadev install` adds the
  `.gitignore` entry so the personal layer never leaks into the
  shared repo).
- **Skill defaults:** each shipped skill carries its own base TOML
  next to its `SKILL.md`. The skill author owns the schema; the
  consumer overrides it.
- **Diagnostics:** parse errors are reported as
  `<filename>:<line> — <reason>` (see Merge rules → Errors).

The resolver does not look anywhere else. There is no global
`~/.aiadev/user.toml` and no environment-variable layer — the three
files above are the entire surface.

## Cross-references

- Spec: [`specs/0014-bmad-inspired-evolutions/spec.md`](../specs/0014-bmad-inspired-evolutions/spec.md) — Story 2.
- Plan: [`specs/0014-bmad-inspired-evolutions/plan.md`](../specs/0014-bmad-inspired-evolutions/plan.md) — ADR-2 pins the public API and the match-key list.
- Implementation: [`src/aiadev/customization.py`](../src/aiadev/customization.py).
- Tests and fixtures: [`tests/test_customization.py`](../tests/test_customization.py) and [`tests/fixtures/customization/`](../tests/fixtures/customization/).
