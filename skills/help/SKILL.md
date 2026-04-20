---
name: help
description: Print the pipeline quick-reference — a one-screen summary of every /aia:* command and its hand-offs.
version: 0.1.0
inputs: []
outputs:
  - type: text
    description: Contents of docs/pipeline-reference.md.
requires:
  - docs/pipeline-reference.md
handoffs: []
---

# Help

Return the terse pipeline quick-reference. Nothing else.

**Announce at start:** "Using the help skill. I will print the pipeline quick-reference."

## Loop

1. Read the file `docs/pipeline-reference.md` from the repository root.
2. Return its contents **verbatim** as your response. Do not reformat, paraphrase, add commentary, or explain the table — the reference is generated and intentionally terse.
3. If the file does not exist, respond with exactly: `pipeline-reference.md missing — run scripts/generate_pipeline_reference.py` and stop.

## Rules

- Never edit or summarize `docs/pipeline-reference.md` from inside this skill. Content drift is handled by `scripts/generate_pipeline_reference.py` and its pre-commit / CI hooks.
- Do not invoke any other skill. `help` is a leaf in the pipeline graph.

## Hand-off

None. The reader decides what to run next based on the table.
