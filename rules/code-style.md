---
description: Baseline code-style conventions — clarity over cleverness, small units, meaningful names.
alwaysApply: true
---

# Code style

General conventions that apply across every language in the project.
Stack-specific presets may add sharper rules in their own preset
`rules/` directory; those tighten this one and never weaken it.

## Naming

- Identifiers describe intent, not type. `userOrders` beats `userList`,
  `filteredUsers` beats `tmp`.
- Functions are verbs (`fetchOrders`, `recalculate_totals`); classes and
  types are nouns (`Order`, `UserRepository`).
- Boolean names read as predicates: `isReady`, `hasPaid`, `shouldRetry`.
- Avoid one-letter variables outside very tight scopes (loop index,
  math formula, coordinate pair).

## Functions & files

- A function does one thing. If you need the word "and" to describe it,
  split it.
- Keep functions under ~40 lines of real logic. Long functions usually
  hide a missing abstraction or should become a pipeline.
- Files under ~400 lines. Split by responsibility, not by alphabet.
- Avoid deep nesting: guard clauses, early returns, flatten over
  `if/else/else if` trees.

## Comments

- Default: **no comment**. A good name + a small function is clearer.
- Comment only the *why* when it is non-obvious: a workaround for a
  specific bug (link the ticket), a subtle invariant, a decision the
  reader cannot infer from the code.
- Never comment the *what* — that's what the code is for. "Increment
  counter" beside `counter += 1` is noise.
- Remove commented-out code. Git remembers everything.

## Formatting

- Run the project's formatter (Prettier / Black / `cargo fmt`) before
  committing. Never hand-tweak around it.
- One declaration per line. One import per line except when an
  auto-formatter groups them.
- Trailing newlines on every file.

## Forbidden

- `any` in TypeScript, `unknown` without a narrowing step, `# type: ignore`
  without an inline reason.
- Magic numbers and strings. Extract to a named constant if used more
  than once or if the meaning is non-obvious.
- Mutation of function arguments. Return a new value instead.
- Mixing concerns inside a function: a validator that also logs and
  also persists is three functions pretending to be one.
