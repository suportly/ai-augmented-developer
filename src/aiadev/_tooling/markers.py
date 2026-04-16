"""cl-N marker generation, parsing, and enumeration."""
from __future__ import annotations

import re
from typing import Any

_CL_N_RE = re.compile(r"\[NEEDS CLARIFICATION:cl-([1-9][0-9]*)\s+([^\]]+)\]")
_LEGACY_RE = re.compile(r"\[NEEDS CLARIFICATION:\s+([^\]]+)\]")
_ANY_MARKER_RE = re.compile(r"\[NEEDS CLARIFICATION:[^\]]*\]")


def next_id(text: str) -> int:
    """Return the next monotonic cl-N id for *text* (max existing + 1, or 1)."""
    ids = [int(m.group(1)) for m in _CL_N_RE.finditer(text)]
    return max(ids, default=0) + 1


def enumerate_markers(text: str) -> list[dict[str, Any]]:
    """List all NEEDS CLARIFICATION markers with their id and question.

    Modern markers (``cl-N``) get ``id = "cl-N"``; legacy markers get
    ``id = None``.
    """
    result: list[dict[str, Any]] = []
    for m in _ANY_MARKER_RE.finditer(text):
        token = m.group(0)
        cl_match = _CL_N_RE.fullmatch(token)
        if cl_match:
            result.append({
                "id": f"cl-{cl_match.group(1)}",
                "question": cl_match.group(2),
            })
        else:
            legacy_match = _LEGACY_RE.fullmatch(token)
            question = legacy_match.group(1) if legacy_match else token
            result.append({"id": None, "question": question})
    return result


def needs_renumbering(text: str) -> bool:
    """True if *text* contains any legacy marker (no cl-N id)."""
    markers = enumerate_markers(text)
    return any(m["id"] is None for m in markers)
