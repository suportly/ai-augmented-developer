"""T021 — CHANGELOG records the 0009 terse-output feature."""

from pathlib import Path

CHANGELOG = Path(__file__).resolve().parents[1] / "CHANGELOG.md"


def test_0_15_0_section_records_terse_feature():
    body = CHANGELOG.read_text(encoding="utf-8")
    section = body.split("## [0.15.0]", 1)[1].split("\n## [", 1)[0]
    lower = section.lower()

    assert "terse" in lower, (
        "[0.15.0] must mention terse"
    )
    assert "0009" in section, (
        "[0.15.0] must reference spec id 0009 for traceability"
    )
    assert "breaking" in lower or "!" in section, (
        "[0.15.0] must flag the /aiadev: → /aia: rename as breaking"
    )


def test_unreleased_records_0030_with_breaking_note_and_pending_benchmark():
    body = CHANGELOG.read_text(encoding="utf-8")
    section = body.split("## [Unreleased]", 1)[1].split("\n## [", 1)[0]
    assert "0030" in section
    for heading in ("### Added", "### Changed", "### Removed", "### Breaking"):
        assert heading in section, heading
    assert "PENDING" in section
    assert "lean" in section.split("### Breaking", 1)[1]
