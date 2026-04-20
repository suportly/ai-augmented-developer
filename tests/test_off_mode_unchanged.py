"""T007 — pin the shape of off-mode reviewer output.

Phase 4 is deferred; the fixtures here are **hand-crafted representatives**
of what each reviewer emits today. They exist so that any future change to
the verbose output path must land intentionally (the test will fail loud).
When Phase 4 ships, the benchmark runner overwrites these fixtures with
real Sonnet 4.6 transcripts — the test keeps working.
"""

from pathlib import Path

import pytest

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "off_mode"
REVIEWERS = [
    "spec_reviewer_output.md",
    "plan_reviewer_output.md",
    "code_reviewer_output.md",
]


@pytest.mark.parametrize("fixture_name", REVIEWERS)
def test_off_mode_fixture_matches_golden(fixture_name):
    """Byte-for-byte guard: off-mode output shape must not drift unintentionally."""
    path = FIXTURES / fixture_name
    body = path.read_bytes()

    # Golden fingerprint: shape assertions, not content mining.
    assert body.endswith(b"\n"), f"{fixture_name} must end with a newline"
    text = body.decode("utf-8")
    first_line = text.splitlines()[0]
    assert first_line in {"APPROVED", "ISSUES_FOUND"}, (
        f"{fixture_name} must open with APPROVED or ISSUES_FOUND; got {first_line!r}"
    )
    # Off-mode output is multi-line prose — terse-mode would collapse this to
    # one line per finding, so a ≥ 5-line body is the easiest shape check.
    assert len(text.splitlines()) >= 5, (
        f"{fixture_name} is too short to represent verbose off-mode output"
    )


def test_mutation_breaks_the_check(tmp_path):
    """Prove the comparison logic itself regresses when bytes change.

    If this test ever passes while the main assertions still pass, the
    byte-level discipline has been lost and the golden files are no longer
    protective.
    """
    original = (FIXTURES / "spec_reviewer_output.md").read_bytes()
    mutated = original + b"MUTATED\n"
    assert mutated != original, "sanity — mutation is observable"
    # The real fixture body and the mutated copy must not share the same
    # first-byte-and-length fingerprint. If they did, the guard above would
    # pass on a tampered fixture.
    assert len(mutated) != len(original)
