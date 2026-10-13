"""Tests for ``aiadev metrics --tokens`` (spec 0022, Story 3).

The fixtures are hand-written transcripts in the shape Claude Code writes
under ``~/.claude/projects/<slug>/``: ``s1`` has three assistant turns and
two tool results (one string, one list of text blocks), ``s2`` is a
sidechain session whose tool result has no matching ``tool_use``, and
``empty`` carries no usage at all and must be skipped.
"""

from __future__ import annotations

import json
import os
import pathlib
import shutil
from typing import Any, Dict, List, Optional

import pytest
from click.testing import CliRunner

from aiadev import token_metrics as tm
from aiadev.cli import main

FIXTURES = pathlib.Path(__file__).parent / "fixtures" / "token_metrics"


@pytest.fixture()
def pinned_dir(tmp_path: pathlib.Path) -> pathlib.Path:
    """Only the original hand-written transcripts (s1, s2, empty).

    ``dedupe_partial.jsonl`` lives in the same fixtures directory but is read
    file-by-file or staged into tmp dirs by its own tests; copying the
    originals keeps the directory-level pinned totals (3120 input tokens,
    4 turns, 2 sessions) independent of it.
    """
    target = tmp_path / "pinned"
    target.mkdir()
    for name in ("s1.jsonl", "s2.jsonl", "empty.jsonl"):
        shutil.copyfile(FIXTURES / name, target / name)
    return target


def _assistant(
    ts: str,
    *,
    message_id: Optional[str],
    output: int,
    inp: int = 0,
    cache_w: int = 0,
    cache_r: int = 0,
) -> Dict[str, Any]:
    message: Dict[str, Any] = {
        "model": "claude-opus-5",
        "usage": {
            "input_tokens": inp,
            "cache_creation_input_tokens": cache_w,
            "cache_read_input_tokens": cache_r,
            "output_tokens": output,
        },
        "content": [{"type": "text", "text": "x"}],
    }
    if message_id is not None:
        message["id"] = message_id
    return {"type": "assistant", "timestamp": ts, "message": message}


def _write_transcript(path: pathlib.Path, events: List[Dict[str, Any]]) -> pathlib.Path:
    path.write_text("".join(json.dumps(e) + "\n" for e in events), encoding="utf-8")
    return path


# ---------------------------------------------------------------------
# Story 3 sc1 — aggregation
# ---------------------------------------------------------------------


def test_slug_matches_claude_code_layout(tmp_path: pathlib.Path) -> None:
    slug = tm.slug_for(tmp_path)
    assert "/" not in slug
    assert slug.startswith("-")
    assert tm.default_transcripts_dir(tmp_path, home=tmp_path / "home") == (
        tmp_path / "home" / ".claude" / "projects" / slug
    )


def test_read_session_sums_usage_and_tool_results() -> None:
    s = tm.read_session(FIXTURES / "s1.jsonl")
    assert s.session_id == "s1"
    assert s.turns == 3  # the <synthetic> line has no usage and is not a turn
    assert s.input_tokens == 20
    assert s.cache_creation_tokens == 1000
    assert s.cache_read_tokens == 2000
    assert s.output_tokens == 100
    assert s.total_input_tokens == 3020
    assert s.tool_calls == 2
    assert s.tool_result_chars == 100 + 20
    assert s.by_tool["Bash"].calls == 1 and s.by_tool["Bash"].result_chars == 100
    assert s.by_tool["Read"].result_chars == 20
    assert s.models == ["claude-opus-5"]
    assert s.started_at == "2026-09-15T10:00:00.000Z"
    assert s.ended_at == "2026-09-15T10:00:09.000Z"


def test_read_session_tolerates_sidechain_and_unknown_tool_ids() -> None:
    s = tm.read_session(FIXTURES / "s2.jsonl")
    assert s.turns == 1 and s.sidechain_turns == 1
    assert s.by_tool["mcp__smart__smart_bash_execute"].result_chars == 5
    assert s.by_tool["(unknown)"].result_chars == 2
    assert s.tool_calls == 2


def test_build_report_orders_by_start_and_skips_empty_sessions(pinned_dir: pathlib.Path) -> None:
    report = tm.build_token_report(pinned_dir)
    assert [s.session_id for s in report.sessions] == ["s2", "s1"]
    totals = report.totals
    assert totals.turns == 4
    assert totals.total_input_tokens == 3020 + 100
    assert totals.tool_result_chars == 120 + 7
    assert totals.by_tool["Bash"].calls == 1


def test_build_report_missing_dir_is_empty(tmp_path: pathlib.Path) -> None:
    report = tm.build_token_report(tmp_path / "nope")
    assert report.sessions == []


def test_format_text_has_totals_and_top_tools(pinned_dir: pathlib.Path) -> None:
    text = tm.format_text(tm.build_token_report(pinned_dir))
    assert "Sessions: 2" in text
    assert "TOTAL" in text
    assert "Top tools by result chars" in text
    assert "Bash" in text and "mcp__smart__smart_bash_execute" in text
    # Never surfaces message text (privacy): the fixture's tool result body must not appear.
    assert "aaaaaaaaaa" not in text


# ---------------------------------------------------------------------
# Spec 0030, Story 1 sc1 — dedupe by message.id, max per usage field
# ---------------------------------------------------------------------


def test_read_session_dedupes_streaming_partials_by_message_id() -> None:
    """The same message.id written twice (output 1 then 214) counts once, as 214."""
    s = tm.read_session(FIXTURES / "dedupe_partial.jsonl")
    # msg_01PARTIAL (3 / 500 / 0 / 214) + one event without message.id (7 / 0 / 500 / 40)
    assert s.turns == 2
    assert s.input_tokens == 3 + 7
    assert s.cache_creation_tokens == 500
    assert s.cache_read_tokens == 500
    assert s.output_tokens == 214 + 40
    assert s.tool_calls == 1


def test_read_session_keeps_max_not_last_regardless_of_order(tmp_path: pathlib.Path) -> None:
    path = _write_transcript(
        tmp_path / "s.jsonl",
        [
            _assistant("2026-09-16T10:00:01.000Z", message_id="msg_A", output=214, inp=3),
            _assistant("2026-09-16T10:00:02.000Z", message_id="msg_A", output=1, inp=3),
        ],
    )
    s = tm.read_session(path)
    assert s.turns == 1
    assert s.output_tokens == 214  # not 215 (sum) and not 1 (last)
    assert s.input_tokens == 3


def test_read_session_takes_max_per_field_independently(tmp_path: pathlib.Path) -> None:
    path = _write_transcript(
        tmp_path / "s.jsonl",
        [
            _assistant("2026-09-16T10:00:01.000Z", message_id="msg_A", output=1, inp=9, cache_w=0, cache_r=5),
            _assistant("2026-09-16T10:00:02.000Z", message_id="msg_A", output=50, inp=2, cache_w=700, cache_r=5),
        ],
    )
    s = tm.read_session(path)
    assert (s.input_tokens, s.cache_creation_tokens, s.cache_read_tokens, s.output_tokens) == (9, 700, 5, 50)


def test_events_without_message_id_each_count_as_unique(tmp_path: pathlib.Path) -> None:
    path = _write_transcript(
        tmp_path / "s.jsonl",
        [
            _assistant("2026-09-16T10:00:01.000Z", message_id=None, output=10),
            _assistant("2026-09-16T10:00:02.000Z", message_id=None, output=10),
            _assistant("2026-09-16T10:00:03.000Z", message_id="msg_A", output=10),
        ],
    )
    s = tm.read_session(path)
    assert s.turns == 3
    assert s.output_tokens == 30


def test_build_report_counts_same_message_id_once_across_files(tmp_path: pathlib.Path) -> None:
    """msg_X appears in both files (partial in the earlier session, final in the later one)."""
    _write_transcript(
        tmp_path / "zz-early.jsonl",
        [
            _assistant("2026-09-16T10:00:01.000Z", message_id="msg_X", output=1, inp=3),
            _assistant("2026-09-16T10:00:02.000Z", message_id="msg_Z", output=5),
        ],
    )
    _write_transcript(
        tmp_path / "aa-late.jsonl",
        [
            _assistant("2026-09-16T11:00:01.000Z", message_id="msg_X", output=214, inp=3),
            _assistant("2026-09-16T11:00:02.000Z", message_id="msg_Y", output=9),
        ],
    )
    report = tm.build_token_report(tmp_path)
    totals = report.totals
    assert totals.turns == 3  # X, Y, Z - X counted once
    assert totals.output_tokens == 214 + 9 + 5  # X at its maximum, not 1 + 214
    assert totals.input_tokens == 3
    # The message is attributed to the session that started first, with the maximum value.
    by_id = {s.session_id: s for s in report.sessions}
    assert [s.session_id for s in report.sessions] == ["zz-early", "aa-late"]
    assert by_id["zz-early"].output_tokens == 214 + 5
    assert by_id["zz-early"].turns == 2
    assert by_id["aa-late"].output_tokens == 9
    assert by_id["aa-late"].turns == 1


def test_build_report_dedupe_is_independent_of_file_names(tmp_path: pathlib.Path) -> None:
    """Swapping the file names (hence the read order) must not change the figures."""

    def build(root: pathlib.Path, first: str, second: str) -> List[Any]:
        root.mkdir()
        _write_transcript(
            root / f"{first}.jsonl",
            [_assistant("2026-09-16T10:00:01.000Z", message_id="msg_X", output=1)],
        )
        _write_transcript(
            root / f"{second}.jsonl",
            [
                _assistant("2026-09-16T11:00:01.000Z", message_id="msg_X", output=214),
                _assistant("2026-09-16T11:00:02.000Z", message_id="msg_Y", output=9),
            ],
        )
        report = tm.build_token_report(root)
        return [(s.started_at, s.turns, s.output_tokens) for s in report.sessions] + [
            ("TOTAL", report.totals.turns, report.totals.output_tokens)
        ]

    assert build(tmp_path / "one", "a", "b") == build(tmp_path / "two", "b", "a")


def test_cli_tokens_json_counts_duplicated_message_once(tmp_path: pathlib.Path) -> None:
    shutil.copyfile(FIXTURES / "dedupe_partial.jsonl", tmp_path / "dedupe_partial.jsonl")
    result = CliRunner().invoke(
        main, ["metrics", "--tokens", "--transcripts-dir", str(tmp_path), "--format", "json"]
    )
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["totals"]["turns"] == 2
    assert data["totals"]["output_tokens"] == 214 + 40


# ---------------------------------------------------------------------
# CLI wiring — sc1, sc2, sc3
# ---------------------------------------------------------------------


def test_cli_tokens_text(pinned_dir: pathlib.Path) -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["metrics", "--tokens", "--transcripts-dir", str(pinned_dir)])
    assert result.exit_code == 0, result.output
    assert "Sessions: 2" in result.output
    assert "tool_chars" in result.output


def test_cli_tokens_json_is_stable(pinned_dir: pathlib.Path) -> None:
    runner = CliRunner()
    a = runner.invoke(main, ["metrics", "--tokens", "--transcripts-dir", str(pinned_dir), "--format", "json"])
    b = runner.invoke(main, ["metrics", "--tokens", "--transcripts-dir", str(pinned_dir), "--format", "json"])
    assert a.exit_code == 0, a.output
    assert a.output == b.output
    data = json.loads(a.output)
    assert data["totals"]["total_input_tokens"] == 3120
    assert [s["session_id"] for s in data["sessions"]] == ["s2", "s1"]
    assert data["sessions"][1]["by_tool"]["Bash"]["result_chars"] == 100


def test_cli_tokens_missing_dir_exits_2_with_path(tmp_path: pathlib.Path) -> None:
    runner = CliRunner()
    missing = tmp_path / "no-transcripts"
    result = runner.invoke(main, ["metrics", "--tokens", "--transcripts-dir", str(missing)])
    assert result.exit_code == 2
    assert str(missing) in result.output


def test_cli_tokens_default_dir_derives_from_cwd(tmp_path: pathlib.Path, monkeypatch) -> None:
    """Without --transcripts-dir the command looks under $HOME/.claude/projects/<slug of cwd>."""
    home = tmp_path / "home"
    workspace = tmp_path / "ws"
    workspace.mkdir()
    target = tm.default_transcripts_dir(workspace, home=home)
    target.mkdir(parents=True)
    (target / "s1.jsonl").write_bytes((FIXTURES / "s1.jsonl").read_bytes())
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr(pathlib.Path, "home", classmethod(lambda cls: home))
    cwd = os.getcwd()
    os.chdir(workspace)
    try:
        result = CliRunner().invoke(main, ["metrics", "--tokens"])
    finally:
        os.chdir(cwd)
    assert result.exit_code == 0, result.output
    assert "Sessions: 1" in result.output
