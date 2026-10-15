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


def test_release_0_25_0_records_0030_with_breaking_note_and_benchmark_result():
    body = CHANGELOG.read_text(encoding="utf-8")
    section = body.split("## [0.25.0]", 1)[1].split("\n## [", 1)[0]
    assert "0030" in section
    for heading in ("### Added", "### Changed", "### Removed", "### Breaking"):
        assert heading in section, heading
    assert "benchmark" in section.lower() and "FAILED" in section and "PASSED" in section
    assert "lean" in section.split("### Breaking", 1)[1]


def test_release_0_26_0_records_0031_context_hygiene():
    body = CHANGELOG.read_text(encoding="utf-8")
    section = body.split("## [0.26.0]", 1)[1].split("\n## [", 1)[0]
    assert "### Added" in section and "### Changed" in section
    assert "0031" in section
    for needle in ("context:", "checkpoint:", "AIADEV_CONTEXT_WARN", "doc-review", "implementer"):
        assert needle in section, needle


def test_token_economy_has_context_hygiene_section():
    doc = (CHANGELOG.parent / "docs" / "token-economy.md").read_text(encoding="utf-8")
    assert "## Context hygiene" in doc
    section = doc.split("## Context hygiene", 1)[1].split("\n## ", 1)[0]
    assert "metrics.md" in section
    assert "tasks.md" in section and "AIADEV_CONTEXT_WARN" in section
