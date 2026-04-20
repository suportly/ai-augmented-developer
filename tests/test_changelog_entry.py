"""T021 — CHANGELOG records the 0009 terse-mode feature."""

from pathlib import Path

CHANGELOG = Path(__file__).resolve().parents[1] / "CHANGELOG.md"


def test_unreleased_mentions_terse_mode_and_spec_id():
    body = CHANGELOG.read_text(encoding="utf-8")
    unreleased = body.split("## [Unreleased]", 1)[1].split("\n## [", 1)[0]
    lower = unreleased.lower()

    assert "terse-mode" in lower or "terse mode" in lower, (
        "[Unreleased] must mention terse-mode"
    )
    assert "0009" in unreleased, (
        "[Unreleased] must reference spec id 0009 for traceability"
    )
    assert "/aia:help" in unreleased, (
        "[Unreleased] must mention the new /aia:help surface"
    )
    assert "breaking" in lower or "!" in unreleased, (
        "[Unreleased] must flag the /aiadev: → /aia: rename as breaking"
    )
