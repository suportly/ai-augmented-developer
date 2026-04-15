---
description: Turn an approved spec.md into a plan.md that passes the Constitution Check.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
argument-hint: "<optional: feature dir under specs/>"
---

Invoke the `plan` skill. Produce `plan.md` (plus research / data-model / contracts when the
skill requires them) from the current feature's approved `spec.md`.

Feature: $ARGUMENTS
