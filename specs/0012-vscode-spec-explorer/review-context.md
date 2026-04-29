# Code Review Context: 0012 VS Code spec explorer extension

## What Was Built

A new top-level `vscode-extension/` TypeScript VS Code extension that renders an aggregated tree of every `specs/<NNNN-slug>/` directory in the active workspace folders. Each spec expands into its parsed task list with live status icons, a `D / N done` counter, a pipeline-state badge (`spec` → `spec → plan` → `spec → plan → tasks` → `implementing` → `complete`), unresolved `[NEEDS CLARIFICATION:cl-N]` rows, and a `● current` marker on the spec whose `Branch:` matches git HEAD. A debounced `FileSystemWatcher` rebuilds the tree on disk changes (≤ 500 ms). Read-only by contract — no writes, no shell-out, no network, no telemetry. Distributed via the VS Code Marketplace and as a `.vsix` attached to GitHub releases.

## Spec / plan / tasks reference

- Spec: [specs/0012-vscode-spec-explorer/spec.md](./spec.md)
- Plan: [specs/0012-vscode-spec-explorer/plan.md](./plan.md) (v2; amended to record the view-layer test-strategy deviation and the dropped bold-label styling)
- Tasks: [specs/0012-vscode-spec-explorer/tasks.md](./tasks.md) (T001–T028 done, T029 scheduled)
- Drift analysis: [specs/0012-vscode-spec-explorer/analysis.md](./analysis.md)

## Branch

`feature/vscode-spec-explorer` — 30 commits, base = `main`. Linear history, one commit per task plus three docs commits (initial spec/plan, plan-v2 + T029, and the analysis).

## Changed files (54 files, +11,275 lines)

```text
.github/workflows/vscode-extension.yml           (new) CI: lint/typecheck/test/package on push + tag-gated marketplace release
.gitignore                                       (modified) added vscode-extension/node_modules/, out/, *.vsix
README.md                                        (modified) added link to vscode-extension/README.md

specs/0012-vscode-spec-explorer/                 (new feature dir)
  spec.md, plan.md, tasks.md, analysis.md

vscode-extension/                                (new top-level surface)
  package.json                  manifest, scripts, devDeps
  package-lock.json
  tsconfig.json
  esbuild.mjs                   bundle src/extension.ts → out/extension.js (cjs, node20, external vscode)
  .vscodeignore
  .mocharc.json
  .eslintrc.cjs                 no-console, no-explicit-any, no-unused, prefer-const
  README.md
  CHANGELOG.md
  media/aiadev.svg              activity-bar icon
  src/
    extension.ts                wireExtension(host) factory + activate/deactivate/buildRealHost
    parser/types.ts             TaskStatus, SpecStatus, PipelineState, Task, Clarification, SpecModel
    parser/spec.ts              parses bold-key headers; missing-Status sentinel; BOM/CRLF/case tolerance
    parser/tasks.ts             parses ### T### + - **Status:** bullets; unknown fallback
    parser/clarifications.ts    extracts cl-N clarification markers with line numbers
    model/aggregate.ts          buildSpecModels() across workspace folders; rejects abs/.. specsRoot
    model/pipelineState.ts      pure 5-state function
    io/filesystem.ts            FileSystem interface + VsCodeFileSystem
    io/git.ts                   GitHeadProvider interface + VsCodeGitHeadProvider (lazy-cache, swallow errors)
    views/icons.ts              makeStatusIcon(ctors) factory + statusIcon production wrapper
    views/specTreeProvider.ts   TreeDataProvider impl; SpecNode/TaskNode/ClarificationGroup/Clarification/EmptyState
    watcher.ts                  createSpecWatcher(): debounced rebuild
  test/
    support/                    fakeFileSystem, fakeGitHeadProvider, vscodeStub
    fixtures/                   canonical/, missing-status/, bom-crlf/, with-clarifications/, malformed-task-status/
    unit/                       176 tests across parser, model, io, views, watcher, extension, manifest, ci, docs
```

## Key decisions

1. **Top-level `vscode-extension/` directory** rather than a separate repo. Schema drift between the parser and `templates/{spec,tasks}-template.md` is the highest-listed risk; co-location lets a single PR keep them in sync. Trade-off: JS toolchain in a Python-heavy repo, isolated under `vscode-extension/` so Python contributors never need Node.

2. **esbuild over webpack.** ~10× faster, zero config; `tsc --noEmit` runs separately for typecheck.

3. **Provider pattern (Article V) for `vscode.workspace.fs` and `vscode.git`.** `FileSystem` + `GitHeadProvider` interfaces with VS Code-backed adapters; in-memory fakes drive every test. The `GitHeadProvider` indirection is the only Article-III edge case (single production caller); a Complexity-tracking row in plan.md cites Article V as the forcing article.

4. **Stub-injection unit tests for the view layer (plan-v2 amendment).** Plan v1 specified `@vscode/test-electron` integration tests; that toolchain proved fragile in the implementer's environment (xvfb + per-run VS Code download). Switched to factory injection of `TreeItem` / `ThemeIcon` / `EventEmitter` / `Uri` / `Range` constructors so view assertions run in plain Node ≤ 50 ms. The tests still exercise real label/description/tooltip/command shapes. **T029** is scheduled to add a real Extension Host suite on top.

5. **Workspace trust = fully supported.** v1 is read-only Markdown; the parser is fuzzed; no shell-out, no network. Manifest declares `capabilities.untrustedWorkspaces.supported: true`.

6. **Read-only by contract.** Non-goals explicitly forbid editing `tasks.md` Status from the UI and forbid spawning pipeline commands. The grep gate test (`grepGate.spec.ts`) blocks `console.*`, `fetch(`, `https?.request`, `child_process` in `src/` to keep the contract honest.

7. **Branch-highlight via description suffix only.** Plan v1 said "bold + ● current badge"; bold-on-`label` would require `MarkdownString` in `description` (not `label`) or `TreeItemLabel.highlights` (which highlights, not bolds). Neither produces bold-on-label cleanly in the stable API. Plan v2 records the dropped half as an explicit Architecture-decision amendment.

8. **One configuration setting:** `aiadev.specExplorer.specsRoot` (default `"specs"`, scope `resource`). Validated at the aggregator boundary against absolute and `..` path segments.

## Areas needing attention

- **TreeDataProvider event typing.** `onDidChangeTreeData` is exposed as `unknown` from `SpecTreeProvider` because the production constructor is built with stub types. The real-host wiring in `buildRealHost()` casts at the boundary. Reviewer: confirm the cast site is correct and that the real `vscode.window.registerTreeDataProvider` accepts the resulting shape.

- **Lazy `require('vscode')` in `extension.ts` and `views/icons.ts`.** This is the mechanism that keeps unit tests Node-only. Confirm the pattern is acceptable for a VS Code extension and that esbuild's `external: ['vscode']` correctly preserves the runtime require.

- **Path validation in `model/aggregate.ts`.** The `specsRoot` validator rejects absolute paths and `..` segments. Worth checking the regex boundaries.

- **Aggregator `dirname`/`basename` helpers.** Inlined POSIX implementations (the prior reviewer flagged an off-by-one that has been fixed). Worth a second pair of eyes.

- **File-watcher debounce.** Unit tests use a fake clock; real timing under VS Code's event loop is exercised by T029, not yet by this PR. Spec's 500 ms latency budget is a target, not asserted against real disk I/O here.

- **Manifest activationEvents.** Carries `"onView:aiadev.specExplorer"` even though VS Code ≥ 1.74 auto-derives it. Kept verbatim to match the task's exact-key contract; harmless redundancy.

## Test coverage

- **Unit tests:** 176 passing (`cd vscode-extension && npm run test:unit`).
- **Lint:** clean (`npm run lint`).
- **Typecheck:** clean (`npm run typecheck`).
- **Package:** verified locally (`npm run package` produces `aiadev-spec-explorer-0.0.1.vsix`, ~10.6 KB, on Node 20).
- **Integration / Extension Host:** none in this PR — scheduled as T029. Plan v2 records this gap explicitly.

Test categories:
- Parsers (spec, tasks, clarifications) with canonical/missing-status/BOM-CRLF/malformed/with-clarifications fixtures.
- Pipeline state machine (table-driven over all five states + defensive corners).
- Aggregator (multi-folder, sort, specsRoot validation, parseError propagation).
- IO adapters (fakes round-trip + edge cases).
- Tree provider (label, description, tooltip, command bindings, multi-root prefix, branch highlight, pipeline badge for all five states, empty state, clarifications group).
- Watcher (debounce burst-collapse, dispose semantics, default ms).
- Extension wiring (registration, refresh on workspace-folder change + watcher event, error logging, dispose).
- Manifest (every contributed key asserted).
- CI grep gate + release-workflow YAML structural assertions + docs structural assertions.

## Constitution check

| Article | Status | Evidence |
|---|---|---|
| I Spec-first | PASS | spec.md clean, no `[NEEDS CLARIFICATION]`, every scenario maps to ≥ 1 task |
| II Test-first | PASS | red-then-green per task; T009 honestly labelled as a regression-guard |
| III Simplicity | PASS (with declared waiver) | Article-V-forced `GitHeadProvider` recorded in Complexity Tracking |
| IV Evidence over claims | this PR's test plan + transcripts | (relies on PR body) |
| V Provider pattern | PASS | FileSystem + GitHeadProvider; vendor SDK only inside adapters; tests use fakes |
| VI Privacy by design | PASS | grep gate, no telemetry, no network, workspace-trust supported |
| VII Attribution | PASS | no adapted material; CREDITS.md untouched |

## Manual verification done

- Local `npm install`, `npm run lint`, `npm run typecheck`, `npm run test:unit`, `npm run package` all green on Node 20.
- Verified `out/extension.js` builds cleanly, esbuild bundle ≈ 28 KB.
- Did **not** open the extension in a real VS Code window during this branch — that's T029's job.
