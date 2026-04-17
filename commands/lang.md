---
description: Swap the Language header in an in-progress feature's spec/plan/tasks.
allowed-tools: Bash
argument-hint: "<bcp-47 code> [--feature <dir>] [--dry-run]"
---

Run `aiadev lang $ARGUMENTS` to rewrite the `**Language:**` header in
`spec.md`, `plan.md`, and `tasks.md` under the active feature directory.
The target feature is inferred from the current git branch slug unless
`--feature <dir>` is passed (e.g. `--feature 0008-llm-tool-integration`).

Only the header is rewritten — existing prose is not translated.
Downstream skills (`plan`, `tasks`, `implement`, `clarify`) read the
header to decide which natural language to continue writing in, so the
next pipeline step produced after this command picks up the new code.
If the user wants existing sections translated, that is a follow-up
edit they (or the agent) must do explicitly.
