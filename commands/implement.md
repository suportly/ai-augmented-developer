---
description: Execute an approved plan + tasks list with subagent-per-task and single review.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Task
argument-hint: "<optional: feature dir under specs/>"
---

Invoke the `implement` skill. One fresh subagent per task in `tasks.md`, one reviewer per
task (conformance, then quality); advance only when it approves.

Feature: $ARGUMENTS
