---
description: Investigate the root cause of a bug or test failure before proposing a fix.
allowed-tools: Read, Glob, Grep, Bash
argument-hint: "<symptom or failing test name>"
---

Invoke the `systematic-debugging` skill. Hypothesis → experiment → root cause, in that
order. Do not patch until the cause is identified.

Symptom: $ARGUMENTS
