# Changelog

All notable changes to the **aiadev Spec Explorer** extension are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.0.11] - 2026-05-13

### Fixed

- `parser/tasks.ts` now accepts paragraph-style task fields where the `Status`, `Depends on`, `Files`, etc. lines are NOT prefixed by a `- ` list bullet. Real trigger: nzr-kdp specs `032-shop-print-order-lifecycle` (17 tasks) and `034-shop-public-checkout-overhaul` (41 tasks) wrote each task block as `**Status**: done` + `**Depends on**: —` + `**Files**:` (paragraph form, every field on its own line, only the `Files` sub-list using bullets). The previous regex required the leading `- `, so all 58 tasks fell through to `unknown` and rendered as "?" instead of green checks. Canonical `- **Status:** done` keeps working unchanged.

## [0.0.10] - 2026-05-07

### Fixed

- `parser/tasks.ts` now accepts the Status bullet with optional bold around the label and/or value, and tolerates trailing prose after the status word. Real trigger: strivex spec 108 wrote each completed task as `- Status: **done** (commit 7ffb07e9)` (label not bolded, value bolded, trailing commit hash). The previous regex `^- \*\*Status:\*\*\s*(\S+)\s*$` required the canonical `- **Status:** done` shape exactly, so all 108 tasks rendered as `unknown` instead of `done`. Canonical form keeps working unchanged.

## [0.0.9] - 2026-05-06

### Changed

- Spec list in the Spec Explorer tree is now sorted by `specId` **descending** (most recent first) instead of ascending. Specs without a numeric id still sink to the end, alpha by workspace folder. Rationale: active work usually lives on the highest-numbered spec; scrolling to the bottom of the list every time was friction.

## [0.0.8] - 2026-05-06

### Fixed

- `parser/tasks.ts` now accepts status synonyms — `completed`/`complete`/`finished` map to `done`, `todo` to `pending`, `wip`/`in-progress` to `in_progress` — and matches them case-insensitively. Real trigger: maycrm spec 0014 used `Status: completed`, which fell through to `unknown` and rendered tasks as "?" instead of green checks. Canonical vocabulary in `tasks.md` is still `pending | in_progress | blocked | done`; synonyms are a tolerance layer for agent-generated drift.

## [0.0.7] - 2026-05-06

### Fixed

- `parser/tasks.ts` now recognises tasks declared at any heading level from H3 to H6. Previously, `tasks.md` files that grouped tasks under a `### Phase N` header and demoted task headings to `#### T001 — Title` rendered as zero-task specs (real-world example: maycrm spec 0014 with 44 tasks across 6 phases). The matcher relaxes from `^###` to `^#{3,6}`; canonical `### T001` form is unchanged.

## [0.0.6] - 2026-05-04

Test-only re-cut of 0.0.5 — the `vscode-extension-v0.0.5` tag never produced a Marketplace artefact because the integration-test suite had been failing on `main` since 2026-04-30 (`needs: build` blocked the `release` job).

### Fixed

- Integration tests no longer hardcode the extension id `aiadev.aiadev-spec-explorer`. Both `activation.spec.ts` and `treeProvider.spec.ts` now derive `EXTENSION_ID` from `package.json` (new `test/integration/suite/extensionId.ts` helper), so `publisher` renames stay self-consistent without a test edit.

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
