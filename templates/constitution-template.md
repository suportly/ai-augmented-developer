# Constitution: {{PROJECT_NAME}}

> This file inherits from the framework-level `constitution.md` (in the
> AI-Augmented Developer repository). Articles below either **extend** or
> **restrict** those defaults. You cannot remove or weaken root articles —
> only add new ones or tighten the existing ones.
>
> Version this file alongside the project; every amendment gets a row in
> the project's own `CHANGELOG.md`.

**Version:** 1.0.0
**Adopted:** {{DATE}}
**Last reviewed:** {{DATE}}

---

## Inherited articles (from the framework)

The following articles apply unchanged; see the upstream `constitution.md`
for full text, rationale, and test. Do **not** restate them here.

- Article I — Spec-first
- Article II — Test-first
- Article III — Simplicity
- Article IV — Evidence over claims
- Article V — Provider pattern
- Article VI — Privacy by design
- Article VII — Attribution

## Project-specific articles

> Add articles that are only meaningful for this project or this stack.
> One per section. Each article has **Statement**, **Rationale**, **Test**,
> and **Waivable?**.

### Article P-1 — {{TITLE}}

**Statement.** ...

**Rationale.** ...

**Test.**

- [ ] ...

**Waivable?** Yes / No — with conditions if yes.

<!-- Copy the block above for each additional article. -->

## Tightened framework articles

> Use this section when the framework article is too loose for your context.
> Name the article and specify the stricter rule.

### Tightening of Article II (Test-first)

- In addition to the root rule, this project requires integration tests
  for any new HTTP endpoint and any new Celery task.

## Waivers granted at adoption

> Any waivers that apply project-wide (not per-PR). These are rare — most
> waivers live in a plan's Complexity Tracking table, not here.

| Article | Waiver | Expiry | Reviewer |
|---|---|---|---|
| | | | |

## Amendment process

Follow the framework amendment process in the root `constitution.md` unless
the project has a stricter rule. Record every amendment in this project's
`CHANGELOG.md`.
