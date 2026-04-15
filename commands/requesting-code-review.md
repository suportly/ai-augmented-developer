---
description: Prepare context and dispatch a reviewer subagent before opening a PR.
allowed-tools: Read, Glob, Grep, Bash, Task
argument-hint: ""
---

Invoke the `requesting-code-review` skill. Collate diffs, tests, and plan references, then
dispatch the reviewer subagent. Surface issues back to the author before PR creation.
