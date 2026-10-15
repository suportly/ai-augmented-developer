"""Context size of the last request, read from the tail of a transcript (spec 0031).

Privacy (Art. VI): each line is parsed, but only ``type``, ``message.id``,
``message.role`` and the three token counters of ``message.usage`` are kept.
Message text and ``tool_result`` bodies are never stored, returned or logged.
"""

from __future__ import annotations

import dataclasses
import json
import os
import time
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from aiadev.token_metrics import default_transcripts_dir

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
    except (ValueError, RecursionError):  # deeply nested line: unreadable, skip it
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
    model = message.get("model")
    if (isinstance(model, str) and model.startswith("<")) or not any(counters):
        return None  # synthetic / zero-usage line (e.g. written after an interrupt): not a real request
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


ACTIVE_WINDOW_SECONDS = 600
DEFAULT_WARN = 150_000
WARN_ENV = "AIADEV_CONTEXT_WARN"


@dataclasses.dataclass(frozen=True)
class SessionContext:
    session_id: str
    tokens: int
    age_seconds: int


def active_contexts(
    workspace: Path, now: float | None = None, home: Path | None = None
) -> list[SessionContext]:
    """Most recent session plus every one modified within the last 600 s (inclusive)."""
    moment = time.time() if now is None else now
    directory = default_transcripts_dir(workspace, home)
    entries: list[tuple[float, Path]] = []
    try:
        for path in directory.glob("*.jsonl"):
            try:
                if path.is_file():
                    entries.append((path.stat().st_mtime, path))
            except OSError:
                continue
    except OSError:
        return []
    entries.sort(key=lambda e: e[0], reverse=True)
    result: list[SessionContext] = []
    for index, (mtime, path) in enumerate(entries):
        age = max(0, int(moment - mtime))
        if index > 0 and moment - mtime > ACTIVE_WINDOW_SECONDS:
            break
        tokens = last_context(path)
        if tokens is not None:
            result.append(SessionContext(path.stem, tokens, age))
    return result


def warn_threshold(env: Mapping[str, str] | None = None) -> int:
    """Token threshold from ``AIADEV_CONTEXT_WARN``; invalid or absent uses 150_000."""
    source = os.environ if env is None else env
    raw = source.get(WARN_ENV, "").strip()
    if raw.isascii() and raw.isdigit() and len(raw) <= 12 and int(raw) > 0:
        return int(raw)
    return DEFAULT_WARN


def format_age(seconds: int) -> str:
    if seconds < 60:
        return f"{seconds}s ago"
    if seconds < 3600:
        return f"{seconds // 60} min ago"
    return f"{seconds // 3600} h ago"


def format_lines(contexts: list[SessionContext], threshold: int) -> list[str]:
    lines: list[str] = []
    for ctx in contexts:
        lines.append(
            f"context: {ctx.tokens // 1000}k tokens "
            f"(session {ctx.session_id[:8]}, {format_age(ctx.age_seconds)})"
        )
        if ctx.tokens > threshold:
            lines.append(
                f"checkpoint: context is above {threshold // 1000}k; the state is in "
                "tasks.md and git, so compact or restart the session and resume with `aiadev next`"
            )
    return lines


def context_lines(
    workspace: Path,
    now: float | None = None,
    home: Path | None = None,
    env: Mapping[str, str] | None = None,
) -> list[str]:
    """Single entry point for ``next`` and ``tasks done``; never raises."""
    try:
        return format_lines(active_contexts(workspace, now, home), warn_threshold(env))
    except (OSError, ValueError, RecursionError):
        return []
