---
description: Detect drift between spec.md, plan.md, tasks.md, and the actual code.
allowed-tools: Read, Glob, Grep, Bash
argument-hint: "<optional: feature dir under specs/>"
---

Invoke the `analyze` skill. Produce a drift report; do NOT fix the gaps — surface them so
the user can decide scope.

Feature: $ARGUMENTS
