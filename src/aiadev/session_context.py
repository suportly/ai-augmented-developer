"""Context size of the last request, read from the tail of a transcript (spec 0031).

Privacy (Art. VI): each line is parsed, but only ``type``, ``message.id``,
``message.role`` and the three token counters of ``message.usage`` are kept.
Message text and ``tool_result`` bodies are never stored, returned or logged.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_WINDOWS = (256 * 1024, 1024 * 1024, 4 * 1024 * 1024)
_MAX_TOKENS = 2**63 - 1  # same bound as token_metrics._int
_FIELDS = ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")


def _int(value: Any) -> int:
    if isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= _MAX_TOKENS:
        return value
    return 0


def _usage_of(raw: bytes) -> tuple[str | None, tuple[int, int, int]] | None:
    """Return ``(message id, counters)`` for an assistant usage line, else None."""
    try:
        obj = json.loads(raw)
    except ValueError:
        return None
    if not isinstance(obj, dict) or obj.get("type") != "assistant":
        return None
    message = obj.get("message")
    if not isinstance(message, dict) or message.get("role") == "user":
        return None
    usage = message.get("usage")
    if not isinstance(usage, dict):
        return None
    mid = message.get("id")
    counters = (_int(usage.get(_FIELDS[0])), _int(usage.get(_FIELDS[1])), _int(usage.get(_FIELDS[2])))
    return (mid if isinstance(mid, str) else None), counters


def _scan(data: bytes, discard_first: bool) -> int | None:
    lines = data.split(b"\n")
    if discard_first:
        lines = lines[1:]
    last_id: str | None = None
    current: tuple[int, int, int] | None = None
    for raw in lines:
        parsed = _usage_of(raw) if raw.strip() else None
        if parsed is None:
            continue
        mid, counters = parsed
        if current is not None and mid is not None and mid == last_id:
            current = (
                max(current[0], counters[0]),
                max(current[1], counters[1]),
                max(current[2], counters[2]),
            )
        else:
            current = counters
        last_id = mid
    return None if current is None else sum(current)


def last_context(path: Path) -> int | None:
    """Context (input + cache creation + cache read) of the last request with usage.

    Reads a window from the end of the file (256 KiB, then 1 MiB, then 4 MiB while
    no usage line is found). Returns None when none is found or the file is unreadable.
    """
    try:
        with path.open("rb") as fh:
            size = fh.seek(0, 2)
            for window in _WINDOWS:
                length = min(size, window)
                offset = size - length
                fh.seek(max(offset - 1, 0))
                data = fh.read(length + (1 if offset > 0 else 0))
                discard = False
                if offset > 0:
                    # The extra leading byte tells whether the window starts on a line
                    # boundary: only a cut line is dropped.
                    discard = data[:1] != b"\n"
                    data = data[1:]
                found = _scan(data, discard_first=discard)
                if found is not None:
                    return found
                if offset == 0:
                    return None
    except OSError:
        return None
    return None
