# Constitution: rationale and amendment process

Read this when amending `constitution.md`, or when you need the reasoning behind an article. The articles themselves (statement, test, waiver) stay in `constitution.md`.

## Rationale per article

### Article I — Spec-first

**Rationale.** Every recurring failure mode we want to eliminate — wasted implementation work, hidden ambiguity surfacing as bugs, disagreement between humans and agents about what "done" means — starts with code that ran ahead of a spec. The cost of writing a spec is always smaller than the cost of discovering the wrong thing was built.

### Article II — Test-first

**Rationale.** Tests written after implementation are the same code twice — they reproduce bugs the implementation already shipped with. A test that has never been red never proves anything.

### Article III — Simplicity (YAGNI)

**Rationale.** Every abstraction has a maintenance cost paid by every future reader. Three similar inline blocks are cheaper than a wrong abstraction. Premature indirection is the most common form of accidental complexity in this codebase.

### Article IV — Evidence over claims

**Rationale.** Agent-written code amplifies the cost of unverified claims: a confident "all green" that was never observed cascades into users hitting broken flows. The fix is cheap — show the evidence.

### Article V — Provider pattern for external systems

**Rationale.** Vendor lock-in is not the only reason. Provider interfaces give us a single chokepoint for: authentication, retry policy, telemetry, test doubles, and the eventual switch when the vendor raises prices or changes terms.

### Article VI — Privacy by design

**Rationale.** The baseline question is not "did we intend to leak this?" but "can this possibly leak?". Encrypting-by-default, never-log-by-default, and isolate-by-default eliminate whole classes of incident before they happen.

### Article VII — Attribution

**Rationale.** This project itself began as an adaptation of other open-source work (`obra/superpowers`, later `github/spec-kit`, the `contains-studio/agents` catalog). The integrity of that lineage is part of the product.

## Relationship to other artifacts and amendment

- **Presets** may **add** articles for their stack (e.g. a preset's own `constitution.md` requiring stack-specific patterns). They may not **remove** articles from this root constitution.
- **Extensions** may not add constitutional articles. Extensions are additive behavior only; governance changes go through this file.
- **`CLAUDE.md`** and its platform siblings quote this constitution in their preamble so the agent has it in context from turn one.
- Every `plan.md` ships with a **Constitution Check** section that ticks each applicable article or justifies a waiver in its **Complexity Tracking** table.

### Amendment process

1. Open an issue proposing the amendment. State the article affected, the incident or evidence motivating the change, and the blast radius (which existing plans would fail a retroactive check).
2. Submit a PR that edits this file and bumps the version at the top. One article per PR.
3. At least one non-author reviewer approves. Breaking changes (article removal or narrowing of a waiver) require two reviewers and 48 hours of public comment.
4. On merge, append a `Changed` entry to `CHANGELOG.md [Unreleased]` noting the version bump.
