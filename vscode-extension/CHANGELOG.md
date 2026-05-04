# Changelog

All notable changes to the **aiadev Spec Explorer** extension are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.0.5] - 2026-05-04

### Fixed

- `parser/tasks.ts` now recognises three real-world task formats that previously rendered specs with zero tasks:
  - Loose heading without separator: `### T001 Title` (status defaults to `unknown`).
  - GitHub task-list checkboxes: `- [x] T001 …` → `done`, `- [ ] T001 …` → `pending`. Tolerates `**T001**` and `~~**T001**~~` markup, and strips leading `[P]` / `[US1]` tags from titles.
  - Status table rows: `| T001 | commit | <status> |` accepts the four word values plus emoji shorthand (✅ ✔ ☑ → done; 🚧 🔄 → in_progress; ⛔ 🚫 → blocked; ⏳ ⬜ → pending). Word values may also be wrapped in `**bold**`, `~~strike~~`, or `` `code` `` backticks. Rows that appear before the matching heading are deferred and applied at end-of-parse.

## [0.0.1] - 2026-04-28

Initial public release covering tasks T001–T027 of `specs/0012-vscode-spec-explorer`.

### Added

- Extension scaffolding with TypeScript, esbuild bundling, and a strict tsconfig (T001).
- VS Code manifest declaring the activity-bar view, untrusted-workspace support, and the `aiadev.specExplorer.specsRoot` configuration (T002).
- Core parser types in `parser/types.ts` (T003).
- `parser/spec.ts` with bold-key header parsing, robust `Status:` handling, and BOM / CRLF / mixed-case tolerance (T004–T006).
- `parser/clarifications.ts` extracting `cl-N` markers with line numbers (T007).
- `parser/tasks.ts` parsing `T###` headings and `**Status:**` bullets, falling back to `unknown` on malformed input (T008–T009).
- Pure pipeline-state function in `model/pipelineState.ts` covering all five states (T010).
- `io/filesystem.ts` `FileSystem` interface plus an in-memory fake for tests (T011).
- `model/aggregate.ts` walking workspace folders to build `SpecModel[]` (T012).
- `io/git.ts` `GitHeadProvider` interface and fake (T013).
- `views/icons.ts` mapping statuses to `ThemeIcon`s (T014).
- `views/specTreeProvider.ts` rendering SpecNode rows with label, badge, and tooltip (T015).
- Empty-state node when no specs are found (T016).
- TaskNode children with status icons and a `D / N done` rollup on the parent (T017).
- Click-to-reveal navigation that opens `tasks.md` at the matching heading (T018).
- Debounced (≤ 500 ms) file-system watcher for live rebuilds (T019).
- ClarificationGroupNode with count and truncated text (T020), and click-to-open at the marker line in `spec.md` (T021).
- Pipeline-state badge on SpecNode covering all five states (T022).
- Multi-root workspace folder prefix on SpecNode labels (T023).
- Branch-highlight (bold + current-branch dot) sourced from `GitHeadProvider` (T024).
- `extension.ts` activate() wiring the provider, watcher, refresh command, and output channel (T025).
- CI workflow: lint, typecheck, unit + integration tests, and `.vsix` packaging (T026).
- Marketplace publish workflow on tag `vscode-extension-v*` (T027).
