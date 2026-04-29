# Feature specification: VS Code spec explorer extension

> This file is produced by the `specify` skill. Keep it focused on **what** and **why** — planning and code belong in `plan.md` and `tasks.md`.

**Branch:** `feature/vscode-spec-explorer`
**Created:** 2026-04-28
**Status:** PR Open
**Spec ID:** 0012
**Language:** en

---

<!-- section: Problem -->
## Problem

Developers using the AI-Augmented Developer pipeline have to navigate a deep `specs/<NNNN-slug>/` tree by hand to read `spec.md`, `plan.md`, and `tasks.md`, and they have no at-a-glance view of which tasks in `tasks.md` are still pending. Today the status of a feature lives inside a Markdown bullet (`- **Status:** pending|in_progress|blocked|done`) that the agent mutates as it works; the human supervisor either has to keep `tasks.md` open and re-read it, or trust the agent's narration. Both options are slow and error-prone for repos with many concurrent specs.

<!-- section: Reconnaissance -->
## Reconnaissance

- **specs/ tree (consumer artifact)** — entry: `specs/0011-specify-reconnaissance/tasks.md` · auth: none · integration: file-watching of `specs/*/tasks.md` and `specs/*/spec.md`.
- **tasks.md schema** — entry: `templates/tasks-template.md` · auth: none · integration: parses `### T001 — <title>` headers and `- **Status:** <state>` bullets; values are `pending|in_progress|blocked|done` per the template's "How to read" block.
- **spec.md schema** — entry: `templates/spec-template.md` · auth: none · integration: parses bold-key header lines of the exact form `**<Key>:**\s*<value>` (e.g. `**Status:** Draft`, `**Spec ID:** 0012`, `**Language:** en`, `**Branch:** feature/...`) from the top metadata block, and counts unresolved `[NEEDS CLARIFICATION:cl-N …]` markers anywhere in the body.
- **plan.md schema** — entry: `templates/plan-template.md` · auth: none · integration: read-only; surfaces presence/absence to drive the pipeline-state badge.
- **Validators (parsing reference)** — entry: `scripts/validate_skills.py` · auth: none · integration: not reused as a library, but the section-anchor comments (`<!-- section: ... -->`) it relies on are the contract this extension also parses.

<!-- section: Users and stakeholders -->
## Users and stakeholders

- **Feature supervisor (primary)** — the developer driving an aiadev feature; needs to monitor task progress without leaving the IDE.
- **Reviewer** — a teammate auditing a feature branch; wants to jump to the exact task or clarification that is blocking.
- **Tech lead / framework maintainers** — own the spec/tasks schemas; this extension hard-depends on those anchors staying stable.
- **Consumer-project teams** — install the extension in any repo that has an `specs/` directory produced by the aiadev pipeline.

<!-- section: Success criteria -->
## Success criteria

- A user opens a repo with ≥ 1 spec and sees, in a dedicated VS Code activity-bar view, every spec under `specs/` listed with its `Spec ID`, title, and Status, in under 1 second for any workspace with ≤ 50 specs.
- For any spec, expanding the node reveals each task `T###` from `tasks.md` with its current Status rendered as a colored icon; clicking a task opens `tasks.md` scrolled to that task's heading.
- When `tasks.md` changes on disk (saved by the agent or the user), the view reflects the new Status within 500 ms with no manual refresh.
- The view shows a per-spec progress indicator (`X / Y done`) that updates from the same file-watch event.
- Every unresolved `[NEEDS CLARIFICATION:cl-N …]` marker in `spec.md` is surfaced as a child node under that spec; resolving it in the file makes the node disappear on the next save.
- The extension installs cleanly on VS Code stable ≥ 1.85 and activates without errors when the workspace contains no `specs/` directory (it shows an empty-state message instead of failing).

<!-- section: Non-goals -->
## Non-goals

- Editing `tasks.md` Status fields from the UI. The pipeline rule "only `implement` mutates Status" stays intact in v1.
- Running aiadev pipeline commands (`/aia:plan`, `/aia:implement`, …) from buttons in this extension. v1 is read-only telemetry.
- Replacing or duplicating `aiadev validate`. Schema validation stays a CLI concern; the extension consumes the same anchors but does not enforce them.
- Supporting non-aiadev `specs/` layouts (e.g. arbitrary Markdown trees). The schema is the aiadev template, period.
- Forking the extension for Cursor / Windsurf / other VS Code derivatives in v1. They are best-effort via the same VSIX (see Clarifications: target editors) but receive no CI coverage and no compatibility guarantees.

<!-- section: User stories -->
## User stories

### Story 1 — At-a-glance feature inventory (P1)

As a feature supervisor, I want a sidebar tree of every spec in my repo so that I can see at a glance which features exist and what state each is in, without `cd`-ing through `specs/`.

**Acceptance scenarios:**

1. Given a repo containing `specs/0008-llm-tool-integration/` and `specs/0011-specify-reconnaissance/`, When I open the workspace and click the aiadev activity-bar icon, Then the view lists both specs sorted by `Spec ID` ascending, each row showing `0008 — LLM tool integration · Approved` and `0011 — Specify reconnaissance step · PR Open` derived from the `Status:` header in their `spec.md`.
2. Given a repo with no `specs/` directory, When I open the view, Then I see an empty-state message ("No aiadev specs found in this workspace") and no error in the VS Code output panel.
3. Given a spec whose `spec.md` is missing the `Status:` header, When the view renders that row, Then the row falls back to `Unknown` status (no crash) and a problem is reported in the row's tooltip pointing at the missing header.

### Story 2 — Live task checklist (P1)

As a feature supervisor, I want to expand a spec node and see every `T###` task with a live Status icon so that I can watch the agent's progress without re-reading `tasks.md`.

**Acceptance scenarios:**

1. Given a `tasks.md` listing N tasks (`T001..T00N`) with mixed statuses, When I expand the spec node, Then I see exactly N child rows in source order, each rendered with the icon corresponding to its parsed Status (`done` = green check, `in_progress` = blue spinning circle, `blocked` = red exclamation, `pending` = grey empty circle), and the parent row shows `D / N done` where D is the count of `done` tasks.
2. Given the view is open and I (or the agent) save `tasks.md` after flipping a task from `pending` to `done`, When the file-watcher event fires, Then within 500 ms that task's icon becomes the green check and the parent row's `D / N done` count increments by exactly 1, with no manual refresh.
3. Given I click the `T007` row, When the click is handled, Then VS Code opens `tasks.md` and reveals the `### T007 —` heading at the top of the visible viewport.

### Story 3 — Surface unresolved clarifications (P2)

As a reviewer, I want every `[NEEDS CLARIFICATION:cl-N …]` marker that is still in a spec to appear as its own row, so that I can jump straight to the question that is blocking the feature.

**Acceptance scenarios:**

1. Given `spec.md` contains two markers `cl-1` and `cl-3`, When the view renders the spec node, Then a "Clarifications (2)" group appears under the spec with two children labelled by the marker question text truncated to the first 80 chars.
2. Given I click the `cl-3` row, When the click is handled, Then `spec.md` opens and the cursor lands on the line containing `cl-3`.
3. Given the user resolves `cl-1` (removes the marker and saves), When the file-watcher fires, Then the `cl-1` row disappears within 500 ms and the group label updates to "Clarifications (1)".

### Story 4 — Pipeline state cue (P2)

As a feature supervisor, I want each spec to carry a small badge showing what pipeline artifact already exists (`spec.md`, `plan.md`, `tasks.md`) so that I can tell at a glance whether the next step is `plan`, `tasks`, or `implement`.

**Acceptance scenarios:**

1. Given a spec directory containing only `spec.md`, When the row renders, Then the badge reads `spec` and a tooltip suggests "next: run `/aiadev:plan`".
2. Given a spec directory containing `spec.md` and `plan.md` but no `tasks.md`, When the row renders, Then the badge reads `spec → plan` and the tooltip suggests "next: run `/aiadev:tasks`".
3. Given a spec directory containing all three artifacts and at least one task with `Status: in_progress`, When the row renders, Then the badge reads `implementing` regardless of how many other tasks are still `pending` or `blocked`.
4. Given a spec directory containing all three artifacts where every task has `Status: done`, When the row renders, Then the badge reads `complete` and the tooltip suggests "next: run `/aiadev:analyze` then `/aiadev:requesting-code-review`".

<!-- section: Clarifications -->
## Clarifications

- **Target editors:** VS Code stable (`engines.vscode ^1.85`) is the only supported target and the only host we test against. Cursor and Windsurf are best-effort via the same VSIX — they should work because they implement the VS Code Extension API, but we make no guarantees and do not run CI on them. No proposed APIs.
- **Distribution channel:** Both. The extension is published to the VS Code Marketplace under an `aiadev` publisher (one-click install for the typical user) and the same `.vsix` artifact is attached to each GitHub release of this repo (offline/sideload path for locked-down environments). A single `vsce package` artifact feeds both channels.
- **Workspace scope:** Multi-root. The view aggregates `specs/` from every `vscode.workspace.workspaceFolders` entry. When there are ≥ 2 roots, each spec row is prefixed with its folder name (e.g. `[framework] 0012 — VS Code spec explorer`); with a single root, no prefix is shown.
- **Telemetry:** None. The extension emits zero metrics, makes zero network calls, and reports zero errors off-device. Diagnostics are written only to the user's local VS Code Output panel under a dedicated "aiadev Spec Explorer" channel. Justification: Constitution Article VI (Privacy by design) and YAGNI — opt-in telemetry can be added later if a concrete data question arises.
- **Branch awareness:** Highlight only. All specs are listed; the spec whose `Branch:` header matches the current git HEAD (read from the built-in `vscode.git` extension's `Repository.state.HEAD`) is rendered bold with a `● current` badge. No filtering. If the workspace has no git repository or the git extension is unavailable, the highlight is silently skipped.
- **Workspace trust:** The extension declares `capabilities.untrustedWorkspaces.supported: true` and activates fully in untrusted workspaces. Justification: v1 is strictly read-only Markdown parsing with no code execution, no shell-out, no network I/O. The threat surface is bounded to parser correctness, which is covered by normal tests/fuzzing.

<!-- section: Data touched -->
## Data touched

- **Read-only** parsing of, per workspace folder:
  - `specs/<NNNN-slug>/spec.md` — headers (`Spec ID`, `Status`, `Language`, `Branch`), `[NEEDS CLARIFICATION:cl-N …]` markers.
  - `specs/<NNNN-slug>/plan.md` — existence + path only.
  - `specs/<NNNN-slug>/tasks.md` — `### T### — title` headings and the `- **Status:** <state>` bullet that immediately follows each.
- **No writes** to disk in v1 (see Non-goals).
- **In-memory only:** parsed model {specId, slug, title, status, tasks[], clarifications[]} held per spec; rebuilt on file-watcher event.

<!-- section: Out-of-band effects -->
## Out-of-band effects

None. The extension is local-only, performs no network I/O, runs no child processes, and does not write user files. (Pending confirmation via cl-4 on telemetry.)

<!-- section: Open risks -->
## Open risks

- **Schema drift** — if `templates/tasks-template.md` changes the `**Status:**` bullet shape, the parser silently desyncs. Mitigation discussion belongs in `plan.md`, but the risk is real because the framework is pre-1.0.
- **Performance on large monorepos** — naive globbing of `specs/**/*.md` could be slow on huge repos; budget in success criteria assumes ≤ 50 specs.
- **Editor-API divergence** — Cursor and other VS Code forks may lag behind the engine version we target (cl-1).
- **User confusion vs. CLI source-of-truth** — if the view shows a stale Status because the file watcher missed an event, users may distrust both the extension and the CLI. Reliability of the watcher matters more than feature breadth.
- **VS Code workspace-trust model** — extensions opened in untrusted workspaces face restricted file access. The chosen activation policy (cl-7) directly affects whether the view appears empty or populated for first-time users on a freshly cloned repo.

<!-- section: Traceability -->
## Traceability

- Originating issue: user demand 2026-04-28 ("criar uma extensao para vscode que mostre … os arquivos gerados nas specs … lista de tarefas e se ela esta feita ou nao")
- Related specs: `specs/0011-specify-reconnaissance/spec.md` (tasks/spec schema source of truth), `specs/0010-pipeline-preflight-checks/spec.md` (sibling tooling around the pipeline)
- Constitution articles invoked: I (Spec-first), III (Simplicity / YAGNI — read-only v1), IV (Evidence over claims — UI must match on-disk state), VI (Privacy by design — local-only, no telemetry by default)
