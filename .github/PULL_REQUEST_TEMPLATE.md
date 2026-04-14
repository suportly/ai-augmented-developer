<!-- One concern per PR. If this description grows past a few paragraphs,
     consider splitting the PR. -->

## Summary

<!-- What is this PR doing, and why? One paragraph. Link the issue. -->

Closes #

## Constitution check

<!-- Tick each applicable article. Every FAIL needs a row in the
     Complexity tracking section below. See constitution.md. -->

- [ ] I. Spec-first — `specs/<branch>/spec.md` exists and is approved, OR this is a waivable change (typo / formatting / revert / hotfix).
- [ ] II. Test-first — failing test committed before the implementation commit, OR this is a documented waiver.
- [ ] III. Simplicity — no new abstraction without a second caller today; no new flag without a named user of the non-default value.
- [ ] IV. Evidence over claims — test plan below enumerates the commands run.
- [ ] V. Provider pattern — external dependencies accessed through a provider interface, OR N/A.
- [ ] VI. Privacy by design — no new plaintext logging of secrets / PII; encrypted fields used for new sensitive data.
- [ ] VII. Attribution — `CREDITS.md` updated if material was adapted.

## Complexity tracking (waivers)

<!-- Leave empty if no article is FAIL. Otherwise one row per waiver. -->

| Article waived | Reason | Alternatives considered | Reviewer |
|---|---|---|---|
| | | | |

## Test plan

<!-- Exact commands run locally and their outcome. One bullet per command.
     Screenshots/recordings welcome for UI changes. -->

- [ ] `python3 scripts/validate_skills.py` — result: …
- [ ] `npx markdownlint-cli2 '**/*.md'` — result: …
- [ ] <project-specific test commands>

## Related skills / templates / artifacts

<!-- If this PR touches a skill, link the produced or consumed artifacts
     (spec.md, plan.md, tasks.md). If it adds a new skill or template,
     say which pipeline stage it slots into. -->

-

## Notes for the reviewer

<!-- Anything that is not obvious from the diff: tricky decisions,
     alternatives rejected, follow-up work deferred to another PR. -->
