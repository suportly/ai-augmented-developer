---
name: help
description: Print the pipeline quick-reference — a one-screen summary of every /aia:* command and its hand-offs, prefixed by a state-aware "Próximo passo" line.
version: 0.2.0
inputs: []
outputs:
  - type: text
    description: Optional "Próximo passo:" line followed by the contents of docs/pipeline-reference.md.
requires:
  - docs/pipeline-reference.md
  - src/aiadev/pipeline_state.py
handoffs: []
---

# Help

Return the terse pipeline quick-reference, prefixed by a one-line
recommendation derived from the current workspace state. Plain mode
preserves the legacy verbatim-only output.

**Announce at start:** "Using the help skill. I will print the pipeline quick-reference."

## Mode

The skill has two modes:

- **State-aware (default):** inspect `specs/` via the `pipeline_state`
  module and prepend `Próximo passo: <command> — <reason>` before the
  reference table.
- **Plain (opt-out):** skip the inspection and emit the reference
  byte-for-byte. Triggered by the `--plain` invocation flag OR by the
  environment variable `AIADEV_HELP_PLAIN` set to one of `1`, `true`,
  `yes`, `on` (case-insensitive). Any other value (including `0`,
  `false`, `no`, `off`, or unset) keeps the default state-aware mode.

## Loop

1. **Detect plain mode.** If the invocation carries `--plain`, OR the
   env var `AIADEV_HELP_PLAIN` is truthy (`1`/`true`/`yes`/`on`,
   case-insensitive), skip to step 3.
2. **Compute the recommendation.** Run, from the repository root:

   ```bash
   python -c "from aiadev.pipeline_state import recommend_next_command; from pathlib import Path; import json, subprocess; branch = subprocess.run(['git', 'branch', '--show-current'], capture_output=True, text=True).stdout.strip() or None; print(json.dumps(recommend_next_command(Path.cwd(), branch=branch)))"
   ```

   Parse the JSON `{"command": "...", "reason": "..."}`. When `command`
   is non-null, emit exactly one line as the FIRST line of output:

   ```text
   Próximo passo: <command> — <reason>
   ```

   Then emit a blank line and continue with step 3. When `command` is
   null (plain mode signaled by the module itself), skip the prefix and
   continue with step 3. When the python invocation fails (module not
   importable, git not available), silently fall through to step 3 —
   the verbatim reference is always a safe answer.

3. **Print the reference.** Read the file `docs/pipeline-reference.md`
   from the repository root and return its contents **verbatim**. Do
   not reformat, paraphrase, add commentary, or explain the table — the
   reference is generated and intentionally terse. The transitions for
   "all tasks done" (`/aiadev:requesting-code-review` then
   `/aiadev:finishing-a-branch`) are owned by the recommender, not by
   this skill.
4. If the file does not exist, respond with exactly:
   `pipeline-reference.md missing — run scripts/generate_pipeline_reference.py`
   and stop.

## Rules

- Never edit or summarize `docs/pipeline-reference.md` from inside this
  skill. Content drift is handled by
  `scripts/generate_pipeline_reference.py` and its pre-commit / CI
  hooks.
- The state-aware prefix is at most one paragraph; never replace or
  paraphrase the verbatim reference table.
- Do not invoke any other skill. `help` is a leaf in the pipeline
  graph — calling a Python module via `python -c` is a tooling
  invocation, not a skill invocation.
- Branch scoping uses `git branch --show-current`; orphan specs (no
  matching branch) yield no recommendation and the skill falls back to
  the verbatim reference.

## Hand-off

None. The reader decides what to run next based on the recommendation
line and the table.
