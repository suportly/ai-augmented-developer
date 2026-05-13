"""Populate the perf_50_specs fixture with 50 minimal spec.md files.

Run from this directory (or any cwd):

    python _generate_perf.py

The generated `specs/` tree is gitignored — only this script and the
README are committed. T002 onwards regenerate the tree on demand so the
detector's perf budget can be measured against a realistic input size.
"""

from __future__ import annotations

from pathlib import Path

SPEC_TEMPLATE = """# Feature specification: perf fixture {index}

**Branch:** `feature/x{index}`
**Created:** 2026-05-13
**Status:** Approved
**Spec ID:** {index}
**Language:** en

---

<!-- section: Problem -->
## Problem

Synthetic perf fixture spec #{index}.

<!-- section: Reconnaissance -->
## Reconnaissance

Reconnaissance: not required (single-surface change: fixtures)

<!-- section: Users and stakeholders -->
## Users and stakeholders

- Pipeline state detector perf tests.

<!-- section: Success criteria -->
## Success criteria

- Detector traverses 50 specs within the documented perf budget.

<!-- section: Non-goals -->
## Non-goals

- Real product behaviour.

<!-- section: User stories -->
## User stories

### Story 1 — Perf load (P1)

As a detector, I want to walk 50 specs quickly.

**Acceptance scenarios**:

1. Given 50 fixture specs, When the detector runs, Then it finishes within the budget.

<!-- section: Clarifications -->
## Clarifications

- None outstanding.

<!-- section: Data touched -->
## Data touched

- None.

<!-- section: Out-of-band effects -->
## Out-of-band effects

- None.

<!-- section: Open risks -->
## Open risks

- None.

<!-- section: Traceability -->
## Traceability

- Originating issue: n/a (fixture)
- Related specs: none
- Constitution articles invoked: II
"""


def main() -> None:
    base = Path(__file__).resolve().parent / "specs"
    base.mkdir(parents=True, exist_ok=True)
    for i in range(1, 51):
        slug_dir = base / f"{i:04d}-x{i}"
        slug_dir.mkdir(parents=True, exist_ok=True)
        (slug_dir / "spec.md").write_text(SPEC_TEMPLATE.format(index=i), encoding="utf-8")
    print(f"Wrote 50 spec.md fixtures under {base}")


if __name__ == "__main__":
    main()
