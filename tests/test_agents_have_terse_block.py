"""T004/T005/T006 — reviewer agents carry a terse-mode output-contract block.

Each reviewer agent body must have a ``## Terse-mode output contract``
section that points at ``schemas/terse-output.schema.json`` and describes
the one-line-per-finding shape.
"""

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_REF = "schemas/terse-output.schema.json"
SECTION_HEADER = "## Terse-mode output contract"


@pytest.mark.parametrize(
    "agent_path",
    [
        "agents/spec-document-reviewer.md",
        # T005 and T006 append their own rows below.
    ],
)
def test_agent_has_terse_block(agent_path: str):
    body = (ROOT / agent_path).read_text(encoding="utf-8")

    assert SECTION_HEADER in body, (
        f"{agent_path} must declare a terse-mode section headed '{SECTION_HEADER}'"
    )
    assert SCHEMA_REF in body, (
        f"{agent_path} terse section must reference {SCHEMA_REF}"
    )
    # One-line-per-finding format cues — the block should mention either
    # the glyphs or the literal "one-line" / "one line per finding" phrase
    # so an implementer cannot accidentally ship an empty header.
    assert "one line per finding" in body.lower() or "one-line per finding" in body.lower(), (
        f"{agent_path} terse section must describe the one-line-per-finding contract"
    )
