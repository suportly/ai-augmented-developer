"""T012 — root CLAUDE.md points readers at /aia:help."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLAUDE_MD = ROOT / "CLAUDE.md"

POINTER_LINE = (
    "> **Quick reference:** run `/aia:help` for a one-screen summary "
    "of the pipeline commands."
)


def test_claude_md_has_quick_reference_pointer():
    body = CLAUDE_MD.read_text(encoding="utf-8")
    assert POINTER_LINE in body, (
        "root CLAUDE.md must contain the verbatim /aia:help pointer line "
        "somewhere under the 'What lives where' section"
    )


def test_pointer_appears_under_what_lives_where():
    body = CLAUDE_MD.read_text(encoding="utf-8")
    anchor = "## What lives where"
    assert anchor in body
    after_anchor = body.split(anchor, 1)[1]
    # Pointer must appear inside the same section (before the next `## ` heading).
    next_section_idx = after_anchor.find("\n## ")
    section_body = after_anchor if next_section_idx == -1 else after_anchor[:next_section_idx]
    assert POINTER_LINE in section_body, (
        "pointer must live inside the 'What lives where' section, "
        "not in some other part of CLAUDE.md"
    )
