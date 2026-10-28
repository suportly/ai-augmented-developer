"""T005 (spec 0032, success criterion #1): CHANGELOG and README mention find-skills."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_unreleased_records_0032_find_skills():
    body = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    section = body.split("## [Unreleased]", 1)[1].split("\n## [", 1)[0]
    assert "0032" in section and "find-skills" in section
    for needle in ("every preset", "never installs", "ceiling"):
        assert needle in section, needle


def test_readme_lists_find_skills_next_to_the_other_skills():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "- **find-skills** —" in readme
