# Drift analysis: 0012 VS Code spec explorer

> Produced by the `analyze` skill on 2026-04-28 against
> `feature/vscode-spec-explorer` (29 commits, 176 unit tests passing,
> lint + typecheck clean, `vsce package` produces a 10.6 KB VSIX).
> This file reports gaps; fixes are a separate pass.

## Acceptance scenarios → tasks → commits

| Scenario | Task(s) | Commit(s) | Status |
|---|---|---|---|
| Story 1.1 (sidebar lists specs) | T012, T015 | ee48464, 39697d0 | covered |
| Story 1.2 (empty-state) | T016 | 397db54 | covered |
| Story 1.3 (missing-Status fallback + tooltip) | T005, T015 | 4474c8f, 39697d0 | covered |
| Story 2.1 (TaskNode + D/N done) | T008, T014, T017 | 1ae0d2a, 93988b6, 0ff69b3 | covered |
| Story 2.2 (file-watcher ≤500 ms) | T019 | 7f9ce29 | covered (latency budget asserted at parser layer; real-fs latency not exercised) |
| Story 2.3 (click TaskNode reveals heading) | T018 | 7258af2 | covered |
| Story 3.1 (Clarifications group) | T007, T020 | 0c2fc76, 50bafaa | covered |
| Story 3.2 (click cl-N opens marker line) | T021 | 7e0c939 | covered |
| Story 3.3 (resolved cl disappears on save) | T007 + T019 | 0c2fc76, 7f9ce29 | covered transitively (parser re-extracts; watcher rebuilds) |
| Story 4.1 (`spec` badge) | T010, T022 | b2b626a, 9676aef | covered |
| Story 4.2 (`spec → plan` badge) | T010, T022 | b2b626a, 9676aef | covered |
| Story 4.3 (`implementing` badge) | T010, T022 | b2b626a, 9676aef | covered |
| Story 4.4 (`complete` badge) | T010, T022 | b2b626a, 9676aef | covered |

All 13 spec acceptance scenarios map to at least one task and one commit.

## Plan phases → tasks

| Plan phase | Tasks |
|---|---|
| 1 Bootstrap & toolchain | T001, T002 |
| 2 Pure parsers + model | T003–T010 |
| 3 IO adapters | T011, T013 |
| 4 Tree view + icons | T014–T018 |
| 5 File-watcher + live updates | T019 |
| 6 P2 polish (clarifications, branch, badge, multi-root) | T020–T025 |
| 7 Distribution | T026–T028 |

No plan phase is unreferenced by a task.

## Gaps

### Documented plan deviation: view-layer test strategy

- **Plan said:** Phase 4 tests use `@vscode/test-electron` in a real Extension Host (plan.md "Phase 4 — Tree view + icons", Technical context "Testing framework", Architecture decisions).
- **Code did:** all view-layer tests are unit tests using stub-injected `TreeItem` / `ThemeIcon` / `EventEmitter` / `Uri` / `Range` constructors (`vscode-extension/test/support/vscodeStub.ts`).
- **Why:** environment fragility (xvfb + VS Code binary download per test run) was deemed prohibitive in subagent execution; documented in T015 commit and `tasks.md` T015 note.
- **Drift:** plan.md's "Testing framework" row, Phase 4 description, and the watcher integration-test row in Phase 5 still describe the integration-test approach. They have not been amended.
- **Suggested handler:** `plan` skill, single-row amendment to acknowledge the unit-stub strategy, OR add the deferred integration-test task (next item).

### Promised follow-up task never created

- **What:** the T015 commit and the `tasks.md` T015 note both reference "a follow-up task to layer on real Extension Host integration tests" (and the analysis-time message proposed a `T029`).
- **Reality:** `tasks.md` ends at T028. No T029 exists. No GitHub issue exists.
- **Risk:** the deferred work is not tracked anywhere durable.
- **Suggested handler:** `tasks` skill (append a new task), or open an issue per `git-workflow.md`.

### Plan Architecture decision phrasing vs T024 implementation

- **Plan said** (Architecture decisions, branch-highlight): "bold + a small `● current` badge".
- **Code did:** `● current` text suffix on `description`; label is **not** bolded. T024's implementer flagged this with an inline code comment as "bold-label stretch deferred — VS Code TreeItem labels do not accept arbitrary markdown in v1 API".
- **Drift:** minor — the badge requirement is met; the bold styling is a UI polish gap. Spec body itself (Story 4 / branch-awareness clarification) does not mention bold.
- **Suggested handler:** acknowledge in PR description; defer or add a polish task. No spec change needed.

### Spec → tasks coverage holes (none)

No acceptance scenario is unreferenced by a task. No `[NEEDS CLARIFICATION]` markers remain in `spec.md`.

### Plan → tasks coverage holes (none)

Every numbered phase in `plan.md` has at least one task in `tasks.md`.

### Task → code coverage holes (none)

Every task `T001..T028` is marked `done` in `tasks.md` and has a corresponding commit on the branch (verified via `git log --oneline main..HEAD`).

### Code → task coverage holes (minor, justified)

Files added beyond the strict task list:

- `vscode-extension/.mocharc.json` (T001 commit) — implementer note: makes `mocha` work from any CWD; harmless.
- `vscode-extension/test/support/vscodeStub.ts` (T015 commit) — required by the documented stub-based test strategy.
- `vscode-extension/test/support/fakeFileSystem.ts` (T011 commit) — required by T012 and onward; explicitly listed in T011 task entry.
- `vscode-extension/test/support/fakeGitHeadProvider.ts` (T013 commit) — same.
- `vscode-extension/.eslintrc.cjs` (T026 commit) — required by `npm run lint`; T026 task entry mentions ESLint config implicitly via the `lint` script requirement.

None of these are scope leaks; all justified by their tasks.

## Constitution check (re-run)

| Article | Verdict | Evidence |
|---|---|---|
| I. Spec-first | PASS | `spec.md` clean, no `[NEEDS CLARIFICATION]`, every scenario maps to ≥ 1 task. |
| II. Test-first | PASS | Every commit shows red-then-green transcript in its agent record; the only "regression-guard" task (T009) is honestly labelled. |
| III. Simplicity | PASS (with declared waiver) | One Article-V-forced indirection (`GitHeadProvider`) recorded in plan.md Complexity Tracking. Factory injections (`statusIcon`, `wireExtension`) justified by Article II. |
| IV. Evidence over claims | DEFERRED | Local run is documented in implementer transcripts. PR test plan + screenshots will be authored at `requesting-code-review` time, per workflow. |
| V. Provider pattern | PASS | `FileSystem` and `GitHeadProvider` wrap `vscode.workspace.fs` and `vscode.git` respectively; vendor APIs imported only inside the production adapters; tests use the fakes. |
| VI. Privacy by design | PASS | CI grep gate (`vscode-extension/test/unit/ci/grepGate.spec.ts`) blocks `console.*` / `fetch` / `child_process` in `src/`. Zero network calls. Zero telemetry. Workspace-trust supported (manifest). |
| VII. Attribution | PASS by absence | No code adapted from another project; `CREDITS.md` untouched. |

No article silently slipped to FAIL.

## Summary

- 28/28 tasks done, all committed, lint + typecheck + unit tests green.
- 13/13 spec acceptance scenarios are referenced by at least one task and one commit.
- Two non-blocking gaps **resolved 2026-04-28** by Option B:
  1. **Plan text vs. test strategy** — plan.md amended to v2 (Plan version line, Technical-context dependency + Testing-framework rows, Constitution Article II row, two new Architecture-decision entries, Phase 4 / Phase 5 / Phase 6 narratives).
  2. **T029 added** — `tasks.md` now ends at T029 (real Extension Host integration tests via `@vscode/test-electron`) with explicit files-to-create, acceptance criteria, and CI-step note. Serial chain and Post-task checklist updated.
- One minor UX deviation (T024 branch-highlight uses description suffix only, not bold label) is now an explicit Architecture-decision amendment in plan v2 — no longer a silent gap.

Recommended next step: `requesting-code-review` to prepare the PR. Both prior gaps now have a documented home; T029 ships in a follow-up branch after this PR lands.
