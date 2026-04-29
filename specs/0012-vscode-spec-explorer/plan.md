# Implementation plan: VS Code spec explorer extension

> Produced by the `plan` skill from an approved `spec.md`. This file describes **how** the spec will be realized. Do not rewrite `spec.md` into `plan.md`.

**Branch:** `feature/vscode-spec-explorer`
**Date:** 2026-04-28
**Spec:** [spec.md](./spec.md)
**Plan version:** 2 — amended 2026-04-28 to record the view-layer test-strategy deviation (stub-based unit tests in T015–T025; real Extension Host integration tests deferred to T029).
**Language:** en

---

## Summary

We will ship a single TypeScript VS Code extension under a new top-level `vscode-extension/` directory. It registers an activity-bar view that renders an aggregated tree of every `specs/<NNNN-slug>/` directory in the active workspace folders, with each spec expanding into its parsed `tasks.md` task list (live status icons), unresolved `[NEEDS CLARIFICATION:cl-N …]` rows, and a pipeline-state badge derived from which artifacts (`spec.md` / `plan.md` / `tasks.md`) exist on disk. The render model is rebuilt by a debounced `FileSystemWatcher` listening for `specs/**/{spec,plan,tasks}.md` changes, so save events propagate in < 500 ms with no manual refresh. Read-only by contract — no writes, no shell-out, no network. Distributed via the VS Code Marketplace and as a `.vsix` attached to GitHub releases.

## Technical context

| Field | Value |
|---|---|
| Active preset | None (root framework repo; new top-level surface) |
| Language / runtime | TypeScript 5.x targeting Node 20, compiled to CommonJS for VS Code host |
| Primary dependencies | `@types/vscode ^1.85`, `esbuild` (bundle), `mocha` + `chai` + `ts-node` (unit), `eslint` + `@typescript-eslint/*` (lint), `@vscode/vsce` (package & publish). `@vscode/test-electron` is **deferred** to T029 (see Architecture decisions). |
| Storage | None. In-memory parsed model rebuilt on file events. |
| Testing framework | Mocha + Chai for **all** v1 tests, including the view layer. View tests use stub injection (`test/support/vscodeStub.ts`) of `TreeItem` / `ThemeIcon` / `EventEmitter` / `Uri` / `Range` constructors so the Node-only test runner never loads `vscode`. Real Extension Host tests via `@vscode/test-electron` are scheduled as T029. |
| Target platform(s) | VS Code stable `^1.85` on Linux, macOS, Windows. Cursor/Windsurf best-effort, no CI. |
| Performance budget | Initial render ≤ 1 s for ≤ 50 specs; file-watcher → re-render ≤ 500 ms; parser ≤ 50 ms per spec on a 200-task `tasks.md` |
| Security considerations | `capabilities.untrustedWorkspaces.supported: true` (read-only Markdown only; no `eval`, no child processes, no `fs.write*`). Parser is fuzzed against malformed `tasks.md` to ensure no exception leaks beyond the channel logger. |

## Constitution check

| Article | Applies? | Status | Evidence |
|---|---|---|---|
| I. Spec-first | Yes | PASS | `specs/0012-vscode-spec-explorer/spec.md` contains zero `[NEEDS CLARIFICATION]` markers (verified 2026-04-28); every acceptance scenario will map to at least one task in `tasks.md` (enforced in Phase 2 onward). |
| II. Test-first | Yes | PASS | Each task in `tasks.md` leads with a failing test. Parser/model/IO/watcher tests are pure Mocha; view-layer tests use stub injection (see Testing framework above). Real Extension Host integration tests are scheduled as T029, not deferred indefinitely. No production code lands without an earlier red test commit. |
| III. Simplicity | Yes | PASS | One internal `FileSystem` adapter (sole second caller: the Mocha test fakes); no plug-in architecture, no settings beyond a single `aiadev.specExplorer.specsRoot` override; pipeline-state computation is one pure function over four booleans. |
| IV. Evidence over claims | Yes | PASS | PR test plan will list `npm run test:unit`, `npm run test:integration`, `npm run package`; integration test transcript pasted; UI screenshots of the tree view in three states (empty, populated, mid-task) attached. |
| V. Provider pattern for external systems | Yes | PASS | The only external boundary is VS Code's built-in `vscode.git` extension API (best-effort, optional). It is wrapped in a `GitHeadProvider` interface with a fake used by tests; the vendor API is imported only inside the implementation. No network, LLM, DB, or vendor SDK otherwise. |
| VI. Privacy by design | Yes | PASS | Zero telemetry, zero network calls, zero log lines containing user file paths beyond what the user already sees in the tree. Diagnostic output goes only to a local "aiadev Spec Explorer" Output channel. CI grep gate added for `console.log`, `fetch`, `https.request`, `child_process`. |
| VII. Attribution | Yes | PASS | No code adapted from another project. If we lift any snippet from the VS Code samples repo during implementation, `CREDITS.md` gains an entry referencing `microsoft/vscode-extension-samples` and its MIT license before the relevant commit lands. |

## Architecture decisions

- **Decision:** Place the extension in a new top-level `vscode-extension/` directory inside this monorepo (rather than a separate repo).
  **Rationale:** Schema drift is the #1 listed risk in the spec — keeping the extension in the same repo as `templates/spec-template.md` and `templates/tasks-template.md` lets a single PR update the parser alongside any template change, and lets CI fail loudly if they desync.
  **Trade-offs:** Couples the JS toolchain to the otherwise Python-only repo; mitigated by isolating all `node_modules`, `package.json`, and TS config under `vscode-extension/` so Python contributors never have to install Node.

- **Decision:** Bundle with `esbuild`, not webpack.
  **Rationale:** `vsce` recommends bundling; esbuild is ~10× faster, has zero config, and produces a single CommonJS entry that VS Code loads directly. Webpack adds plugins and config we do not need.
  **Trade-offs:** esbuild does not do type-checking — we run `tsc --noEmit` separately in CI. Acceptable; standard VS Code extension idiom.

- **Decision:** Parsers are pure functions over `string` input that return a typed model; all I/O lives in a thin `FileSystem` and `GitHeadProvider` adapter layer.
  **Rationale:** Article II + III. Pure parsers are unit-testable in Mocha with zero VS Code dependency; integration tests exercise only activation, tree wiring, and the watcher debounce.
  **Trade-offs:** One extra interface (`FileSystem`) when `vscode.workspace.fs` would also work in tests; justified because Article V N/A but Article II demands cheap unit tests.

- **Decision:** A single debounced `FileSystemWatcher` on `**/specs/*/{spec,plan,tasks}.md` rebuilds the model from disk on each event.
  **Rationale:** Simpler than incremental delta tracking; the parser is fast enough (≤ 50 ms × 50 specs = 2.5 s worst case, but in practice we rebuild only the changed spec via path → spec-id map). Debounce window 100 ms collapses bursty save events.
  **Trade-offs:** A pathological monorepo with thousands of specs would not fit; that is out of scope per the spec's success criterion (≤ 50 specs).

- **Decision:** Workspace-trust posture is fully supported (`untrustedWorkspaces.supported: true`) with no limitations.
  **Rationale:** Resolves cl-7 in spec; v1 is read-only Markdown. The threat surface is parser correctness, covered by tests + fuzzing.
  **Trade-offs:** None given the read-only contract. If a future version adds a "run /aiadev:implement" command, that version must downgrade trust support — flagged in the v2 backlog.

- **Decision:** Pipeline-state badge is computed as a pure function `({hasSpec, hasPlan, hasTasks, anyTaskInProgress, allTasksDone}) → 'spec' | 'spec → plan' | 'spec → plan → tasks' | 'implementing' | 'complete'`.
  **Rationale:** All five states from spec Story 4 collapse to one switch statement; no need for a class hierarchy.
  **Trade-offs:** None.

- **Decision (amendment, plan v2):** View-layer tests use stub injection rather than `@vscode/test-electron` for v1.
  **Rationale:** Real Extension Host tests need an `xvfb` display + a per-run VS Code binary download, both of which were unstable in the implementer's subagent environment. The factory-injection pattern lets every view assertion run in plain Node ≤ 50 ms while still exercising the real tree shape, label/description/tooltip wiring, and command bindings.
  **Trade-offs:** Stubs cannot exercise activation under a real Extension Host, real `FileSystemWatcher` event timing on the user's filesystem, or real `vscode.git` API drift. T029 is scheduled to add an integration suite that covers exactly those gaps.

- **Decision (amendment, plan v2):** Branch-highlight in T024 surfaces ` · ● current` as a description suffix; the spec/plan language "bold + ● current badge" is satisfied only on the badge half.
  **Rationale:** VS Code's `TreeItem.label` is a plain string in the stable API; bold styling would require switching to the `TreeItemLabel`-with-`highlights` shape (which only highlights, not bolds) or a `MarkdownString` description (which renders markdown but inside `description`, not `label`). Neither produces the desired bold-on-label result without compromising another field.
  **Trade-offs:** Visual cue is the badge alone, not bold + badge. Documented as a UI polish item; not a Story-4 acceptance failure.

## Project structure changes

```text
vscode-extension/                                    (new)
vscode-extension/package.json                        (new) — manifest, contributes.views, activationEvents
vscode-extension/tsconfig.json                       (new)
vscode-extension/.vscodeignore                       (new)
vscode-extension/README.md                           (new) — Marketplace description
vscode-extension/CHANGELOG.md                        (new)
vscode-extension/esbuild.mjs                         (new)
vscode-extension/src/extension.ts                    (new) — activate/deactivate; wires providers
vscode-extension/src/parser/spec.ts                  (new) — pure spec.md parser
vscode-extension/src/parser/tasks.ts                 (new) — pure tasks.md parser
vscode-extension/src/parser/clarifications.ts        (new) — extracts cl-N markers
vscode-extension/src/parser/types.ts                 (new) — Spec, Task, Status types
vscode-extension/src/model/aggregate.ts              (new) — workspace folder → SpecModel[]
vscode-extension/src/model/pipelineState.ts          (new) — pure state machine
vscode-extension/src/io/filesystem.ts                (new) — FileSystem interface + vscode.workspace.fs impl
vscode-extension/src/io/git.ts                       (new) — GitHeadProvider interface + vscode.git impl
vscode-extension/src/views/specTreeProvider.ts       (new) — TreeDataProvider impl
vscode-extension/src/views/icons.ts                  (new) — status → ThemeIcon mapping
vscode-extension/src/watcher.ts                      (new) — FileSystemWatcher + debounce
vscode-extension/test/unit/parser.spec.ts            (new) — Mocha unit tests
vscode-extension/test/unit/pipelineState.spec.ts     (new)
vscode-extension/test/unit/aggregate.spec.ts         (new)
vscode-extension/test/integration/runTest.ts         (new) — @vscode/test-electron entrypoint
vscode-extension/test/integration/suite/index.ts     (new) — Mocha suite loader
vscode-extension/test/integration/suite/activation.spec.ts        (new)
vscode-extension/test/integration/suite/treeProvider.spec.ts      (new)
vscode-extension/test/integration/suite/watcher.spec.ts           (new)
vscode-extension/test/fixtures/                      (new) — sample specs/ trees per scenario
.github/workflows/vscode-extension.yml               (new) — lint + test + package on PR; publish on tag
CREDITS.md                                           (modified) — entry if any vscode-extension-samples code is reused
.gitignore                                           (modified) — `vscode-extension/node_modules/`, `*.vsix`, `vscode-extension/out/`
README.md                                            (modified) — link to the extension's README
```

## Phase breakdown

### Phase 1 — Bootstrap & toolchain (serial prerequisite)

- Scaffold `vscode-extension/` with `package.json`, `tsconfig.json`, `esbuild.mjs`, `.vscodeignore`.
- Manifest declares: `activationEvents: ["onView:aiadev.specExplorer"]`, single view container in the activity bar, `capabilities.untrustedWorkspaces.supported: true`, no commands beyond an internal `aiadev.specExplorer.refresh`, and a `contributes.configuration` block exposing exactly one setting `aiadev.specExplorer.specsRoot` (default `"specs"`, type `string`, scope `resource`) consumed by `model/aggregate.ts`.
- CI workflow `vscode-extension.yml`: install Node, `npm ci`, `npm run lint`, `npm run typecheck`, `npm run test:unit`, `xvfb-run -a npm run test:integration`, `npm run package` producing `aiadev-spec-explorer-<version>.vsix`.
- `.gitignore` updates.

### Phase 2 — Pure parsers + model (test-first, independent within phase)

Within this phase, parser and model tasks share no files and may proceed in parallel.

- `parser/types.ts` types frozen first.
- `parser/spec.ts` extracts headers + `cl-N` markers; returns the typed sentinel `{ status: 'unknown', parseError: string }` (with a human-readable reason such as `"Missing **Status:** header"`) when the `**Status:**` line is absent or unparseable, instead of throwing. Tested against fixtures including missing `Status:`, BOM, CRLF line endings, mixed-case keys.
- `parser/types.ts` `SpecModel` carries a `workspaceFolderName: string` field so the tree layer can render multi-root prefixes without re-walking workspace state.
- `parser/tasks.ts` extracts every `### T### — title` heading and the `**Status:**` bullet that follows; tested against the `tasks-template.md` placeholder fixture and the live `0011-specify-reconnaissance/tasks.md`.
- `parser/clarifications.ts` extracts `[NEEDS CLARIFICATION:cl-N …]` markers with their line number for "click → reveal".
- `model/aggregate.ts` walks workspace folders, calls parsers via the `FileSystem` interface, returns `SpecModel[]`.
- `model/pipelineState.ts` pure switch over the five-state output.

### Phase 3 — IO adapters

- `io/filesystem.ts` thin wrapper over `vscode.workspace.fs.readFile` + `findFiles`; matching fake under `test/fixtures/`.
- `io/git.ts` wraps the built-in `vscode.git` extension API with try/catch around `getExtension('vscode.git')?.exports.getAPI(1)`; degrades silently when absent.
- No dedicated Phase-3 unit tests: the fake is exercised by Phase 2 model tests; the real adapter wraps VS Code APIs and is exercised end-to-end by the Phase 4–5 integration suite.

### Phase 4 — Tree view + icons (P1 stories 1 + 2)

- `views/icons.ts` maps `pending|in_progress|blocked|done|unknown` to `ThemeIcon` ids (`circle-outline`, `sync~spin`, `error`, `check`, `question`). Exposes a `makeStatusIcon(ctors)` factory for test injection plus a lazy-binding `statusIcon(status)` wrapper for production code (lazy `require('vscode')`).
- `views/specTreeProvider.ts` implements `TreeDataProvider<Node>` with the node kinds `SpecNode | TaskNode | ClarificationGroupNode | ClarificationNode | EmptyStateNode`. The provider takes `TreeItemCtors` and `IconFactories` via constructor injection so unit tests never load `vscode`.
- `SpecNode.label` prepends `[<workspaceFolderName>] ` when `vscode.workspace.workspaceFolders.length > 1`; with a single root no prefix is rendered (resolves spec clarification "Workspace scope").
- `SpecNode.description` carries the pipeline-state badge with optional ` · D / N done` suffix and ` · ● current` when the spec's branch matches HEAD.
- `SpecNode.tooltip` is populated from `SpecModel.parseError` when set; otherwise a 4-line block (`<dirName> · <pipelineState>` / `Status: ...` / `Next: /aiadev:...` / `<specPath>`).
- `extension.ts` registers the provider and the "aiadev Spec Explorer" Output channel.

**View-layer tests (plan-v2 amendment):** Mocha unit tests with stub injection of `TreeItem` / `ThemeIcon` / `EventEmitter` / `Uri` / `Range` constructors via `test/support/vscodeStub.ts`. No `@vscode/test-electron`, no Extension Host. Real Extension Host tests live in T029.

### Phase 5 — File-watcher + live updates (P1 story 2 scenario 2 + P2 story 3)

- `watcher.ts` creates a single `FileSystemWatcher` for `**/specs/*/{spec,plan,tasks}.md`, debounces events at 100 ms (configurable), and emits a single coalesced callback per quiescent window.
- Per the plan-v2 amendment, debounce + dispose semantics are covered by Mocha unit tests using an injected fake clock and fake watcher (`test/unit/watcher.spec.ts`). Real `writeFile`-to-`getChildren` latency is exercised in T029.

### Phase 6 — P2 polish: clarifications group, branch highlight, pipeline badge

- Surface `cl-N` rows with truncated question text (Story 3).
- `git.ts` HEAD lookup feeds `provider.setCurrentBranch(workspaceFolderUri, branch)`; the tree provider appends a ` · ● current` badge to the matching row's description. Bold-on-label was attempted and dropped (see Architecture decision amendment, plan v2).
- Empty-state and `Unknown` status fall-throughs covered by stub-based unit tests; T029 will re-cover them inside a real Extension Host.

### Phase 7 — Distribution

- **Manual prerequisite (outside CI):** an `aiadev` Marketplace publisher account is created and a `VSCE_PAT` secret is stored on the GitHub repo. Phase 7 CI tasks assume both exist; if they do not, the `.vsix` GitHub-release path still works (see risk row 3).
- Marketplace listing copy in `vscode-extension/README.md`.
- GitHub Actions: on tag `vscode-extension-v*`, `vsce publish` to Marketplace and attach the `.vsix` to the GitHub release.
- CHANGELOG.md seeded.

## Risks and mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Schema drift between `templates/*-template.md` and the parser silently desyncs the view | High | High | Phase 2 fixtures include the live template files copied verbatim; CI re-runs parser tests against the template on every commit, failing if anchors or `**Status:**` shape change. A dedicated Mocha test asserts every `<!-- section: ... -->` anchor declared in `templates/spec-template.md` is recognised by `parser/spec.ts`. |
| `vscode.git` extension API differs across forks (Cursor/Windsurf) | Med | Low | `GitHeadProvider` swallows errors and returns `undefined`; branch highlight is silently disabled. No assertion of git state in non-VS-Code-stable hosts. |
| Marketplace publisher account approval delays first release | Low | Med | Phase 7 is sequenced last; the `.vsix` artifact is independently usable from GitHub releases, so users are unblocked even if Marketplace is pending. |
| File-watcher misses an event on network filesystems (NFS, SMB) | Med | Med | Provide a manual `aiadev.specExplorer.refresh` command bound to a refresh icon on the view title bar; integration test covers the explicit-refresh path. |
| Parser exception on malformed user-edited `tasks.md` blanks the entire view | Med | High | Each spec is parsed in isolation inside a try/catch; on failure the row renders with `Unknown` status and a tooltip pointing at the parse error logged to the Output channel. |
| Adding a JS toolchain to this Python-only repo confuses contributors | Med | Low | All Node tooling is confined to `vscode-extension/`; root `CONTRIBUTING.md` (out of scope here) gains a one-line note that the extension is opt-in. |

## Complexity tracking

> No Constitution Check rows are `FAIL`. One Article-III edge case is documented for transparency, citing Article V as the forcing article (allowed by Article III's waiver clause).

| Article waived | Reason | Alternatives considered | Reviewer |
|---|---|---|---|
| III (single-caller indirection) | `GitHeadProvider` interface has only one production implementation today, but Article V requires the vendor API (`vscode.git`) be reached through a project-owned provider so tests can substitute a fake. The interface is therefore Article-V-forced, not speculative. | (a) Call `vscode.git` directly from `aggregate.ts` — rejected: violates Article V and makes branch-highlight untestable without spinning up a real git repo in every integration run. (b) Mock the `vscode.git` SDK in tests — rejected: Article V test rule forbids mocking the SDK. | plan-document-reviewer (2026-04-28) |

## Hand-off to `tasks`

The next skill is `tasks`. It consumes this plan and produces `tasks.md`.
Pre-conditions before hand-off:

- [x] Constitution Check is fully populated, no blank rows.
- [x] Complexity tracking is empty and justified.
- [x] Project structure delta is accurate.
