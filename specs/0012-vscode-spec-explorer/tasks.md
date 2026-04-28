# Tasks: VS Code spec explorer extension

> Produced by the `tasks` skill from an approved `plan.md`. Consumed by `implement`.

**Branch:** `feature/vscode-spec-explorer`
**Plan:** [plan.md](./plan.md)
**Generated:** 2026-04-28
**Language:** en

---

## How to read this file

- Tasks are ordered. `implement` runs them top-to-bottom.
- One task = one commit. The commit message starts with the task id.
- Each task links back to the spec acceptance scenarios it exercises.
- `Status` is one of: `pending`, `in_progress`, `blocked`, `done`. Only `implement` mutates it.

## Task list

### T001 — Scaffold extension package + typecheck + esbuild smoke

- **Status:** done
- **Depends on:** —
- **Files:**
  - create: `vscode-extension/package.json`
  - create: `vscode-extension/tsconfig.json`
  - create: `vscode-extension/esbuild.mjs`
  - create: `vscode-extension/.vscodeignore`
  - create: `vscode-extension/src/extension.ts` (stub `activate`/`deactivate`)
  - test: `vscode-extension/test/unit/bootstrap.spec.ts` (assert `require('../../out/extension.js').activate` is a function)
  - modify: `.gitignore` (add `vscode-extension/node_modules/`, `vscode-extension/out/`, `*.vsix`)
- **Spec scenarios:** prerequisite for every Story 1–4 scenario (no scenario directly).
- **Acceptance:**
  - [ ] Failing test written and observed failing for the stated reason (no `out/extension.js` yet).
  - [ ] `npm install`, `npm run typecheck` (`tsc --noEmit`), `npm run build` (`node esbuild.mjs`), `npm run test:unit` all pass.
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat(vscode-extension): T001 scaffold extension package`.

### T002 — Manifest declares activity-bar view, untrusted-workspace, configuration

- **Status:** done
- **Depends on:** T001
- **Files:**
  - modify: `vscode-extension/package.json` (`contributes.viewsContainers.activitybar`, `contributes.views`, `activationEvents: ["onView:aiadev.specExplorer"]`, `capabilities.untrustedWorkspaces.supported: true`, `contributes.configuration` with `aiadev.specExplorer.specsRoot` default `"specs"`, `contributes.commands` with `aiadev.specExplorer.refresh`)
  - test: `vscode-extension/test/unit/manifest.spec.ts` (parse `package.json`, assert each declared key)
- **Spec scenarios:** prerequisite for every story; encodes cl-7 (workspace trust) and the multi-root configuration knob.
- **Acceptance:**
  - [ ] Failing test written for missing manifest keys; observed red.
  - [ ] Test passes after manifest edit.
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat(vscode-extension): T002 manifest activity-bar view + configuration`.

### T003 — Define core types in `parser/types.ts`

- **Status:** done
- **Depends on:** T001
- **Files:**
  - create: `vscode-extension/src/parser/types.ts` (`TaskStatus`, `Task`, `Clarification`, `SpecModel`, `PipelineState` — `SpecModel` includes `workspaceFolderName: string`, `parseError?: string`, `status: 'draft'|'in review'|'approved'|'implemented'|'pr open'|'unknown'`)
  - test: `vscode-extension/test/unit/types.spec.ts` (compile-time-only test importing each type and asserting tagged-union exhaustiveness via a `never`-check helper)
- **Spec scenarios:** type backbone for Story 1.1, 1.3, multi-root prefix.
- **Acceptance:**
  - [ ] Failing test (red because file does not exist).
  - [ ] Types compile and the exhaustiveness test passes.
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat(vscode-extension): T003 parser type backbone`.

### T004 — `parser/spec.ts` parses bold-key headers

- **Status:** done
- **Depends on:** T003
- **Files:**
  - create: `vscode-extension/src/parser/spec.ts` (pure `parseSpec(source: string): SpecModel`)
  - test: `vscode-extension/test/unit/parser/spec.spec.ts` (fixture asserting `Spec ID`, `Status`, `Branch`, `Language` extracted from a canonical `spec.md` body)
  - test: `vscode-extension/test/fixtures/specs/canonical/spec.md`
- **Spec scenarios:** Story 1 scenario 1.
- **Acceptance:**
  - [ ] Failing test written; observed red.
  - [ ] Minimum implementation makes the test pass.
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat(vscode-extension): T004 parse spec.md bold-key headers`.

### T005 — `parser/spec.ts` returns `{ status: 'unknown', parseError }` on missing Status

- **Status:** done
- **Depends on:** T004
- **Files:**
  - modify: `vscode-extension/src/parser/spec.ts`
  - test: `vscode-extension/test/unit/parser/spec.spec.ts` (add case)
  - test: `vscode-extension/test/fixtures/specs/missing-status/spec.md`
- **Spec scenarios:** Story 1 scenario 3.
- **Acceptance:**
  - [ ] Failing test written; observed red.
  - [ ] Implementation never throws; returns sentinel with human-readable `parseError`.
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat(vscode-extension): T005 spec parser missing-Status sentinel`.

### T006 — `parser/spec.ts` tolerates BOM, CRLF, mixed-case keys

- **Status:** done
- **Depends on:** T004
- **Files:**
  - modify: `vscode-extension/src/parser/spec.ts`
  - test: `vscode-extension/test/unit/parser/spec.spec.ts` (parameterised cases per encoding/casing variant)
  - test: `vscode-extension/test/fixtures/specs/bom-crlf/spec.md` (UTF-8 BOM + CRLF lines)
- **Spec scenarios:** robustness layer behind every Story 1 scenario.
- **Acceptance:**
  - [ ] Failing test written; observed red.
  - [ ] Test passes; existing T004/T005 tests still green.
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat(vscode-extension): T006 spec parser BOM/CRLF/case tolerance`.

### T007 — `parser/clarifications.ts` extracts cl-N markers with line numbers

- **Status:** done
- **Depends on:** T003
- **Files:**
  - create: `vscode-extension/src/parser/clarifications.ts` (pure `extractClarifications(source: string): Clarification[]` returning `{ id: 'cl-N', question, line }`)
  - test: `vscode-extension/test/unit/parser/clarifications.spec.ts`
  - test: `vscode-extension/test/fixtures/specs/with-clarifications/spec.md`
- **Spec scenarios:** Story 3 scenarios 1, 2, 3.
- **Acceptance:**
  - [ ] Failing test written; observed red.
  - [ ] Implementation passes including ordering and line-number accuracy.
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat(vscode-extension): T007 parse cl-N clarification markers`.

### T008 — `parser/tasks.ts` parses `T###` headings + `**Status:**` bullet

- **Status:** done
- **Depends on:** T003
- **Files:**
  - create: `vscode-extension/src/parser/tasks.ts` (pure `parseTasks(source: string): Task[]`)
  - test: `vscode-extension/test/unit/parser/tasks.spec.ts` (uses `templates/tasks-template.md` + `specs/0011-specify-reconnaissance/tasks.md` copied into fixtures)
  - test: `vscode-extension/test/fixtures/specs/canonical/tasks.md`
- **Spec scenarios:** Story 2 scenarios 1, 2, 3.
- **Acceptance:**
  - [ ] Failing test written; observed red.
  - [ ] Parser handles all four valid statuses (`pending|in_progress|blocked|done`) and preserves source-order.
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat(vscode-extension): T008 parse tasks.md T### + Status bullets`.

### T009 — `parser/tasks.ts` falls back to `unknown` on malformed Status

- **Status:** done
- **Depends on:** T008
- **Files:**
  - modify: `vscode-extension/src/parser/tasks.ts`
  - test: `vscode-extension/test/unit/parser/tasks.spec.ts` (case)
  - test: `vscode-extension/test/fixtures/specs/malformed-task-status/tasks.md`
- **Spec scenarios:** robustness behind Story 2 scenario 1.
- **Acceptance:**
  - [ ] Failing test written; observed red.
  - [ ] Parser never throws on malformed status; returns `unknown` for that task only.
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat(vscode-extension): T009 tasks parser unknown-status fallback`.

### T010 — `model/pipelineState.ts` pure 5-state function

- **Status:** done
- **Depends on:** T003
- **Files:**
  - create: `vscode-extension/src/model/pipelineState.ts` (`computePipelineState({hasSpec, hasPlan, hasTasks, anyTaskInProgress, allTasksDone}) -> PipelineState`)
  - test: `vscode-extension/test/unit/model/pipelineState.spec.ts` (table-driven over all branches)
- **Spec scenarios:** Story 4 scenarios 1, 2, 3, 4.
- **Acceptance:**
  - [ ] Failing test written; observed red.
  - [ ] Test passes for all enumerated states.
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat(vscode-extension): T010 pipeline state machine`.

### T011 — `io/filesystem.ts` `FileSystem` interface + fake

- **Status:** done
- **Depends on:** T003
- **Files:**
  - create: `vscode-extension/src/io/filesystem.ts` (`FileSystem` interface; `VsCodeFileSystem` impl wrapping `vscode.workspace.fs` + `findFiles`)
  - create: `vscode-extension/test/support/fakeFileSystem.ts` (in-memory fake)
  - test: `vscode-extension/test/unit/io/fakeFileSystem.spec.ts` (round-trip read/list)
- **Spec scenarios:** infra under all stories.
- **Acceptance:**
  - [ ] Failing test written; observed red.
  - [ ] Fake supports the interface as used by `aggregate.ts`.
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat(vscode-extension): T011 FileSystem interface + fake`.

### T012 — `model/aggregate.ts` walks workspace folders, builds `SpecModel[]`

- **Status:** done
- **Depends on:** T004, T005, T007, T008, T011
- **Files:**
  - create: `vscode-extension/src/model/aggregate.ts` (`buildSpecModels(fs, folders, specsRoot): Promise<SpecModel[]>`)
  - test: `vscode-extension/test/unit/model/aggregate.spec.ts` (uses `FakeFileSystem` + multi-folder fixture)
  - test: `vscode-extension/test/fixtures/workspaces/multi-root/folder-a/specs/0001-alpha/spec.md`
  - test: `vscode-extension/test/fixtures/workspaces/multi-root/folder-b/specs/0001-beta/spec.md`
- **Spec scenarios:** Story 1 scenario 1; multi-root clarification.
- **Acceptance:**
  - [ ] Failing test written; observed red.
  - [ ] `SpecModel[]` carries `workspaceFolderName` for each entry; sorted by `Spec ID` ascending then by folder name.
  - [ ] Honours the `aiadev.specExplorer.specsRoot` setting.
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat(vscode-extension): T012 aggregate spec models across workspace folders`.

### T013 — `io/git.ts` `GitHeadProvider` interface + fake

- **Status:** done
- **Depends on:** T011
- **Files:**
  - create: `vscode-extension/src/io/git.ts` (`GitHeadProvider` interface; `VsCodeGitHeadProvider` impl with try/catch on `getExtension('vscode.git')?.exports.getAPI(1)`)
  - create: `vscode-extension/test/support/fakeGitHeadProvider.ts`
  - test: `vscode-extension/test/unit/io/fakeGitHeadProvider.spec.ts` (returns set HEAD; returns `undefined` when missing)
- **Spec scenarios:** Story 4 / branch-highlight (cl-6) infra.
- **Acceptance:**
  - [ ] Failing test written; observed red.
  - [ ] Real adapter degrades silently when extension absent; fake covers tests.
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat(vscode-extension): T013 GitHeadProvider interface + fake`.

### T014 — `views/icons.ts` status → `ThemeIcon` mapping

- **Status:** done
- **Depends on:** T003
- **Files:**
  - create: `vscode-extension/src/views/icons.ts` (`statusIcon(status: TaskStatus | 'unknown'): ThemeIcon`)
  - test: `vscode-extension/test/unit/views/icons.spec.ts` (asserts each status maps to the spec'd `ThemeIcon` id)
- **Spec scenarios:** Story 2 scenario 1.
- **Acceptance:**
  - [ ] Failing test written; observed red.
  - [ ] Mapping covers `pending|in_progress|blocked|done|unknown` exactly.
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat(vscode-extension): T014 status → ThemeIcon mapping`.

### T015 — `views/specTreeProvider.ts` renders SpecNode rows (label, badge, tooltip)

- **Status:** done

> **Plan deviation:** view tests use stub-based unit tests (factory injection of `TreeItem`/`EventEmitter`) instead of `@vscode/test-electron` integration tests. Real Extension Host integration tests are deferred to T029 (added below).
- **Depends on:** T010, T012, T014
- **Files:**
  - create: `vscode-extension/src/views/specTreeProvider.ts` (`SpecTreeProvider implements TreeDataProvider<Node>`; `SpecNode`/`TaskNode`/`ClarificationGroupNode` shapes)
  - test: `vscode-extension/test/integration/runTest.ts`
  - test: `vscode-extension/test/integration/suite/index.ts`
  - test: `vscode-extension/test/integration/suite/specTreeProvider.spec.ts` (asserts label, description = pipeline badge + `D / N done`, tooltip = `parseError` when set; uses `FakeFileSystem`)
- **Spec scenarios:** Story 1 scenarios 1, 3.
- **Acceptance:**
  - [ ] Failing test written; observed red (run via `xvfb-run -a npm run test:integration` locally).
  - [ ] SpecNode rows match the spec output exactly for the canonical fixture.
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat(vscode-extension): T015 SpecNode rendering`.

### T016 — Empty-state node when no specs found

- **Status:** done
- **Depends on:** T015
- **Files:**
  - modify: `vscode-extension/src/views/specTreeProvider.ts`
  - test: `vscode-extension/test/integration/suite/emptyState.spec.ts`
- **Spec scenarios:** Story 1 scenario 2.
- **Acceptance:**
  - [ ] Failing test written; observed red.
  - [ ] Empty-state row reads "No aiadev specs found in this workspace"; no errors logged.
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat(vscode-extension): T016 empty-state row`.

### T017 — TaskNode children with status icons + parent `D / N done`

- **Status:** done
- **Depends on:** T015
- **Files:**
  - modify: `vscode-extension/src/views/specTreeProvider.ts`
  - test: `vscode-extension/test/integration/suite/taskNodes.spec.ts`
- **Spec scenarios:** Story 2 scenario 1.
- **Acceptance:**
  - [ ] Failing test written; observed red.
  - [ ] Expanding a SpecNode yields N TaskNode rows in source order with correct icons; SpecNode description shows `D / N done`.
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat(vscode-extension): T017 TaskNode rendering + done count`.

### T018 — Click TaskNode reveals heading in `tasks.md`

- **Status:** pending
- **Depends on:** T017
- **Files:**
  - modify: `vscode-extension/src/views/specTreeProvider.ts` (set `command: 'vscode.open'` with selection range derived from parsed line number)
  - test: `vscode-extension/test/integration/suite/taskNavigation.spec.ts`
- **Spec scenarios:** Story 2 scenario 3.
- **Acceptance:**
  - [ ] Failing test written; observed red.
  - [ ] Clicking opens `tasks.md` and the active editor reveals the `### T###` heading at the top of the viewport.
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat(vscode-extension): T018 reveal task heading on click`.

### T019 — `watcher.ts` debounced rebuild (≤ 500 ms)

- **Status:** pending
- **Depends on:** T012, T015
- **Files:**
  - create: `vscode-extension/src/watcher.ts` (`createWatcher(fs, onChange)` — single `FileSystemWatcher` for `**/specs/*/{spec,plan,tasks}.md`, 100 ms debounce, path-keyed rebuild)
  - test: `vscode-extension/test/integration/suite/watcher.spec.ts` (writes `tasks.md`, asserts tree reflects new state within 500 ms)
- **Spec scenarios:** Story 2 scenario 2; Story 3 scenario 3.
- **Acceptance:**
  - [ ] Failing test written; observed red.
  - [ ] Latency assertion holds in CI on Linux.
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat(vscode-extension): T019 debounced file-watcher rebuild`.

### T020 — ClarificationGroupNode (count + truncated text)

- **Status:** pending
- **Depends on:** T015, T007
- **Files:**
  - modify: `vscode-extension/src/views/specTreeProvider.ts`
  - test: `vscode-extension/test/integration/suite/clarifications.spec.ts`
- **Spec scenarios:** Story 3 scenario 1.
- **Acceptance:**
  - [ ] Failing test written; observed red.
  - [ ] Group label reads `Clarifications (N)`; child rows show question text truncated to 80 chars.
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat(vscode-extension): T020 ClarificationGroupNode rendering`.

### T021 — Click cl row opens `spec.md` at marker line

- **Status:** pending
- **Depends on:** T020
- **Files:**
  - modify: `vscode-extension/src/views/specTreeProvider.ts`
  - test: `vscode-extension/test/integration/suite/clarificationNavigation.spec.ts`
- **Spec scenarios:** Story 3 scenario 2.
- **Acceptance:**
  - [ ] Failing test written; observed red.
  - [ ] Active editor cursor lands on the marker line after click.
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat(vscode-extension): T021 reveal cl-N marker on click`.

### T022 — Pipeline-state badge on SpecNode (all five states)

- **Status:** pending
- **Depends on:** T010, T015, T017
- **Files:**
  - modify: `vscode-extension/src/views/specTreeProvider.ts`
  - test: `vscode-extension/test/integration/suite/pipelineBadge.spec.ts` (table over five fixtures: `spec` / `spec → plan` / `spec → plan → tasks` / `implementing` / `complete`)
- **Spec scenarios:** Story 4 scenarios 1, 2, 3, 4.
- **Acceptance:**
  - [ ] Failing test written; observed red.
  - [ ] Each SpecNode renders the correct badge text + tooltip for its fixture.
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat(vscode-extension): T022 pipeline-state badge`.

### T023 — Multi-root folder prefix on SpecNode label

- **Status:** pending
- **Depends on:** T015, T012
- **Files:**
  - modify: `vscode-extension/src/views/specTreeProvider.ts`
  - test: `vscode-extension/test/integration/suite/multiRoot.spec.ts` (two-folder workspace; asserts prefix appears with two roots and disappears when one root remains)
- **Spec scenarios:** Story 1 scenario 1 + multi-root clarification.
- **Acceptance:**
  - [ ] Failing test written; observed red.
  - [ ] `[<folderName>] ` appears iff `workspaceFolders.length > 1`.
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat(vscode-extension): T023 multi-root folder prefix`.

### T024 — Branch-highlight (bold + ● current badge) from GitHeadProvider

- **Status:** pending
- **Depends on:** T013, T015
- **Files:**
  - modify: `vscode-extension/src/views/specTreeProvider.ts`
  - test: `vscode-extension/test/integration/suite/branchHighlight.spec.ts` (uses `FakeGitHeadProvider`; verifies styling and silent fallback when HEAD is `undefined`)
- **Spec scenarios:** branch-awareness clarification (cl-6).
- **Acceptance:**
  - [ ] Failing test written; observed red.
  - [ ] Matching spec is bold + carries `● current` description fragment; non-match unchanged.
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat(vscode-extension): T024 branch-aware highlight`.

### T025 — `extension.ts` activate(): wire provider, watcher, refresh command, output channel

- **Status:** pending
- **Depends on:** T015, T019, T024
- **Files:**
  - modify: `vscode-extension/src/extension.ts`
  - test: `vscode-extension/test/integration/suite/activation.spec.ts` (asserts view registered, command palette has `aiadev.specExplorer.refresh`, output channel exists, no errors with empty workspace)
- **Spec scenarios:** Story 1 scenario 2 + activation backbone for all stories.
- **Acceptance:**
  - [ ] Failing test written; observed red.
  - [ ] All wiring assertions pass.
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat(vscode-extension): T025 activation wiring`.

### T026 — CI workflow: lint, typecheck, unit + integration tests, package vsix

- **Status:** pending
- **Depends on:** T001, T025
- **Files:**
  - create: `.github/workflows/vscode-extension.yml` (Node 20, `npm ci`, `npm run lint`, `npm run typecheck`, `npm run test:unit`, `xvfb-run -a npm run test:integration`, `npm run package`)
  - create: `vscode-extension/.eslintrc.cjs`
  - test: `vscode-extension/test/unit/ci/grepGate.spec.ts` (greps `src/` for `console.log`, `fetch(`, `https.request(`, `child_process` and asserts none in production code)
- **Spec scenarios:** privacy/no-network guarantee (Article VI evidence).
- **Acceptance:**
  - [ ] Failing test written; observed red.
  - [ ] Workflow file passes `actionlint` (run locally if available) and the grep gate passes.
  - [ ] No other existing test regresses.
  - [ ] Commit message: `ci(vscode-extension): T026 lint + test + package + grep gate`.

### T027 — Marketplace publish workflow on tag `vscode-extension-v*`

- **Status:** pending
- **Depends on:** T026
- **Files:**
  - modify: `.github/workflows/vscode-extension.yml` (add `release:` job gated on tag pattern; uses `VSCE_PAT` secret)
  - test: `vscode-extension/test/unit/ci/releaseWorkflow.spec.ts` (parses YAML, asserts tag-pattern + `vsce publish` step + GitHub-release attach step)
- **Spec scenarios:** distribution clarification (cl-2).
- **Acceptance:**
  - [ ] Failing test written; observed red.
  - [ ] YAML parses; required jobs/steps present.
  - [ ] No other existing test regresses.
  - [ ] Commit message: `ci(vscode-extension): T027 marketplace publish on tag`.

### T028 — Extension README, CHANGELOG, root index entry

- **Status:** pending
- **Depends on:** T025
- **Files:**
  - create: `vscode-extension/README.md` (Marketplace listing copy)
  - create: `vscode-extension/CHANGELOG.md` (seeded with `## 0.1.0`)
  - modify: `README.md` (root) — link to `vscode-extension/README.md`
  - test: `vscode-extension/test/unit/docs/markdown.spec.ts` (markdownlint passes on the new files; root README link resolves)
- **Spec scenarios:** discoverability supporting Story 1 scenario 1 (users find the view).
- **Acceptance:**
  - [ ] Failing test written; observed red.
  - [ ] Markdownlint clean; broken-link checker passes.
  - [ ] No other existing test regresses.
  - [ ] Commit message: `docs(vscode-extension): T028 README + CHANGELOG + root index`.

## Parallelization hints

- **Parallel group A — pure parsers and types after T003:** T004, T007, T008 may be attempted in parallel once T003 lands (disjoint files).
- **Parallel group B — IO interfaces:** T011 and T013 (after T003) touch disjoint files.
- **Parallel group C — view enhancements after T015:** T020, T022, T023, T024 each touch `specTreeProvider.ts` and therefore must be **serial** with respect to each other; do not parallelise. T016, T017 also touch `specTreeProvider.ts` — serial.
- Serial: T001 → T002 → T003 → (group A) → T005 → T006 → T009 → T010 → (group B) → T012 → T014 → T015 → T016 → T017 → T018 → T019 → T020 → T021 → T022 → T023 → T024 → T025 → T026 → T027 → T028.

## Post-task checklist

After every task:

- [ ] Commit message references the task id.
- [ ] Status in this file updated.

After all tasks:

- [ ] Full test suite passes (`cd vscode-extension && npm run test:unit && xvfb-run -a npm run test:integration && npm run package`).
- [ ] `analyze` skill runs and reports no drift vs spec / plan.
- [ ] Hand off to `requesting-code-review` to open the PR.
