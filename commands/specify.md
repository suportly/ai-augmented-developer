---
description: Turn a demand into a numbered spec.md (AI-Augmented Developer pipeline).
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
argument-hint: "<natural-language demand>"
---

Invoke the `specify` skill to transform the user's demand into `specs/<NNNN-slug>/spec.md`
(zero-padded auto-incrementing `NNNN` across `specs/`).
Follow the skill's instructions exactly; do not skip the Constitution Check.

User demand: $ARGUMENTS
