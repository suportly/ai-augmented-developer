"""Root CLAUDE.md points readers at `aiadev next` (spec 0030 cl-1)."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLAUDE_MD = ROOT / "CLAUDE.md"

POINTER_LINE = (
    "> **Quick reference:** run `aiadev next` for the pipeline state "
    "and the next step."
)


def test_claude_md_has_quick_reference_pointer():
    body = CLAUDE_MD.read_text(encoding="utf-8")
    assert POINTER_LINE in body, (
        "root CLAUDE.md must contain the verbatim `aiadev next` pointer line"
    )


def test_pointer_appears_under_what_lives_where():
    body = CLAUDE_MD.read_text(encoding="utf-8")
    anchor = "## What lives where"
    assert anchor in body
    after_anchor = body.split(anchor, 1)[1]
    next_section_idx = after_anchor.find("\n## ")
    section_body = after_anchor if next_section_idx == -1 else after_anchor[:next_section_idx]
    assert POINTER_LINE in section_body, (
        "pointer must live inside the 'What lives where' section"
    )
