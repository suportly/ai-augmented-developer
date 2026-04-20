"""T007 — pin the shape of off-mode reviewer output (byte-for-byte).

Phase 4 is deferred; the fixtures here are hand-crafted representatives
of what each reviewer emits today. They exist so that any future change to
the verbose output path must land intentionally. When Phase 4 lands, the
benchmark runner overwrites these fixtures with real Sonnet 4.6 transcripts
and the pinned digests below get refreshed by the same commit.
"""

import hashlib
from pathlib import Path

import pytest

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "off_mode"

# Pinned SHA-256 of each fixture at commit time. If the fixture content
# changes — even a single byte — the digest must be recomputed explicitly,
# forcing a reviewer to see and approve the new shape.
PINNED: dict[str, str] = {
    "spec_reviewer_output.md": "ec70d2d2b84dba3d51cc15c67ba2af60ae69e269350626dd7d409fb60055f2a6",
    "plan_reviewer_output.md": "ee18a2f620a60d9a2aa27c10b730baf59095b588366e60c5ea6885d8c9bd5cec",
    "code_reviewer_output.md": "addfa94e26791da07bf9a3bb3f5a6b998769b0333d6ae9a77bc11e3da11244f6",
}


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _expected_digests() -> dict[str, str]:
    """Compute digests live — this module's own source is the golden record.

    We commit the pinned map above as a human-readable fingerprint and
    verify it matches the actual bytes. The test proves that either the
    fixtures or the pinned digests (both tracked, both reviewed) moved
    together, never one without the other.
    """
    return {name: _digest(FIXTURES / name) for name in PINNED}


@pytest.mark.parametrize("fixture_name", sorted(PINNED))
def test_off_mode_fixture_matches_pinned_digest(fixture_name: str):
    actual = _digest(FIXTURES / fixture_name)
    expected = PINNED[fixture_name]
    assert actual == expected, (
        f"{fixture_name} drifted: pinned={expected[:12]}… actual={actual[:12]}… — "
        f"update the PINNED map in this file *and* the fixture together, "
        f"or revert the fixture change"
    )


def test_mutation_of_fixture_body_breaks_digest_check(tmp_path: Path):
    """Same-length content substitution must still trigger the guard."""
    original = (FIXTURES / "spec_reviewer_output.md").read_bytes()
    # Same length, different content — the byte-for-byte guard's real job.
    mutated = original.replace(b"ISSUES_FOUND", b"XXXXXX_FOUND")
    assert mutated != original, "sanity — substitution is observable"
    assert len(mutated) == len(original), "mutation must be same-length"

    mutated_path = tmp_path / "spec_reviewer_output.md"
    mutated_path.write_bytes(mutated)
    assert _digest(mutated_path) != PINNED["spec_reviewer_output.md"], (
        "digest-based guard must detect same-length body substitutions"
    )
