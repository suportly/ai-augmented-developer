# `aiadev learn`

`aiadev learn` mines the pipeline's own audit trail for **recurring failure
patterns** and proposes reviewable guidance edits — so lessons the team keeps
re-learning become durable guidance instead of tribal knowledge. It reuses the
same primitives as [`aiadev metrics`](./metrics.md) and is **read-only by
default**, local, and makes no network calls.

Spec: [`specs/0018-aiadev-learn/spec.md`](../specs/0018-aiadev-learn/spec.md).

## What it detects

Deterministic aggregation over `specs/*/.review-log.jsonl` (no ML):

- **Reviewer recurrence** — the same reviewer (`spec-`/`plan-`/`code-reviewer`)
  failing the **first** review pass across multiple features. The trail carries
  no "category" of rejection, so the signal is per reviewer.
- **Task rework** — tasks that needed one or more `CHANGES_REQUESTED` rounds.

A pattern seen in fewer than the evidence threshold (default 2 features) is
reported as **"evidência insuficiente"** rather than asserted — a thin trail
never invents a pattern.

## Usage

```bash
# Ranked text report over the last 90 days (default window).
aiadev learn

# Stable JSON for CI (fixed schema, no execution timestamp).
aiadev learn --format json

# Widen or narrow the aggregation window (mirrors `aiadev metrics`).
aiadev learn --since 2026-01-01

# Include reviewer free-text prose (the `note` field). OFF by default so
# reviewer prose stays out of shareable output (Article VI).
aiadev learn --show-bodies

# Write the proposals to a reviewable artifact.
aiadev learn --write
```

## `--write` and proposals

Each sufficiently-evidenced pattern carries a **proposal**: a starting-point
guidance snippet plus a target file under `rules/`. `--write` renders these to
**`specs/_learnings.md`** — a reviewable artifact, **never** the live guide
files and **never** `constitution.md` (which follows its own amendment
process). Nothing is applied automatically: you accept, edit, or reject each
item and promote it by hand.

## Privacy

The command is local and read-only by default. Reviewer prose lives in the
`note` field and is excluded from output unless you pass `--show-bodies`,
mirroring `aiadev metrics --show-bodies` (Article VI, privacy by design).
