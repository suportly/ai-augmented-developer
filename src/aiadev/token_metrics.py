"""Token usage per Claude Code session, read from local transcripts.

Spec: ``specs/0022-smart-mcp-proxy-token-economy/spec.md`` (Story 3).

Claude Code writes one JSONL transcript per session under
``~/.claude/projects/<slug>/<session-id>.jsonl`` where ``<slug>`` is the
absolute workspace path with every ``/`` replaced by ``-``. Each
``assistant`` line carries ``message.usage`` (input, cache creation, cache
read, output tokens) and its ``tool_use`` blocks; each ``user`` line that
answers a tool carries ``tool_result`` blocks keyed by ``tool_use_id``.

This module is **read-only** and never sends anything anywhere. It also
never surfaces message text: only counts and sizes leave this module
(Article VI, Privacy by design). The parser is tolerant — every field it
does not find counts as zero — because the transcript format evolves
between Claude Code versions.

Deduplication (spec ``0030-lean-pipeline``, Story 1): Claude Code writes the
same assistant message several times while streaming, always with the same
``message.id`` and a ``usage`` that only grows (``output_tokens`` 1, then 214).
Each ``message.id`` is therefore counted once, with the **maximum** of every
``usage`` field, so the result does not depend on which occurrence or which
file is read first. An assistant event without ``message.id`` counts as unique.
"""

from __future__ import annotations

import dataclasses
import json
import pathlib
from typing import Any, Dict, Iterable, List, Optional, Tuple


def slug_for(workspace: pathlib.Path) -> str:
    """Return the transcript directory name Claude Code uses for ``workspace``."""
    text = str(workspace.resolve())
    return text.replace("\\", "-").replace("/", "-")


def default_transcripts_dir(workspace: pathlib.Path, home: Optional[pathlib.Path] = None) -> pathlib.Path:
    """``~/.claude/projects/<slug>`` for ``workspace``."""
    base = home if home is not None else pathlib.Path.home()
    return base / ".claude" / "projects" / slug_for(workspace)


@dataclasses.dataclass
class ToolUsage:
    calls: int = 0
    result_chars: int = 0


@dataclasses.dataclass
class SessionTokens:
    session_id: str
    file: str
    started_at: Optional[str] = None
    ended_at: Optional[str] = None
    turns: int = 0
    input_tokens: int = 0
    cache_creation_tokens: int = 0
    cache_read_tokens: int = 0
    output_tokens: int = 0
    tool_calls: int = 0
    tool_result_chars: int = 0
    sidechain_turns: int = 0
    models: List[str] = dataclasses.field(default_factory=list)
    by_tool: Dict[str, ToolUsage] = dataclasses.field(default_factory=dict)

    @property
    def total_input_tokens(self) -> int:
        return self.input_tokens + self.cache_creation_tokens + self.cache_read_tokens

    def to_dict(self) -> Dict[str, Any]:
        d = dataclasses.asdict(self)
        d["total_input_tokens"] = self.total_input_tokens
        d["by_tool"] = {k: dataclasses.asdict(v) for k, v in sorted(self.by_tool.items())}
        return d


@dataclasses.dataclass
class TokenReport:
    transcripts_dir: str
    sessions: List[SessionTokens]

    @property
    def totals(self) -> SessionTokens:
        t = SessionTokens(session_id="TOTAL", file="")
        for s in self.sessions:
            t.turns += s.turns
            t.input_tokens += s.input_tokens
            t.cache_creation_tokens += s.cache_creation_tokens
            t.cache_read_tokens += s.cache_read_tokens
            t.output_tokens += s.output_tokens
            t.tool_calls += s.tool_calls
            t.tool_result_chars += s.tool_result_chars
            t.sidechain_turns += s.sidechain_turns
            for name, u in s.by_tool.items():
                agg = t.by_tool.setdefault(name, ToolUsage())
                agg.calls += u.calls
                agg.result_chars += u.result_chars
        return t

    def to_dict(self) -> Dict[str, Any]:
        return {
            "transcripts_dir": self.transcripts_dir,
            "sessions": [s.to_dict() for s in self.sessions],
            "totals": self.totals.to_dict(),
        }


def _int(value: Any) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) else 0


def _result_chars(content: Any) -> int:
    if isinstance(content, str):
        return len(content)
    if isinstance(content, list):
        total = 0
        for part in content:
            if isinstance(part, dict) and isinstance(part.get("text"), str):
                total += len(part["text"])
        return total
    return 0


_TOKEN_FIELDS = ("input_tokens", "cache_creation_tokens", "cache_read_tokens", "output_tokens")


@dataclasses.dataclass
class _MessageUsage:
    """``usage`` of one assistant message, named after the ``SessionTokens`` fields."""

    input_tokens: int = 0
    cache_creation_tokens: int = 0
    cache_read_tokens: int = 0
    output_tokens: int = 0
    sidechain: bool = False

    @classmethod
    def from_event(cls, usage: Dict[str, Any], sidechain: bool) -> "_MessageUsage":
        return cls(
            input_tokens=_int(usage.get("input_tokens")),
            cache_creation_tokens=_int(usage.get("cache_creation_input_tokens")),
            cache_read_tokens=_int(usage.get("cache_read_input_tokens")),
            output_tokens=_int(usage.get("output_tokens")),
            sidechain=sidechain,
        )

    def merged(self, other: "_MessageUsage") -> "_MessageUsage":
        """Field-wise maximum: streaming ``usage`` only grows, so max == final."""
        values = {f: max(getattr(self, f), getattr(other, f)) for f in _TOKEN_FIELDS}
        return _MessageUsage(sidechain=self.sidechain or other.sidechain, **values)


def _add_message(session: SessionTokens, message: _MessageUsage) -> None:
    session.turns += 1
    if message.sidechain:
        session.sidechain_turns += 1
    for name in _TOKEN_FIELDS:
        setattr(session, name, getattr(session, name) + getattr(message, name))


def _iter_lines(path: pathlib.Path) -> Iterable[Dict[str, Any]]:
    with path.open("r", encoding="utf-8", errors="replace") as fh:
        for raw in fh:
            raw = raw.strip()
            if not raw:
                continue
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if isinstance(data, dict):
                yield data


def _read_transcript(path: pathlib.Path) -> Tuple[SessionTokens, Dict[str, _MessageUsage]]:
    """Parse one transcript file without counting messages that carry a ``message.id``.

    Returns the session (tool results, models, timestamps and the usage of
    events *without* ``message.id`` already applied) and the per-``message.id``
    maximum usage, not yet added to the session so that the caller can
    deduplicate ids that repeat across files. Never raises on malformed lines.
    """
    session = SessionTokens(session_id=path.stem, file=path.name)
    messages: Dict[str, _MessageUsage] = {}
    tool_names: Dict[str, str] = {}
    models: List[str] = []
    for event in _iter_lines(path):
        kind = event.get("type")
        if kind not in ("assistant", "user"):
            continue
        ts = event.get("timestamp")
        if isinstance(ts, str):
            if session.started_at is None or ts < session.started_at:
                session.started_at = ts
            if session.ended_at is None or ts > session.ended_at:
                session.ended_at = ts
        message = event.get("message")
        if not isinstance(message, dict):
            continue
        content = message.get("content")
        if kind == "assistant":
            usage = message.get("usage")
            if isinstance(usage, dict):
                current = _MessageUsage.from_event(usage, sidechain=event.get("isSidechain") is True)
                message_id = message.get("id")
                if isinstance(message_id, str) and message_id:
                    seen = messages.get(message_id)
                    messages[message_id] = seen.merged(current) if seen is not None else current
                else:
                    _add_message(session, current)  # no id: counts as a unique event
            model = message.get("model")
            if isinstance(model, str) and model and not model.startswith("<") and model not in models:
                models.append(model)
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "tool_use":
                        name = block.get("name")
                        tid = block.get("id")
                        if isinstance(name, str) and isinstance(tid, str):
                            tool_names[tid] = name
        else:  # user
            if not isinstance(content, list):
                continue
            for block in content:
                if not isinstance(block, dict) or block.get("type") != "tool_result":
                    continue
                tid = block.get("tool_use_id")
                name = tool_names.get(tid, "(unknown)") if isinstance(tid, str) else "(unknown)"
                chars = _result_chars(block.get("content"))
                session.tool_calls += 1
                session.tool_result_chars += chars
                usage_by_tool = session.by_tool.setdefault(name, ToolUsage())
                usage_by_tool.calls += 1
                usage_by_tool.result_chars += chars
    session.models = models
    return session, messages


def read_session(path: pathlib.Path) -> SessionTokens:
    """Aggregate one transcript file. Never raises on malformed lines.

    Each ``message.id`` is counted once, with the maximum of every usage field.
    """
    session, messages = _read_transcript(path)
    for message in messages.values():
        _add_message(session, message)
    return session


def build_token_report(transcripts_dir: pathlib.Path) -> TokenReport:
    """Aggregate every ``*.jsonl`` under ``transcripts_dir``, oldest session first.

    A ``message.id`` that appears in more than one file is counted once, with
    the maximum of each usage field across files, and attributed to the
    session that started first (ties broken by session id), so the figures do
    not depend on the order files are read.

    Returns an empty report when the directory does not exist; the CLI
    decides how to report that.
    """
    parsed: List[Tuple[SessionTokens, Dict[str, _MessageUsage]]] = []
    if transcripts_dir.is_dir():
        parsed = [_read_transcript(path) for path in sorted(transcripts_dir.glob("*.jsonl"))]
    parsed.sort(key=lambda p: (p[0].started_at or "", p[0].session_id))

    best: Dict[str, _MessageUsage] = {}
    for _, messages in parsed:
        for message_id, usage in messages.items():
            seen = best.get(message_id)
            best[message_id] = seen.merged(usage) if seen is not None else usage

    sessions: List[SessionTokens] = []
    counted: set = set()
    for session, messages in parsed:
        for message_id in messages:
            if message_id not in counted:
                counted.add(message_id)
                _add_message(session, best[message_id])
        if session.turns == 0 and session.tool_calls == 0:
            continue
        sessions.append(session)
    return TokenReport(transcripts_dir=str(transcripts_dir), sessions=sessions)


def _fmt(n: int) -> str:
    return f"{n:,}"


def format_text(report: TokenReport, top_tools: int = 8) -> str:
    """Human-readable table: one row per session, then totals and top tools by chars."""
    lines: List[str] = []
    lines.append(f"Transcripts: {report.transcripts_dir}")
    lines.append(f"Sessions: {len(report.sessions)}")
    lines.append("")
    header = f"{'session':<14} {'started':<20} {'turns':>5} {'input':>9} {'cache_w':>9} {'cache_r':>10} {'output':>8} {'tools':>5} {'tool_chars':>10}"
    lines.append(header)
    lines.append("-" * len(header))
    for s in report.sessions:
        started = (s.started_at or "")[:19].replace("T", " ")
        lines.append(
            f"{s.session_id[:12]:<14} {started:<20} {s.turns:>5} {_fmt(s.input_tokens):>9} "
            f"{_fmt(s.cache_creation_tokens):>9} {_fmt(s.cache_read_tokens):>10} {_fmt(s.output_tokens):>8} "
            f"{s.tool_calls:>5} {_fmt(s.tool_result_chars):>10}"
        )
    t = report.totals
    lines.append("-" * len(header))
    lines.append(
        f"{'TOTAL':<14} {'':<20} {t.turns:>5} {_fmt(t.input_tokens):>9} "
        f"{_fmt(t.cache_creation_tokens):>9} {_fmt(t.cache_read_tokens):>10} {_fmt(t.output_tokens):>8} "
        f"{t.tool_calls:>5} {_fmt(t.tool_result_chars):>10}"
    )
    lines.append("")
    lines.append(f"Total input tokens (input + cache_w + cache_r): {_fmt(t.total_input_tokens)}")
    if t.sidechain_turns:
        lines.append(f"Subagent (sidechain) turns included: {t.sidechain_turns}")
    if t.by_tool:
        lines.append("")
        lines.append(f"Top tools by result chars (chars entering context):")
        ranked = sorted(t.by_tool.items(), key=lambda kv: kv[1].result_chars, reverse=True)[:top_tools]
        width = max(len(name) for name, _ in ranked)
        for name, u in ranked:
            avg = u.result_chars // u.calls if u.calls else 0
            lines.append(f"  {name:<{width}}  calls {u.calls:>5}  chars {_fmt(u.result_chars):>12}  avg {_fmt(avg):>8}")
    return "\n".join(lines) + "\n"


def format_json(report: TokenReport) -> str:
    return json.dumps(report.to_dict(), indent=2, sort_keys=True, ensure_ascii=False) + "\n"
