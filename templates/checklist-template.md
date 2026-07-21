# Checklist: {{CATEGORY}} — {{FEATURE_NAME}}

> Produced by the `checklist` skill. Run after `plan` and before the PR
> opens. `{{CATEGORY}}` is one of: `security`, `performance`, `accessibility`,
> `internationalization`, `privacy`, `observability`, or a custom category
> registered by a preset.

**Branch:** `{{BRANCH}}`
**Plan:** [plan.md](./plan.md)
**Reviewer:** {{AGENT_OR_PERSON}}
**Date:** {{DATE}}

---

## Scope

<!-- Which parts of the plan this checklist covers. If a part is out of
     scope for this category, say why. -->

## Items

| # | Check | Status | Evidence |
|---|---|---|---|
| 1 | ... | PASS / FAIL / N/A | link or note |
| 2 | ... | PASS / FAIL / N/A | |

<!-- Category-specific defaults follow. Delete the ones that do not apply
     and keep the ones that do. Presets are free to add more. -->

### Security (default items)

- Input validation at every boundary that takes user data.
- Parameterized queries; no string-concatenated SQL.
- Authentication required on every endpoint that returns user data.
- Authorization enforced per user; no cross-user leaks.
- Secrets not logged, not echoed, not in error messages.
- Dependency vulnerability scan is clean or exceptions are documented.

### Performance (default items)

- N+1 query check on each new queryset.
- Pagination on every list endpoint; no unbounded result sets.
- Heavy work off the request cycle (async tasks, background jobs).
- Cold-start impact measured for new dependencies.

### Accessibility (default items)

- Semantic HTML or accessible components.
- Keyboard navigation for all interactive elements.
- Focus-visible states present and not suppressed.
- Contrast ratio meets WCAG AA for text and interactive elements.
- Screen reader labels on icons, inputs, and status indicators.

### Internationalization (default items)

- User-facing strings are marked for translation.
- No hard-coded currency, date, or number formats in UI.
- RTL layouts verified if supported.

### Token economy (default items)

> Lens for context bloat — the tokens the agent reads, not just what a
> reviewer writes. Reviewer-output verbosity is already governed by
> `terse-mode` (spec 0009); this category covers **tool output**. Optional
> external compressors and how to wire them: see
> [`docs/token-economy.md`](../docs/token-economy.md).

- Noisy tool output (test logs, `git status`, build) is not dumped wholesale into context; it is filtered or summarized.
- Long command output is truncated or paginated, not pasted in full — no unbounded logs in context.
- Repeated/near-duplicate output is de-duplicated rather than repeated verbatim.
- Compression opportunities on high-volume commands are identified (and, if a compressor is wired, applied).
- Reviewer output follows `terse-mode` (spec 0009) — this item only references that rule; it does not restate it.

## Failed items

<!-- Copy rows from the table above that are FAIL. For each, describe the
     remediation and the task (or new task id) that will address it. -->

| # | Failed check | Remediation | Owner task |
|---|---|---|---|
| | | | |

## Sign-off

- [ ] All non-N/A items are PASS, or listed in **Failed items** with an owner task.
- [ ] Evidence links resolve (no dead links).
