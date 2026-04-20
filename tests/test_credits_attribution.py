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
    assert "terse output" in body.lower() or "terse-output" in body.lower(), (
        "credit block must name the adapted concept (terse output contract)"
    )
