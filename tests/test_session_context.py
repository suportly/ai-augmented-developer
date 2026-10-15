"""T006 (spec 0031): context of the last request read from the transcript tail."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from aiadev import session_context
from aiadev.session_context import (
    SessionContext,
    active_contexts,
    context_lines,
    format_age,
    format_lines,
    last_context,
    warn_threshold,
)
from aiadev.token_metrics import default_transcripts_dir

KIB = 1024
MIB = 1024 * KIB


def _usage_line(mid: str, i: int = 0, c: int = 0, r: int = 0, role: str = "assistant") -> str:
    return json.dumps(
        {
            "type": "assistant",
            "message": {
                "id": mid,
                "role": role,
                "usage": {
                    "input_tokens": i,
                    "cache_creation_input_tokens": c,
                    "cache_read_input_tokens": r,
                    "output_tokens": 5,
                },
            },
        }
    )


def _big_line(size: int, text: str = "x") -> str:
    body = text * size
    return json.dumps(
        {
            "type": "user",
            "message": {
                "role": "user",
                "content": [{"type": "tool_result", "content": body}],
            },
        }
    )


def _write(path: Path, lines: list[str], tail: str = "\n") -> Path:
    path.write_text("\n".join(lines) + tail, encoding="utf-8")
    return path


def test_small_file_returns_last_request_context(tmp_path: Path) -> None:
    p = _write(tmp_path / "t.jsonl", [_usage_line("a", 1, 2, 3), _usage_line("b", 10, 20, 30)])
    assert last_context(p) == 60


def test_small_file_first_line_not_discarded(tmp_path: Path) -> None:
    p = _write(tmp_path / "t.jsonl", [_usage_line("a", 1, 2, 3)])
    assert last_context(p) == 6


def test_large_file_first_line_of_window_is_discarded(tmp_path: Path) -> None:
    # The window starts mid-line inside a huge line; it must not confuse the parse.
    lines = [_usage_line("old", 999), _big_line(300 * KIB), _usage_line("new", 7)]
    p = _write(tmp_path / "t.jsonl", lines)
    assert last_context(p) == 7


def test_cut_first_line_that_is_valid_json_is_not_used(tmp_path: Path) -> None:
    # Window offset > 0 lands exactly so the first (partial) line is a usage line
    # whose tail looks complete: it must be dropped, not counted.
    filler = _big_line(256 * KIB)
    p = tmp_path / "t.jsonl"
    p.write_text(_usage_line("zzz", 500) + "\n" + filler + "\n", encoding="utf-8")
    # Window of 256 KiB sees only part of filler; no usage -> falls to 1 MiB -> finds it.
    assert last_context(p) == 500


def test_tool_result_over_256k_at_end_falls_to_1mib(tmp_path: Path) -> None:
    p = _write(tmp_path / "t.jsonl", [_usage_line("a", 42), _big_line(400 * KIB)])
    assert last_context(p) == 42


def test_5mib_line_without_usage_returns_none(tmp_path: Path) -> None:
    p = _write(tmp_path / "t.jsonl", [_usage_line("a", 42), _big_line(5 * MIB)])
    assert last_context(p) is None


def test_gap_within_4mib_is_found(tmp_path: Path) -> None:
    p = _write(tmp_path / "t.jsonl", [_usage_line("a", 42), _big_line(2 * MIB)])
    assert last_context(p) == 42


def test_no_usage_anywhere_returns_none(tmp_path: Path) -> None:
    p = _write(tmp_path / "t.jsonl", [_big_line(10), json.dumps({"type": "summary"})])
    assert last_context(p) is None


def test_empty_and_missing_files(tmp_path: Path) -> None:
    empty = tmp_path / "e.jsonl"
    empty.write_text("")
    assert last_context(empty) is None
    assert last_context(tmp_path / "missing.jsonl") is None
    assert last_context(tmp_path) is None  # a directory: OSError on open


def test_truncated_final_line_is_ignored(tmp_path: Path) -> None:
    p = tmp_path / "t.jsonl"
    p.write_text(_usage_line("a", 5) + "\n" + _usage_line("b", 99)[:40], encoding="utf-8")
    assert last_context(p) == 5


def test_only_truncated_line(tmp_path: Path) -> None:
    p = tmp_path / "t.jsonl"
    p.write_text(_usage_line("a", 5)[:30], encoding="utf-8")
    assert last_context(p) is None


def test_malformed_lines_are_ignored(tmp_path: Path) -> None:
    lines = [
        _usage_line("a", 3),
        "not json",
        "[1, 2]",
        "42",
        json.dumps({"type": "assistant"}),
        json.dumps({"type": "assistant", "message": "str"}),
        json.dumps({"type": "assistant", "message": {"id": "q", "usage": "x"}}),
        "",
    ]
    assert last_context(_write(tmp_path / "t.jsonl", lines)) == 3


def test_same_message_id_takes_max_per_field(tmp_path: Path) -> None:
    lines = [
        _usage_line("a", 1, 100, 0),
        _usage_line("m", 2, 3, 4),
        _usage_line("m", 2, 50, 4),
        _usage_line("m", 1, 50, 9),
    ]
    assert last_context(_write(tmp_path / "t.jsonl", lines)) == 2 + 50 + 9


def test_user_message_is_ignored(tmp_path: Path) -> None:
    lines = [_usage_line("a", 5), _usage_line("u", 1000, role="user")]
    assert last_context(_write(tmp_path / "t.jsonl", lines)) == 5


def test_non_assistant_type_is_ignored(tmp_path: Path) -> None:
    other = json.loads(_usage_line("x", 1000))
    other["type"] = "system"
    lines = [_usage_line("a", 5), json.dumps(other)]
    assert last_context(_write(tmp_path / "t.jsonl", lines)) == 5


def test_invalid_values_count_zero(tmp_path: Path) -> None:
    line = json.dumps(
        {
            "type": "assistant",
            "message": {
                "id": "a",
                "usage": {
                    "input_tokens": True,
                    "cache_creation_input_tokens": -5,
                    "cache_read_input_tokens": 10**30,
                },
            },
        }
    )
    assert last_context(_write(tmp_path / "t.jsonl", [line])) == 0
    line2 = line.replace("true", "7").replace("-5", '"3"')
    assert last_context(_write(tmp_path / "u.jsonl", [line2])) == 7


def test_secret_in_tool_result_is_never_exposed(tmp_path: Path) -> None:
    secret = "SECRET-MARKER-XYZ"
    lines = [_usage_line("a", 11), _big_line(1, text=secret)]
    result = last_context(_write(tmp_path / "t.jsonl", lines))
    assert result == 11
    assert type(result) is int
    assert secret not in repr(result)


def test_first_window_line_is_dropped_even_when_the_cut_leaves_valid_json(tmp_path: Path) -> None:
    """The window starts exactly at a complete JSON object that is really the
    tail of a longer, malformed line: it must not be counted."""
    from aiadev import session_context as sc

    window = sc._WINDOWS[0]
    good = json.dumps({"type": "assistant", "message": {"id": "m", "usage": {"input_tokens": 1234}}})
    base = {"type": "assistant", "message": {"id": "m", "usage": {"input_tokens": 999_999}, "pad": ""}}
    skeleton = len(json.dumps(base).encode())
    pad = window - len(good.encode()) - 2 - skeleton  # object + "\n" + good + "\n" == window
    base["message"]["pad"] = "p" * pad
    poison = json.dumps(base).encode()
    assert len(poison) + 1 + len(good.encode()) + 1 == window
    path = tmp_path / "s.jsonl"
    path.write_bytes(b"J" * 5000 + poison + b"\n" + good.encode() + b"\n")
    assert last_context(path) == 1234


def test_window_starting_on_a_line_boundary_keeps_its_first_line(tmp_path: Path, monkeypatch) -> None:
    from aiadev import session_context as sc

    monkeypatch.setattr(sc, "_WINDOWS", (1024,))
    line = {"type": "assistant", "message": {"id": "m", "usage": {"input_tokens": 77}, "pad": ""}}
    pad = 1024 - len(json.dumps(line).encode()) - 1
    line["message"]["pad"] = "p" * pad
    raw = json.dumps(line).encode() + b"\n"
    assert len(raw) == 1024
    path = tmp_path / "s.jsonl"
    path.write_bytes(b"junk\n" + raw)
    assert last_context(path) == 77


# --- T007: active sessions, threshold, line format -------------------------

NOW = 1_800_000_000.0


def _session(tmp_path: Path, sid: str, tokens: int | None, age: float, sub: str = "") -> Path:
    ws = tmp_path / "ws"
    ws.mkdir(exist_ok=True)
    d = default_transcripts_dir(ws, tmp_path / "home")
    if sub:
        d = d / sub
    d.mkdir(parents=True, exist_ok=True)
    f = d / f"{sid}.jsonl"
    f.write_text(_usage_line("m", r=tokens) + "\n" if tokens is not None else "{}\n", encoding="utf-8")
    os.utime(f, (NOW - age, NOW - age))
    return f


def _active(tmp_path: Path) -> list[SessionContext]:
    return active_contexts(tmp_path / "ws", now=NOW, home=tmp_path / "home")


def test_most_recent_always_enters_even_when_old(tmp_path: Path) -> None:
    _session(tmp_path, "aaaa", 1000, 99_999)
    out = _active(tmp_path)
    assert out == [SessionContext("aaaa", 1000, 99_999)]


def test_two_within_window_enter_ordered_by_mtime(tmp_path: Path) -> None:
    _session(tmp_path, "old", 2000, 500)
    _session(tmp_path, "new", 1000, 10)
    assert [c.session_id for c in _active(tmp_path)] == ["new", "old"]


def test_window_boundary_600_in_601_out(tmp_path: Path) -> None:
    _session(tmp_path, "new", 1, 5)
    _session(tmp_path, "edge", 1, 600)
    _session(tmp_path, "out", 1, 601)
    assert [c.session_id for c in _active(tmp_path)] == ["new", "edge"]


def test_unreadable_context_is_left_out(tmp_path: Path) -> None:
    _session(tmp_path, "bad", None, 1)
    _session(tmp_path, "good", 5, 2)
    assert [c.session_id for c in _active(tmp_path)] == ["good"]


def test_subagent_directory_is_not_listed(tmp_path: Path) -> None:
    _session(tmp_path, "main", 5, 100)
    _session(tmp_path, "sub", 5, 1, sub="main/subagents")
    assert [c.session_id for c in _active(tmp_path)] == ["main"]


def test_future_mtime_age_is_zero(tmp_path: Path) -> None:
    _session(tmp_path, "fut", 5, -50)
    assert _active(tmp_path)[0].age_seconds == 0


def test_missing_directory_gives_empty(tmp_path: Path) -> None:
    assert active_contexts(tmp_path / "ws", now=NOW, home=tmp_path / "nohome") == []


@pytest.mark.parametrize(
    "env,expected",
    [
        ({}, 150_000),
        ({"AIADEV_CONTEXT_WARN": "200000"}, 200_000),
        ({"AIADEV_CONTEXT_WARN": ""}, 150_000),
        ({"AIADEV_CONTEXT_WARN": "abc"}, 150_000),
        ({"AIADEV_CONTEXT_WARN": "0"}, 150_000),
        ({"AIADEV_CONTEXT_WARN": "-5"}, 150_000),
        ({"AIADEV_CONTEXT_WARN": "1.5"}, 150_000),
    ],
)
def test_warn_threshold(env: dict[str, str], expected: int) -> None:
    assert warn_threshold(env) == expected


def test_format_age() -> None:
    assert [format_age(s) for s in (0, 59, 60, 180, 3599, 3600, 7300)] == [
        "0s ago", "59s ago", "1 min ago", "3 min ago", "59 min ago", "1 h ago", "2 h ago",
    ]


def test_format_lines_exact_and_equal_does_not_warn() -> None:
    above = SessionContext("abcdefgh1234", 412_345, 180)
    assert format_lines([above], 150_000) == [
        "context: 412k tokens (session abcdefgh, 3 min ago)",
        "checkpoint: context is above 150k; the state is in tasks.md and git, "
        "so compact or restart the session and resume with `aiadev next`",
    ]
    assert format_lines([SessionContext("abcdefgh", 150_000, 5)], 150_000) == [
        "context: 150k tokens (session abcdefgh, 5s ago)"
    ]
    assert format_lines([], 150_000) == []


def test_two_sessions_checkpoint_only_for_the_one_above() -> None:
    lines = format_lines([SessionContext("aaaaaaaa", 300_000, 1), SessionContext("bbbbbbbb", 50_000, 2)], 150_000)
    assert [l.split(":")[0] for l in lines] == ["context", "checkpoint", "context"]
    assert "aaaaaaaa" in lines[0] and "bbbbbbbb" in lines[2]


def test_context_lines_composes_with_env(tmp_path: Path) -> None:
    _session(tmp_path, "abcdefgh", 412_345, 180)
    kw = {"now": NOW, "home": tmp_path / "home"}
    assert len(context_lines(tmp_path / "ws", env={}, **kw)) == 2
    assert len(context_lines(tmp_path / "ws", env={"AIADEV_CONTEXT_WARN": "500000"}, **kw)) == 1


def test_context_lines_never_raises(tmp_path: Path, monkeypatch) -> None:
    def boom(*a, **k):
        raise OSError("denied")

    monkeypatch.setattr(session_context, "active_contexts", boom)
    assert context_lines(tmp_path, home=tmp_path) == []
    monkeypatch.setattr(session_context, "active_contexts", lambda *a, **k: (_ for _ in ()).throw(ValueError("x")))
    assert context_lines(tmp_path, home=tmp_path) == []


import os


@pytest.mark.skipif(hasattr(os, "geteuid") and os.geteuid() == 0, reason="chmod 0 does not block root")
def test_unreadable_directory_gives_empty(tmp_path: Path) -> None:
    f = _session(tmp_path, "x", 5, 1)
    d = f.parent
    d.chmod(0)
    try:
        assert _active(tmp_path) == []
        assert context_lines(tmp_path / "ws", now=NOW, home=tmp_path / "home") == []
    finally:
        d.chmod(0o755)


def test_deeply_nested_line_is_skipped_and_never_raises(tmp_path: Path, monkeypatch) -> None:
    from aiadev import session_context as sc

    good = json.dumps({"type": "assistant", "message": {"id": "m", "usage": {"input_tokens": 9}}})
    path = tmp_path / "s.jsonl"
    path.write_text(good + "\n" + "[" * 200_000 + "]" * 200_000 + "\n")
    assert last_context(path) == 9  # the pathological line is just skipped

    real = sc.json.loads

    def boom(raw, *a, **k):
        if raw.startswith(b"["):
            raise RecursionError
        return real(raw, *a, **k)

    monkeypatch.setattr(sc.json, "loads", boom)
    assert last_context(path) == 9
    monkeypatch.setattr(sc, "active_contexts", lambda *a, **k: (_ for _ in ()).throw(RecursionError()))
    assert sc.context_lines(tmp_path / "ws", now=NOW, home=tmp_path / "home") == []


def test_threshold_ignores_non_ascii_digits_and_absurd_lengths() -> None:
    from aiadev.session_context import warn_threshold

    assert warn_threshold({"AIADEV_CONTEXT_WARN": "²"}) == 150_000
    assert warn_threshold({"AIADEV_CONTEXT_WARN": "١٢٣"}) == 150_000
    assert warn_threshold({"AIADEV_CONTEXT_WARN": "9" * 5000}) == 150_000


def test_context_k_truncates_instead_of_rounding() -> None:
    from aiadev.session_context import SessionContext, format_lines

    (line,) = format_lines([SessionContext("abcdefgh1234", 412_900, 5)], 1_000_000)
    assert line.startswith("context: 412k tokens (session abcdefgh,")
