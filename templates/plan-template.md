# Implementation plan: {{FEATURE_NAME}}

> Produced by the `plan` skill from an approved `spec.md`. This file describes **how** the spec will be realized. Do not rewrite `spec.md` into `plan.md`.

**Branch:** `{{BRANCH}}`
**Date:** {{DATE}}
**Spec:** [spec.md](./spec.md)
**Plan version:** 1
**Language:** {{DOC_LANGUAGE}} <!-- mirrors spec.md; write plan prose in this language. -->

---

## Summary

<!-- One paragraph, no more. "We will do X by doing Y, landing in Z files.
     Work is split into N tasks over approximately M hours." -->

## Technical context

| Field | Value |
|---|---|
| Active preset | {{PRESET_NAME}} |
| Language / runtime | {{LANGUAGE}} |
| Primary dependencies | {{DEPS}} |
| Storage | {{STORAGE}} |
| Testing framework | {{TEST_FRAMEWORK}} |
| Target platform(s) | {{TARGETS}} |
| Performance budget | {{PERF_BUDGET_OR_NA}} |
| Security considerations | {{SECURITY_NOTES}} |

## Constitution check

> One row per applicable article from `constitution.md`. `N/A` is allowed
> if the article does not apply to this plan. Every `FAIL` must have a
> corresponding row in **Complexity tracking** below.

| Article | Applies? | Status | Evidence |
|---|---|---|---|
| I. Spec-first | Yes | PASS / FAIL / N/A | `spec.md` approved on YYYY-MM-DD |
| II. Test-first | Yes | PASS / FAIL / N/A | all tasks begin with a failing test |
| III. Simplicity | Yes | PASS / FAIL / N/A | no new abstraction without second caller |
| IV. Evidence over claims | Yes | PASS / FAIL / N/A | PR test plan enumerates commands |
| V. Provider pattern | Yes / No | PASS / FAIL / N/A | see file X |
| VI. Privacy by design | Yes / No | PASS / FAIL / N/A | no new sensitive logs; encrypted fields listed |
| VII. Attribution | Yes / No | PASS / FAIL / N/A | no adapted material, or `CREDITS.md` updated |
| Preset-specific articles | List | ... | ... |

## Architecture decisions

<!-- Short ADR-style notes. Format:
     Decision: <what>
     Rationale: <why this over the alternatives>
     Trade-offs: <what we give up> -->

-

## Project structure changes

```text
<show the directory delta as a diff-style listing>
path/to/new/file.ext         (new)
path/to/modified/file.ext    (modified)
path/to/removed/file.ext     (removed)
```

## Phase breakdown

> Each phase is a checkpoint. Within a phase, tasks are independent enough
> that order does not matter — across phases, order does matter.

### Phase 1 — {{PHASE_1_NAME}}

-

### Phase 2 — {{PHASE_2_NAME}}

-

## Risks and mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| {{RISK}} | Low / Med / High | Low / Med / High | {{MITIGATION}} |

## Complexity tracking

> Required when any Constitution Check row is `FAIL`. Empty table if no waivers.

| Article waived | Reason | Alternatives considered | Reviewer |
|---|---|---|---|
| | | | |

## Hand-off to `tasks`

The next skill is `tasks`. It consumes this plan and produces `tasks.md`.
Pre-conditions before hand-off:

- [ ] Constitution Check is fully populated, no blank rows.
- [ ] Complexity tracking is filled or empty-and-justified.
- [ ] Project structure delta is accurate.
