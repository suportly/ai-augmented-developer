"""T021 — CHANGELOG records the 0009 terse-mode feature."""

from pathlib import Path

CHANGELOG = Path(__file__).resolve().parents[1] / "CHANGELOG.md"


def test_0_15_0_section_records_terse_mode_feature():
    body = CHANGELOG.read_text(encoding="utf-8")
    section = body.split("## [0.15.0]", 1)[1].split("\n## [", 1)[0]
    lower = section.lower()

    assert "terse-mode" in lower or "terse mode" in lower, (
        "[0.15.0] must mention terse-mode"
    )
    assert "0009" in section, (
        "[0.15.0] must reference spec id 0009 for traceability"
    )
    assert "/aia:help" in section, (
        "[0.15.0] must mention the new /aia:help surface"
    )
    assert "breaking" in lower or "!" in section, (
        "[0.15.0] must flag the /aiadev: → /aia: rename as breaking"
    )
