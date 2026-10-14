"""T001 — verify CREDITS.md attributes juliusbrussee/caveman per Article VII."""

from pathlib import Path

CREDITS = Path(__file__).resolve().parents[1] / "CREDITS.md"


def test_credits_names_juliusbrussee_caveman_with_url_and_license():
    body = CREDITS.read_text(encoding="utf-8")
    assert "juliusbrussee/caveman" in body.lower() or "JuliusBrussee/caveman" in body, (
        "CREDITS.md must name the caveman repo (Article VII)"
    )
    assert "https://github.com/JuliusBrussee/caveman" in body, (
        "CREDITS.md must link to the caveman repo"
    )
    assert "license" in body.lower(), (
        "caveman credit block must mention the upstream license"
    )
    assert "0030" in body, "credit block must note the removal in spec 0030"


def test_credits_records_spec_kit_mechanisms_adapted_in_0030():
    body = CREDITS.read_text(encoding="utf-8")
    section = body.split("### [github/spec-kit]", 1)[1].split("\n### ", 1)[0]
    assert "0030" in section
    lower = section.lower()
    for term in ("preflight", "scenario-to-task", "ceiling", "checklist gate"):
        assert term in lower, f"spec-kit credit must mention {term!r}"
