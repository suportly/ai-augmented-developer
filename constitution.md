# Constitution

This document governs how the AI-Augmented Developer framework is built and how projects using it should expect it to behave. It is also the default constitution copied into new projects via `aiadev init` — projects can then edit, add, or waive articles for their own context.

Changes to this file follow the process in `CONTRIBUTING.md`. Amendments require an issue, an RFC-style PR, and at least one reviewer who is not the author.

**Version:** 1.0.0 — cf. [CHANGELOG.md](./CHANGELOG.md).

---

## Article I — Spec-first

**Statement.** No code is written without an approved `spec.md`. Specifications describe **what** and **why**; plans and code describe **how**.

**Rationale.** Every recurring failure mode we want to eliminate — wasted implementation work, hidden ambiguity surfacing as bugs, disagreement between humans and agents about what "done" means — starts with code that ran ahead of a spec. The cost of writing a spec is always smaller than the cost of discovering the wrong thing was built.

**Test.** For any branch producing code that affects behavior:

- [ ] `specs/<branch>/spec.md` exists.
- [ ] It contains zero `[NEEDS CLARIFICATION]` markers.
- [ ] Every `spec.md` acceptance scenario maps to at least one task in `tasks.md`.

**Waivable?** Yes, for:

- Typo fixes, formatting, comment edits, documentation-only changes.
- Reverts of previously-merged changes (the revert's motivation goes in the commit message).
- Emergency fixes explicitly labelled `hotfix:` in the commit prefix; a retrospective `spec.md` must be filed within 72 hours.

---

## Article II — Test-first

**Statement.** For any change that alters behavior, a failing test is written before the implementation. The test must fail for the right reason before production code is added.

**Rationale.** Tests written after implementation are the same code twice — they reproduce bugs the implementation already shipped with. A test that has never been red never proves anything.

**Test.** For each task in `tasks.md`:

- [ ] The commit introducing the test is earlier (in history) than the commit that makes it pass.
- [ ] The test was observed failing on the task author's machine before the implementation commit.
- [ ] The test exercises an acceptance scenario in `spec.md`.

**Waivable?** Yes, for:

- Research spikes explicitly marked `@spike` in the branch name and deleted before merge.
- Exploratory prototypes in `experiments/` that never ship to users.
- Generated code (migrations, codegen output) where the generator itself is tested.

Waivers must be documented in the PR body under `Complexity Tracking`.

---

## Article III — Simplicity (YAGNI)

**Statement.** Build only what the current spec requires. No speculative generalization, no abstraction for hypothetical future callers, no options nobody asked for.

**Rationale.** Every abstraction has a maintenance cost paid by every future reader. Three similar inline blocks are cheaper than a wrong abstraction. Premature indirection is the most common form of accidental complexity in this codebase.

**Test.** For each plan or PR:

- [ ] No new class, interface, protocol, or indirection layer without a second caller that needs it **today**.
- [ ] No new configuration flag without a named user of the non-default value.
- [ ] No new dependency without a rejected alternative documented.

**Waivable?** Yes, when another article forces the abstraction (e.g. Article V requires a provider interface around an external service even if there is only one provider today). The waiver cites the forcing article.

---

## Article IV — Evidence over claims

**Statement.** "Done" means verified. A claim that tests pass, a build works, or a feature behaves correctly is backed by a transcript, log, or command the reader can re-run — not by the author's memory.

**Rationale.** Agent-written code amplifies the cost of unverified claims: a confident "all green" that was never observed cascades into users hitting broken flows. The fix is cheap — show the evidence.

**Test.** For each PR:

- [ ] The test plan in the PR body lists the exact commands run (not "ran the tests").
- [ ] At least one command's output (pass/fail summary) is pasted or linked.
- [ ] For UI changes, a screenshot or recording is attached.
- [ ] Any "worked locally" claim names the OS, language version, and relevant environment.

**Waivable?** No. Evidence is non-negotiable, because the alternative is trust without verification.

---

## Article V — Provider pattern for external systems

**Statement.** Any external dependency with a network boundary (LLM API, database, object storage, email, push notifications, payment, feature flag service) is accessed through a provider interface defined inside the project, not through the vendor SDK directly.

**Rationale.** Vendor lock-in is not the only reason. Provider interfaces give us a single chokepoint for: authentication, retry policy, telemetry, test doubles, and the eventual switch when the vendor raises prices or changes terms.

**Test.** For each plan that introduces or modifies an external integration:

- [ ] A provider interface lives in the project (`<app>/providers/<name>.py` or equivalent).
- [ ] The vendor SDK is imported only inside the provider implementation.
- [ ] Tests use a fake provider, not a mocked SDK.

**Waivable?** Yes, for one-off scripts under `scripts/` that never run in production. Not waivable for anything invoked by user-facing code.

---

## Article VI — Privacy by design

**Statement.** Sensitive data is encrypted at rest, never logged in plaintext, and segregated per user at every layer from storage to API response.

**Rationale.** The baseline question is not "did we intend to leak this?" but "can this possibly leak?". Encrypting-by-default, never-log-by-default, and isolate-by-default eliminate whole classes of incident before they happen.

**Test.** For each PR:

- [ ] No new log line contains credentials, tokens, PII, or message bodies (verified by grep in CI).
- [ ] Any new model field containing secrets uses the project's encrypted field type (e.g. `EncryptedTextField`).
- [ ] Any new queryset that returns data from multiple users is gated by an explicit permission check.

**Waivable?** No for production code paths. Yes for test fixtures with clearly fake data (`user@example.com`).

---

## Article VII — Attribution

**Statement.** When material (skills, templates, agent definitions, prompts) is adapted from another project, the source is named in `CREDITS.md` with a link and license notice. Forks without attribution erode the ecosystem we depend on.

**Rationale.** This project itself began as an adaptation of other open-source work (`obra/superpowers`, later `github/spec-kit`, the `contains-studio/agents` catalog). The integrity of that lineage is part of the product.

**Test.** For each PR that adds content derived from another project:

- [ ] `CREDITS.md` has an entry with the source repo, the specific material, and the license.
- [ ] If the source license requires it, the original notice is preserved alongside the adapted file.

**Waivable?** No.

---

## Relationship to other artifacts

- **Presets** may **add** articles for their stack (e.g. `presets/django-drf-react/constitution.md` can require API-first, async-first, and Docker-native patterns). They may not **remove** articles from this root constitution.
- **Extensions** may not add constitutional articles. Extensions are additive behavior only; governance changes go through this file.
- **`CLAUDE.md`** and its platform siblings quote this constitution in their preamble so the agent has it in context from turn one.
- Every `plan.md` ships with a **Constitution Check** section that ticks each applicable article or justifies a waiver in its **Complexity Tracking** table.

## Amendment process

1. Open an issue proposing the amendment. State the article affected, the incident or evidence motivating the change, and the blast radius (which existing plans would fail a retroactive check).
2. Submit a PR that edits this file and bumps the version at the top. One article per PR.
3. At least one non-author reviewer approves. Breaking changes (article removal or narrowing of a waiver) require two reviewers and 48 hours of public comment.
4. On merge, append a `Changed` entry to `CHANGELOG.md [Unreleased]` noting the version bump.
