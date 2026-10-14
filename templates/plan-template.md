# Implementation plan: {{FEATURE_NAME}}

> Produced by the `plan` skill: **how** the spec is realized. Do not rewrite `spec.md` here.

**Branch:** `{{BRANCH}}`
**Date:** {{DATE}}
**Spec:** [spec.md](./spec.md)
**Plan version:** 1
**Language:** {{DOC_LANGUAGE}} <!-- mirrors spec.md; write plan prose in this language. -->

---

## Summary

<!-- One paragraph. -->

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

> One row per applicable article; `N/A` allowed. Every `FAIL` needs a **Complexity tracking** row.

| Article | Applies? | Status | Evidence |
|---|---|---|---|
| I. Spec-first | Yes | PASS / FAIL / N/A | `spec.md` approved on YYYY-MM-DD |
| II. Test-first | Yes | PASS / FAIL / N/A | all tasks begin with a failing test |
| III. Simplicity | Yes | PASS / FAIL / N/A | no abstraction without second caller |
| IV. Evidence over claims | Yes | PASS / FAIL / N/A | PR test plan lists commands |
| V. Provider pattern | Yes / No | PASS / FAIL / N/A | see file X |
| VI. Privacy by design | Yes / No | PASS / FAIL / N/A | no sensitive logs; encrypted fields |
| VII. Attribution | Yes / No | PASS / FAIL / N/A | `CREDITS.md` updated or none |
| Preset-specific articles | List | ... | ... |

## Architecture decisions

<!-- ADR-style: Decision / Rationale / Trade-offs. -->

-

## Project structure changes

```text
path/to/new/file.ext         (new)
path/to/modified/file.ext    (modified)
path/to/removed/file.ext     (removed)
```

## Phase breakdown

> Each phase is a checkpoint; order matters across phases, not within.

### Phase 1 — {{PHASE_1_NAME}}

-

### Phase 2 — {{PHASE_2_NAME}}

-

## Risks and mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| {{RISK}} | Low / Med / High | Low / Med / High | {{MITIGATION}} |

## Complexity tracking

> Required when any row is `FAIL`.

| Article waived | Reason | Alternatives considered | Reviewer |
|---|---|---|---|
| | | | |

## Hand-off to `tasks`

Next skill: `tasks`. Before hand-off: Constitution Check fully populated (no blank rows), Complexity tracking filled or justified empty, structure delta accurate.
