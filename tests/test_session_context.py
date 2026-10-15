"""T006 (spec 0031): context of the last request read from the transcript tail."""

from __future__ import annotations

import json
from pathlib import Path

from aiadev.session_context import last_context

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
