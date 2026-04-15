---
description: Execute an approved plan + tasks list with subagent-per-task and two-stage review.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Task
argument-hint: "<optional: feature dir under specs/>"
---

Invoke the `implement` skill. Dispatch one fresh subagent per task in `tasks.md`, apply
spec-compliance review then code-quality review, and move on only when both pass.

Feature: $ARGUMENTS
