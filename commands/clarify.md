---
description: Resolve [NEEDS CLARIFICATION] markers in spec.md or plan.md, one at a time.
allowed-tools: Read, Edit, Grep, Glob
argument-hint: "<optional: spec or plan path>"
---

Invoke the `clarify` skill. Walk the current feature's `spec.md` (or `plan.md` when specified)
and surface each `[NEEDS CLARIFICATION]` marker to the user, editing the file with their answers.

Target: $ARGUMENTS
