---
description: Decompose an approved plan.md into an ordered tasks.md (one task = one test + one commit).
allowed-tools: Read, Write, Edit, Glob, Grep
argument-hint: "<optional: feature dir under specs/>"
---

Invoke the `tasks` skill against the current feature's `plan.md`. Produce `tasks.md` with
atomic, test-first tasks ready for `implement`.

Feature: $ARGUMENTS
