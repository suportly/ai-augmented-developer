"""Tests for ``aiadev metrics --tokens`` (spec 0022, Story 3).

The fixtures are hand-written transcripts in the shape Claude Code writes
under ``~/.claude/projects/<slug>/``: ``s1`` has three assistant turns and
two tool results (one string, one list of text blocks), ``s2`` is a
sidechain session whose tool result has no matching ``tool_use``, and
``empty`` carries no usage at all and must be skipped.
"""

from __future__ import annotations

import dataclasses
import json
import os
import pathlib
import re
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


@pytest.fixture()
def subagent_dir(tmp_path: pathlib.Path) -> pathlib.Path:
    """``with_subagents/`` staged in tmp: ``sess-main`` plus ``agent-aaa``, nested ``agent-bbb`` and a journal.

    Main thread: 2 turns, input 15 / cache_w 100 / cache_r 100 / output 150,
    one Bash tool result of 2 chars. Subagents: aaa (2 turns, 5 / 200 / 200 /
    50), bbb under ``workflows/wf_x`` (2 turns, 5 / 50 / 300 / 50). The
    sibling ``journal.jsonl`` carries 9999-token assistant events that must
    never be read. Each agent has an ``agent-<id>.meta.json`` next to it:
    aaa is described as ``implement: ...`` and bbb as ``review: ...``.
    """
    target = tmp_path / "with_subagents"
    shutil.copytree(FIXTURES / "with_subagents", target)
    return target


def _assistant(
    ts: str,
    *,
    message_id: Optional[str],
    output: int,
    inp: int = 0,
    cache_w: int = 0,
    cache_r: int = 0,
    detail: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """One assistant event; ``detail`` is the ``usage.cache_creation`` object (absent when ``None``)."""
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
    if detail is not None:
        message["usage"]["cache_creation"] = detail
    if message_id is not None:
        message["id"] = message_id
    return {"type": "assistant", "timestamp": ts, "message": message}


def _write_transcript(path: pathlib.Path, events: List[Dict[str, Any]]) -> pathlib.Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(e) + "\n" for e in events), encoding="utf-8")
    return path


def _write_agent(
    root: pathlib.Path, session: str, relative: str, events: List[Dict[str, Any]]
) -> pathlib.Path:
    """Write ``<root>/<session>/subagents/<relative>`` the way Claude Code lays it out."""
    flagged = [dict(e, isSidechain=True) for e in events]
    return _write_transcript(root / session / "subagents" / relative, flagged)


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
# Spec 0030, Story 1 sc2/sc3 — subagents under <session>/subagents/
# ---------------------------------------------------------------------


def _agents(session: tm.SessionTokens) -> Dict[str, tm.SubagentTokens]:
    return {a.agent_id: a for a in session.subagents}


def test_subagent_usage_is_reported_separately_from_main(subagent_dir: pathlib.Path) -> None:
    report = tm.build_token_report(subagent_dir)
    assert [s.session_id for s in report.sessions] == ["sess-main"]
    main = report.sessions[0]

    # Main-thread figures stay main-thread only.
    assert main.turns == 2
    assert (main.input_tokens, main.cache_creation_tokens, main.cache_read_tokens, main.output_tokens) == (
        15,
        100,
        100,
        150,
    )
    assert main.tool_calls == 1 and main.tool_result_chars == 2  # the subagent's tool result is not counted
    assert report.totals.turns == 2 and report.totals.output_tokens == 150

    # Each subagent has its own figures, found by the agent-<id>.jsonl file name.
    agents = _agents(main)
    assert sorted(agents) == ["aaa", "bbb"]
    aaa, bbb = agents["aaa"], agents["bbb"]
    assert (aaa.turns, aaa.input_tokens, aaa.cache_creation_tokens, aaa.cache_read_tokens, aaa.output_tokens) == (
        2,
        5,
        200,
        200,
        50,
    )
    assert (bbb.turns, bbb.input_tokens, bbb.cache_creation_tokens, bbb.cache_read_tokens, bbb.output_tokens) == (
        2,
        5,
        50,
        300,
        50,
    )

    # Report-level subagent sum, separate from the main-thread totals.
    sub = report.subagent_totals
    assert sub.turns == 4
    assert (sub.input_tokens, sub.cache_creation_tokens, sub.cache_read_tokens, sub.output_tokens) == (
        10,
        250,
        500,
        100,
    )
    assert sub.total_input_tokens == 760

    # sidechain_turns is no longer zero: it is the number of subagent turns.
    assert main.sidechain_turns == 4
    assert report.totals.sidechain_turns == 4


def test_nested_workflow_agents_are_included_and_journal_is_ignored(subagent_dir: pathlib.Path) -> None:
    report = tm.build_token_report(subagent_dir)
    agents = _agents(report.sessions[0])
    assert "bbb" in agents  # subagents/workflows/wf_x/agent-bbb.jsonl
    assert "journal" not in agents
    assert not any("journal" in a.agent_id for a in report.sessions[0].subagents)
    # journal.jsonl holds 9999-token assistant events: none of them may leak into the sums.
    sub = report.subagent_totals
    assert sub.output_tokens == 100 and sub.input_tokens == 10
    assert sub.turns == 4


def test_read_session_includes_the_subagents_next_to_it(subagent_dir: pathlib.Path) -> None:
    s = tm.read_session(subagent_dir / "sess-main.jsonl")
    assert sorted(_agents(s)) == ["aaa", "bbb"]
    assert s.turns == 2 and s.sidechain_turns == 4


def test_session_without_subagents_dir_has_empty_subagents(pinned_dir: pathlib.Path) -> None:
    report = tm.build_token_report(pinned_dir)
    assert [s.session_id for s in report.sessions] == ["s2", "s1"]
    assert all(s.subagents == [] for s in report.sessions)
    assert report.subagent_totals.turns == 0
    assert report.subagent_totals.total_input_tokens == 0
    assert tm.read_session(FIXTURES / "s1.jsonl").subagents == []


def test_session_with_empty_subagents_dir_is_fine(tmp_path: pathlib.Path) -> None:
    _write_transcript(
        tmp_path / "s.jsonl",
        [_assistant("2026-09-16T10:00:01.000Z", message_id="msg_A", output=10)],
    )
    (tmp_path / "s" / "subagents").mkdir(parents=True)
    report = tm.build_token_report(tmp_path)
    assert report.sessions[0].subagents == []
    assert report.sessions[0].sidechain_turns == 0


def test_message_id_repeated_between_main_and_subagent_counts_once(tmp_path: pathlib.Path) -> None:
    _write_transcript(
        tmp_path / "s.jsonl",
        [_assistant("2026-09-16T10:00:01.000Z", message_id="msg_X", output=1, inp=3)],
    )
    _write_agent(
        tmp_path,
        "s",
        "agent-a.jsonl",
        [
            _assistant("2026-09-16T10:00:02.000Z", message_id="msg_X", output=214, inp=3),
            _assistant("2026-09-16T10:00:03.000Z", message_id="msg_Y", output=9),
        ],
    )
    report = tm.build_token_report(tmp_path)
    main = report.sessions[0]
    # msg_X belongs to the main thread (at its maximum); the subagent keeps only msg_Y.
    assert main.turns == 1 and main.output_tokens == 214 and main.input_tokens == 3
    sub = report.subagent_totals
    assert sub.turns == 1 and sub.output_tokens == 9
    assert report.totals.turns + sub.turns == 2  # X once, Y once
    assert main.sidechain_turns == 1


def test_message_id_repeated_between_two_subagents_counts_once(tmp_path: pathlib.Path) -> None:
    def build(root: pathlib.Path, first: str, second: str) -> tm.TokenReport:
        _write_transcript(
            root / "s.jsonl",
            [_assistant("2026-09-16T10:00:00.000Z", message_id="msg_M", output=1)],
        )
        _write_agent(
            root,
            "s",
            f"{first}.jsonl",
            [
                _assistant("2026-09-16T10:00:01.000Z", message_id="msg_S", output=1, inp=3),
                _assistant("2026-09-16T10:00:02.000Z", message_id="msg_P", output=5),
            ],
        )
        _write_agent(
            root,
            "s",
            f"workflows/wf_x/{second}.jsonl",
            [
                _assistant("2026-09-16T10:00:03.000Z", message_id="msg_S", output=214, inp=3),
                _assistant("2026-09-16T10:00:04.000Z", message_id="msg_Q", output=7),
            ],
        )
        return tm.build_token_report(root)

    one = build(tmp_path / "one", "agent-a", "agent-b")
    two = build(tmp_path / "two", "agent-b", "agent-a")
    for report in (one, two):
        sub = report.subagent_totals
        assert sub.turns == 3  # S, P, Q - S counted once
        assert sub.output_tokens == 214 + 5 + 7  # S at its maximum, not 1 + 214
        assert sub.input_tokens == 3
        assert report.totals.turns == 1
    # The figures do not depend on which file is read first.
    assert one.subagent_totals == two.subagent_totals


def test_subagent_streaming_partials_dedupe_inside_one_file(tmp_path: pathlib.Path) -> None:
    _write_transcript(
        tmp_path / "s.jsonl",
        [_assistant("2026-09-16T10:00:00.000Z", message_id="msg_M", output=1)],
    )
    _write_agent(
        tmp_path,
        "s",
        "agent-a.jsonl",
        [
            _assistant("2026-09-16T10:00:01.000Z", message_id="msg_A", output=1, inp=3, cache_w=500),
            _assistant("2026-09-16T10:00:02.000Z", message_id="msg_A", output=214, inp=3, cache_w=500),
            _assistant("2026-09-16T10:00:03.000Z", message_id=None, output=40, inp=7),
        ],
    )
    (agent,) = tm.build_token_report(tmp_path).sessions[0].subagents
    assert agent.agent_id == "a"
    assert agent.turns == 2
    assert agent.output_tokens == 214 + 40
    assert agent.input_tokens == 3 + 7
    assert agent.cache_creation_tokens == 500


def test_unreadable_or_garbage_subagent_files_are_skipped(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_transcript(
        tmp_path / "s.jsonl",
        [_assistant("2026-09-16T10:00:00.000Z", message_id="msg_M", output=1)],
    )
    _write_agent(
        tmp_path, "s", "agent-ok.jsonl", [_assistant("2026-09-16T10:00:01.000Z", message_id="msg_A", output=5)]
    )
    # Would count (99 output tokens) if it were read; the patched reader refuses it below.
    _write_agent(
        tmp_path, "s", "agent-locked.jsonl", [_assistant("2026-09-16T10:00:02.000Z", message_id="msg_L", output=99)]
    )
    agents_dir = tmp_path / "s" / "subagents"
    (agents_dir / "agent-garbage.jsonl").write_bytes(b"not json\n{broken\n\xff\xfe\x00\n[1, 2]\n")
    (agents_dir / "agent-dir.jsonl").mkdir()  # a directory that happens to match the pattern

    real_read = tm._read_transcript

    def read_or_deny(path: pathlib.Path) -> Any:
        if path.name == "agent-locked.jsonl":  # deterministic stand-in for chmod 000 (a no-op as root)
            raise PermissionError(13, "Permission denied", str(path))
        return real_read(path)

    monkeypatch.setattr(tm, "_read_transcript", read_or_deny)
    report = tm.build_token_report(tmp_path)

    agents = _agents(report.sessions[0])
    assert "ok" in agents and agents["ok"].output_tokens == 5
    assert "garbage" not in agents and "dir" not in agents
    assert "locked" not in agents
    assert report.sessions[0].turns == 1


def test_subagents_path_that_is_a_regular_file_is_ignored(tmp_path: pathlib.Path) -> None:
    _write_transcript(
        tmp_path / "s.jsonl",
        [
            _assistant("2026-09-16T10:00:01.000Z", message_id="msg_A", output=10),
            _assistant("2026-09-16T10:00:02.000Z", message_id="msg_B", output=20),
        ],
    )
    (tmp_path / "s").mkdir()
    (tmp_path / "s" / "subagents").write_text("not a directory\n", encoding="utf-8")  # a file, not a dir

    report = tm.build_token_report(tmp_path)
    main = report.sessions[0]
    assert main.subagents == []
    assert main.turns == 2 and main.output_tokens == 30
    assert main.sidechain_turns == 0
    assert report.subagent_totals.turns == 0
    assert tm.read_session(tmp_path / "s.jsonl").subagents == []


def test_subagent_text_and_tool_results_never_surface(subagent_dir: pathlib.Path) -> None:
    report = tm.build_token_report(subagent_dir)
    for rendered in (repr(report), tm.format_text(report), tm.format_json(report)):
        assert "subagent-secret-body" not in rendered
        assert "workflow step" not in rendered


# ---------------------------------------------------------------------
# Spec 0030, Story 1 sc2/sc3 — subagent role from the meta.json description
# ---------------------------------------------------------------------


def _write_meta(root: pathlib.Path, agent: str, meta: Any, session: str = "s") -> pathlib.Path:
    """Write ``agent-<agent>.meta.json`` next to ``agent-<agent>.jsonl`` (raw text when ``meta`` is a str)."""
    path = root / session / "subagents" / f"agent-{agent}.meta.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(meta if isinstance(meta, str) else json.dumps(meta), encoding="utf-8")
    return path


def _session_with_agents(root: pathlib.Path, agents: List[str]) -> None:
    """A main thread plus one one-turn subagent transcript per name in ``agents`` (no meta.json yet)."""
    _write_transcript(
        root / "s.jsonl",
        [_assistant("2026-09-16T10:00:00.000Z", message_id="msg_M", output=1)],
    )
    for name in agents:
        _write_agent(
            root,
            "s",
            f"agent-{name}.jsonl",
            [_assistant("2026-09-16T10:00:01.000Z", message_id=f"msg_{name}", output=5)],
        )


def test_subagent_role_comes_from_the_meta_json_description_prefix(subagent_dir: pathlib.Path) -> None:
    report = tm.build_token_report(subagent_dir)
    agents = _agents(report.sessions[0])
    assert agents["aaa"].role == "implement"
    assert agents["bbb"].role == "review"  # nested under workflows/wf_x, meta.json next to it
    assert report.unclassified_subagents == 0
    assert _agents(tm.read_session(subagent_dir / "sess-main.jsonl"))["aaa"].role == "implement"


@pytest.mark.parametrize(
    ("description", "role"),
    [
        ("implement: T003 add the role field", "implement"),
        ("review: T003 add the role field", "review"),
        ("review: branch feature/0030-lean-pipeline", "review"),
        ("  IMPLEMENT: T003", "implement"),  # case-insensitive, leading whitespace tolerated
        ("\tReview: T003", "review"),
        ("doc-review: spec 0031", "doc-review"),  # spec 0031 T010
        ("Doc-Review: plan x", "doc-review"),
        ("  DOC-REVIEW: tasks", "doc-review"),
        ("doc-review spec", "unclassified"),  # the colon is required
        ("doc-review : spec", "unclassified"),
        ("doc-reviewer: spec", "unclassified"),
        ("implement:", "implement"),  # the prefix alone is enough
        ("implement T003", "unclassified"),  # the colon is required
        ("implement : T003", "unclassified"),
        ("implementation: T003", "unclassified"),  # a longer word is not the prefix
        ("review of implement: T003", "unclassified"),  # a prefix, not a substring
        ("Explore the transcripts", "unclassified"),
        ("spec-document-reviewer: spec", "unclassified"),
        ("", "unclassified"),
    ],
)
def test_subagent_role_prefix_convention(tmp_path: pathlib.Path, description: str, role: str) -> None:
    _session_with_agents(tmp_path, ["a"])
    _write_meta(tmp_path, "a", {"agentType": "general-purpose", "description": description, "spawnDepth": 1})
    (agent,) = tm.build_token_report(tmp_path).sessions[0].subagents
    assert agent.role == role


def test_agent_type_is_not_used_to_infer_the_role(tmp_path: pathlib.Path) -> None:
    _session_with_agents(tmp_path, ["a"])
    _write_meta(tmp_path, "a", {"agentType": "implement", "description": "Explore the repo"})
    (agent,) = tm.build_token_report(tmp_path).sessions[0].subagents
    assert agent.role == "unclassified"


def test_missing_or_unreadable_meta_json_is_unclassified_and_counted(tmp_path: pathlib.Path) -> None:
    names = ["ok", "nometa", "garbage", "binary", "deep", "digits", "array", "nodesc", "numdesc", "nulldesc", "dirmeta"]
    _session_with_agents(tmp_path, names)
    _write_meta(tmp_path, "ok", {"description": "implement: T003"})
    # "nometa" has no meta.json at all.
    _write_meta(tmp_path, "garbage", "{not json at all")
    (tmp_path / "s" / "subagents" / "agent-binary.meta.json").write_bytes(b"\xff\xfe\x00{\x80")
    _write_meta(tmp_path, "deep", "[" * 1_000_000)  # deeper than any supported interpreter limit -> RecursionError
    # an integer with > 4300 digits raises a plain ValueError (not JSONDecodeError)
    _write_meta(tmp_path, "digits", '{"description": 1' + "0" * 5000 + "}")
    _write_meta(tmp_path, "array", [1, 2, 3])  # valid JSON, not an object
    _write_meta(tmp_path, "nodesc", {"agentType": "general-purpose"})
    _write_meta(tmp_path, "numdesc", {"description": 42})
    _write_meta(tmp_path, "nulldesc", {"description": None})
    (tmp_path / "s" / "subagents" / "agent-dirmeta.meta.json").mkdir()  # cannot be opened as a file

    report = tm.build_token_report(tmp_path)  # must not raise
    agents = _agents(report.sessions[0])
    assert sorted(agents) == sorted(names)  # every transcript is still reported
    assert agents["ok"].role == "implement"
    assert {n: a.role for n, a in agents.items() if n != "ok"} == {n: "unclassified" for n in names if n != "ok"}
    assert report.unclassified_subagents == len(names) - 1
    # A broken meta.json costs the role, never the figures.
    assert all(a.turns == 1 and a.output_tokens == 5 for a in agents.values())
    assert report.subagent_totals.turns == len(names)


def test_unclassified_count_spans_sessions_and_is_zero_without_subagents(
    tmp_path: pathlib.Path, pinned_dir: pathlib.Path
) -> None:
    assert tm.build_token_report(pinned_dir).unclassified_subagents == 0
    assert tm.build_token_report(tmp_path / "missing").unclassified_subagents == 0

    for session, started in (("s1", "2026-09-16T10:00:00.000Z"), ("s2", "2026-09-17T10:00:00.000Z")):
        _write_transcript(
            tmp_path / f"{session}.jsonl", [_assistant(started, message_id=f"msg_{session}", output=1)]
        )
        for agent in ("a", "b"):
            _write_agent(
                tmp_path,
                session,
                f"agent-{agent}.jsonl",
                [_assistant(started, message_id=f"msg_{session}_{agent}", output=3)],
            )
    _write_meta(tmp_path, "a", {"description": "implement: T001"}, session="s1")
    _write_meta(tmp_path, "b", {"description": "no convention"}, session="s1")
    # s2 has no meta.json at all: both of its agents are unclassified.
    report = tm.build_token_report(tmp_path)
    assert [a.role for s in report.sessions for a in s.subagents] == [
        "implement",
        "unclassified",
        "unclassified",
        "unclassified",
    ]
    assert report.unclassified_subagents == 3


def test_subagent_role_never_reads_message_text(tmp_path: pathlib.Path) -> None:
    def chatty(message_id: str) -> Dict[str, Any]:
        event = _assistant("2026-09-16T10:00:01.000Z", message_id=message_id, output=5)
        event["message"]["content"] = [{"type": "text", "text": "implement: T003 review: branch"}]
        return event

    prompt = {
        "type": "user",
        "timestamp": "2026-09-16T10:00:02.000Z",
        "message": {"role": "user", "content": "review: T003 implement: T003"},
    }
    _session_with_agents(tmp_path, [])  # main thread only
    _write_agent(tmp_path, "s", "agent-chatty.jsonl", [chatty("msg_C")])
    _write_agent(tmp_path, "s", "agent-prompted.jsonl", [prompt, chatty("msg_P")])
    report = tm.build_token_report(tmp_path)
    assert {a.agent_id: a.role for a in report.sessions[0].subagents} == {
        "chatty": "unclassified",
        "prompted": "unclassified",
    }
    assert report.unclassified_subagents == 2


def test_subagent_description_text_never_surfaces(subagent_dir: pathlib.Path) -> None:
    report = tm.build_token_report(subagent_dir)
    # The roles were derived (so the meta.json files were read) ...
    assert {a.role for a in report.sessions[0].subagents} == {"implement", "review"}
    # ... but only the role is kept, never the description it came from.
    for rendered in (repr(report), tm.format_text(report), tm.format_json(report)):
        assert "description-secret-marker" not in rendered
    for agent in report.sessions[0].subagents:
        assert "description-secret-marker" not in repr(dataclasses.asdict(agent))


# ---------------------------------------------------------------------
# Spec 0030, Story 1 sc4 — documented weights and equivalent cost
# ---------------------------------------------------------------------


def _tiers(five_minute: Optional[int] = None, one_hour: Optional[int] = None) -> Dict[str, int]:
    """A ``usage.cache_creation`` object in the shape Claude Code writes; omitted tiers are absent."""
    detail: Dict[str, int] = {}
    if five_minute is not None:
        detail["ephemeral_5m_input_tokens"] = five_minute
    if one_hour is not None:
        detail["ephemeral_1h_input_tokens"] = one_hour
    return detail


def _cost(tmp_path: pathlib.Path, *events: Dict[str, Any]) -> float:
    """Equivalent cost of a main-thread transcript made of ``events``."""
    path = _write_transcript(tmp_path / "cost.jsonl", list(events))
    return tm.read_session(path).equivalent_cost


def test_weights_are_named_documented_constants() -> None:
    assert tm.WEIGHT_CACHE_READ == 0.1
    assert tm.WEIGHT_INPUT == 1.0
    assert tm.WEIGHT_OUTPUT == 5.0
    assert tm.WEIGHT_CACHE_WRITE_5M == 1.25
    assert tm.WEIGHT_CACHE_WRITE_1H == 2.0


def test_equivalent_cost_weights_the_four_usage_components(tmp_path: pathlib.Path) -> None:
    event = _assistant(
        "2026-09-16T10:00:01.000Z",
        message_id="msg_A",
        inp=100,
        cache_r=1000,
        output=10,
        cache_w=100,
        detail=_tiers(five_minute=40, one_hour=60),
    )
    # 1.0*100 + 0.1*1000 + 5.0*10 + 1.25*40 + 2.0*60
    assert _cost(tmp_path, event) == 100 + 100 + 50 + 50 + 120 == 420


def test_cache_write_without_tier_detail_is_weighted_at_the_5m_rate(tmp_path: pathlib.Path) -> None:
    event = _assistant("2026-09-16T10:00:01.000Z", message_id="msg_A", output=0, cache_w=1000)
    assert _cost(tmp_path, event) == 1250  # 1.25 * cache_creation_input_tokens


def test_equivalent_cost_of_pinned_fixtures_is_comparable_across_sessions(pinned_dir: pathlib.Path) -> None:
    report = tm.build_token_report(pinned_dir)
    by_id = {s.session_id: s for s in report.sessions}
    # s1: input 20, cache_w 1000 (no detail), cache_r 2000, output 100
    assert by_id["s1"].equivalent_cost == 20 + 1250 + 200 + 500 == 1970
    # s2: input 100, output 7
    assert by_id["s2"].equivalent_cost == 100 + 35 == 135
    assert report.totals.equivalent_cost == 1970 + 135
    assert report.totals.equivalent_cost == pytest.approx(sum(s.equivalent_cost for s in report.sessions))


def test_cost_of_an_empty_session_is_zero() -> None:
    assert tm.SessionTokens(session_id="x", file="x.jsonl").equivalent_cost == 0
    assert tm.SubagentTokens(agent_id="x").equivalent_cost == 0


def test_cost_is_rounded_to_strip_float_noise(tmp_path: pathlib.Path) -> None:
    # 0.1 * 3 == 0.30000000000000004 and 0.1 * 1234567 == 123456.70000000001 in binary floats;
    # every weight has <= 2 decimals, so rounding to 2 decimals is exact and keeps totals comparable.
    one = _assistant("2026-10-13T10:00:00Z", message_id="m1", output=0, cache_r=3)
    assert _cost(tmp_path, one) == 0.3
    big = _assistant("2026-10-13T10:00:00Z", message_id="m2", output=0, cache_r=1234567)
    assert _cost(tmp_path / "big", big) == 123456.7


@pytest.mark.parametrize(
    ("cache_w", "detail", "expected"),
    [
        # detail breaks all of it down: 1.25*40 + 2.0*60
        (100, _tiers(five_minute=40, one_hour=60), 50 + 120),
        # real transcripts: everything is 1h and 5m + 1h == cache_creation_input_tokens
        (100, _tiers(five_minute=0, one_hour=100), 200),
        # only one tier present: the other counts as 0 and the remainder is weighted at 1.25
        (100, _tiers(one_hour=60), 120 + 1.25 * 40),
        (100, _tiers(five_minute=40), 50 + 1.25 * 60),
        # detail covers less than the total: the remainder is weighted at 1.25
        (100, _tiers(five_minute=20, one_hour=30), 25 + 60 + 1.25 * 50),
        # detail covers more than the total: trust the detail, the remainder never goes negative
        (100, _tiers(five_minute=300, one_hour=0), 375),
        (100, _tiers(five_minute=60, one_hour=60), 75 + 120),
        # an empty detail object says nothing: same as no detail
        (100, {}, 125),
        # detail without a total: weight what the detail says
        (0, _tiers(five_minute=10, one_hour=10), 12.5 + 20),
    ],
)
def test_cache_write_rule_when_detail_and_total_disagree(
    tmp_path: pathlib.Path, cache_w: int, detail: Dict[str, int], expected: float
) -> None:
    event = _assistant("2026-09-16T10:00:01.000Z", message_id="msg_A", output=0, cache_w=cache_w, detail=detail)
    assert _cost(tmp_path, event) == expected


@pytest.mark.parametrize(
    "detail",
    [None, "5m", [1, 2], 7, True, {"ephemeral_5m_input_tokens": "9", "ephemeral_1h_input_tokens": None}],
    ids=["null", "string", "list", "int", "bool", "non-int-values"],
)
def test_malformed_cache_creation_detail_falls_back_to_the_total(tmp_path: pathlib.Path, detail: Any) -> None:
    event = _assistant("2026-09-16T10:00:01.000Z", message_id="msg_A", output=0, cache_w=100)
    event["message"]["usage"]["cache_creation"] = detail
    assert _cost(tmp_path, event) == 125  # 1.25 * cache_creation_input_tokens


def test_tier_detail_follows_the_max_per_field_dedupe_across_partials(tmp_path: pathlib.Path) -> None:
    """Streaming repeats one message.id; 5m and 1h are kept at their maximum, counted once."""
    first = _assistant(
        "2026-09-16T10:00:01.000Z",
        message_id="msg_A",
        output=1,
        cache_w=500,
        detail=_tiers(five_minute=300, one_hour=0),
    )
    last = _assistant(
        "2026-09-16T10:00:02.000Z",
        message_id="msg_A",
        output=214,
        cache_w=500,
        detail=_tiers(five_minute=100, one_hour=200),
    )
    # max per field: 5m = 300 (from the first), 1h = 200 (from the last); the remainder is 0
    expected = 5 * 214 + 1.25 * 300 + 2.0 * 200
    assert _cost(tmp_path, first, last) == expected
    assert _cost(tmp_path, last, first) == expected  # independent of the order of the partials

    session = tm.read_session(tmp_path / "cost.jsonl")
    assert session.turns == 1
    assert (session.cache_write_5m_tokens, session.cache_write_1h_tokens) == (300, 200)


def test_tier_detail_arriving_late_replaces_the_5m_fallback_instead_of_adding_to_it(
    tmp_path: pathlib.Path,
) -> None:
    """A partial without the detail must not make the final message pay 1.25x on top of its 1h write."""
    partial = _assistant("2026-09-16T10:00:01.000Z", message_id="msg_A", output=1, cache_w=100)
    final = _assistant(
        "2026-09-16T10:00:02.000Z", message_id="msg_A", output=9, cache_w=100, detail=_tiers(one_hour=100)
    )
    assert _cost(tmp_path, partial, final) == 5 * 9 + 2.0 * 100


def test_cost_counts_a_message_repeated_across_main_and_subagent_once(tmp_path: pathlib.Path) -> None:
    _write_transcript(
        tmp_path / "s.jsonl",
        [
            _assistant(
                "2026-09-16T10:00:01.000Z",
                message_id="msg_X",
                output=1,
                cache_w=100,
                detail=_tiers(five_minute=0, one_hour=100),
            )
        ],
    )
    _write_agent(
        tmp_path,
        "s",
        "agent-a.jsonl",
        [
            _assistant(
                "2026-09-16T10:00:02.000Z",
                message_id="msg_X",
                output=10,
                cache_w=100,
                detail=_tiers(five_minute=0, one_hour=100),
            )
        ],
    )
    report = tm.build_token_report(tmp_path)
    # msg_X is the main thread's, at its maximum; the subagent keeps nothing, so it is not reported.
    assert report.sessions[0].equivalent_cost == 5 * 10 + 2.0 * 100
    assert report.sessions[0].subagents == []
    assert report.subagent_totals.equivalent_cost == 0


def test_cost_is_kept_per_subagent_and_in_the_report_totals(tmp_path: pathlib.Path) -> None:
    _write_transcript(
        tmp_path / "s.jsonl",
        [
            _assistant(
                "2026-09-16T10:00:00.000Z",
                message_id="msg_M",
                inp=10,
                output=2,
                cache_w=100,
                detail=_tiers(five_minute=0, one_hour=100),
            )
        ],
    )
    _write_agent(
        tmp_path,
        "s",
        "agent-a.jsonl",
        [
            # msg_A is written twice while streaming: counted once at its maximum
            _assistant("2026-09-16T10:00:01.000Z", message_id="msg_A", output=1, cache_r=1000),
            _assistant(
                "2026-09-16T10:00:02.000Z",
                message_id="msg_A",
                output=20,
                cache_r=1000,
                cache_w=40,
                detail=_tiers(five_minute=40, one_hour=0),
            ),
        ],
    )
    _write_agent(
        tmp_path,
        "s",
        "workflows/wf_x/agent-b.jsonl",
        [_assistant("2026-09-16T10:00:03.000Z", message_id="msg_B", inp=50, output=4, cache_w=10)],
    )
    report = tm.build_token_report(tmp_path)
    main = report.sessions[0]
    agents = _agents(main)

    assert main.equivalent_cost == 10 + 10 + 200  # 1.0*10 + 5.0*2 + 2.0*100
    assert agents["a"].equivalent_cost == 100 + 100 + 50  # 0.1*1000 + 5.0*20 + 1.25*40
    assert agents["b"].equivalent_cost == 50 + 20 + 12.5  # 1.0*50 + 5.0*4 + 1.25*10
    # The report keeps main thread and subagents apart, and each total is the sum of its parts.
    assert report.totals.equivalent_cost == main.equivalent_cost
    sub = report.subagent_totals
    assert sub.equivalent_cost == pytest.approx(agents["a"].equivalent_cost + agents["b"].equivalent_cost)
    assert (sub.cache_write_5m_tokens, sub.cache_write_1h_tokens) == (50, 0)


# ---------------------------------------------------------------------
# Spec 0030, Story 1 sc2/sc4 — report formats: subagents by role, cost, JSON keys
# ---------------------------------------------------------------------

# The per-session JSON keys before spec 0030: the report may gain keys, never lose these.
_LEGACY_SESSION_KEYS = frozenset(
    {
        "session_id",
        "file",
        "started_at",
        "ended_at",
        "turns",
        "input_tokens",
        "cache_creation_tokens",
        "cache_read_tokens",
        "output_tokens",
        "tool_calls",
        "tool_result_chars",
        "sidechain_turns",
        "models",
        "by_tool",
        "total_input_tokens",
    }
)
_LEGACY_REPORT_KEYS = frozenset({"transcripts_dir", "sessions", "totals"})
_SUBAGENT_JSON_KEYS = {
    "agent_id",
    "role",
    "turns",
    "input_tokens",
    "cache_creation_tokens",
    "cache_read_tokens",
    "output_tokens",
    "equivalent_cost",
}


def _role_rows(text: str) -> Dict[str, List[str]]:
    """Cells of the "Subagents by role" block, by row label (the label itself dropped)."""
    lines = text.splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith("Subagents by role"))
    rows: Dict[str, List[str]] = {}
    for line in lines[start + 1 :]:
        if not line.strip():
            break
        cells = line.split()
        if cells[0] in ("implement", "review", "doc-review", "unclassified", "TOTAL"):
            rows[cells[0]] = cells[1:]
    return rows


def _json(directory: pathlib.Path) -> Dict[str, Any]:
    return json.loads(tm.format_json(tm.build_token_report(directory)))


def test_cost_and_subagents_are_serialized_without_the_tier_fields(
    pinned_dir: pathlib.Path, subagent_dir: pathlib.Path
) -> None:
    """The JSON gains keys (cost, subagents) and keeps every old one; the tier split stays internal."""
    for directory in (pinned_dir, subagent_dir):
        report = tm.build_token_report(directory)
        rendered = tm.format_text(report) + tm.format_json(report)
        assert "equivalent_cost" in rendered
        for needle in ("cache_write_5m_tokens", "cache_write_1h_tokens"):
            assert needle not in rendered
        for session in [*report.sessions, report.totals]:
            assert "cache_write_5m_tokens" not in session.to_dict()
            assert "cache_write_1h_tokens" not in session.to_dict()

    data = _json(pinned_dir)
    assert _LEGACY_REPORT_KEYS <= set(data)
    for session in data["sessions"]:
        assert set(session) == _LEGACY_SESSION_KEYS | {"equivalent_cost", "subagents"}
        assert session["subagents"] == []
    # The totals row is the main thread only: its subagents live at the report level.
    assert set(data["totals"]) == _LEGACY_SESSION_KEYS | {"equivalent_cost"}
    assert data["totals"]["total_input_tokens"] == 3120  # unchanged, pinned


def test_json_report_level_subagent_and_cost_keys(subagent_dir: pathlib.Path) -> None:
    data = _json(subagent_dir)
    assert set(data) == _LEGACY_REPORT_KEYS | {
        "subagent_totals",
        "subagents_by_role",
        "unclassified_subagents",
        "unclassified_share",  # spec 0031 T010
        "total_equivalent_cost",
        "cost_model",
        "context_distribution",  # spec 0031 T004
        "top_sessions",
        "model_shares",
        "subagent_share",
    }

    # main thread: 1.0*15 + 1.25*100 + 0.1*100 + 5.0*150
    assert data["sessions"][0]["equivalent_cost"] == data["totals"]["equivalent_cost"] == 900.0
    assert data["sessions"][0]["turns"] == 2  # main thread only, as before

    usage = {"turns": 4, "input_tokens": 10, "cache_creation_tokens": 250, "cache_read_tokens": 500, "output_tokens": 100}
    assert data["subagent_totals"] == {"agents": 2, "equivalent_cost": 872.5, **usage}
    assert data["total_equivalent_cost"] == 900.0 + 872.5

    by_role = data["subagents_by_role"]
    assert set(by_role) == {"implement", "review", "doc-review", "unclassified"}  # JSON keys are sorted
    assert by_role["implement"] == {
        "agents": 1,
        "turns": 2,
        "input_tokens": 5,
        "cache_creation_tokens": 200,
        "cache_read_tokens": 200,
        "output_tokens": 50,
        "equivalent_cost": 525.0,
    }
    assert by_role["review"]["agents"] == 1 and by_role["review"]["equivalent_cost"] == 347.5
    assert by_role["doc-review"]["agents"] == 0 and by_role["doc-review"]["equivalent_cost"] == 0
    assert by_role["unclassified"]["agents"] == 0 and by_role["unclassified"]["equivalent_cost"] == 0
    assert data["unclassified_subagents"] == 0

    agents = {a["agent_id"]: a for a in data["sessions"][0]["subagents"]}
    assert sorted(agents) == ["aaa", "bbb"]
    assert set(agents["aaa"]) == _SUBAGENT_JSON_KEYS
    assert agents["aaa"]["role"] == "implement" and agents["bbb"]["role"] == "review"
    assert agents["aaa"]["equivalent_cost"] == 525.0  # 1.0*5 + 1.25*200 + 0.1*200 + 5.0*50
    assert agents["bbb"]["equivalent_cost"] == 347.5  # 1.0*5 + 1.25*50 + 0.1*300 + 5.0*50


def test_json_declares_the_cost_as_an_approximation_with_its_weights(subagent_dir: pathlib.Path) -> None:
    model = _json(subagent_dir)["cost_model"]
    assert model["approximation"] is True
    assert model["unit"] == "equivalent_input_tokens"
    assert model["weights"] == {
        "input": tm.WEIGHT_INPUT,
        "output": tm.WEIGHT_OUTPUT,
        "cache_read": tm.WEIGHT_CACHE_READ,
        "cache_write_5m": tm.WEIGHT_CACHE_WRITE_5M,
        "cache_write_1h": tm.WEIGHT_CACHE_WRITE_1H,
    }


def test_json_by_role_sums_to_the_subagent_totals_across_sessions(tmp_path: pathlib.Path) -> None:
    for session, started in (("s1", "2026-09-16T10:00:00.000Z"), ("s2", "2026-09-17T10:00:00.000Z")):
        _write_transcript(
            tmp_path / f"{session}.jsonl", [_assistant(started, message_id=f"msg_{session}", output=1)]
        )
        for agent in ("a", "b"):
            _write_agent(
                tmp_path,
                session,
                f"agent-{agent}.jsonl",
                [_assistant(started, message_id=f"msg_{session}_{agent}", output=3, inp=2)],
            )
    _write_meta(tmp_path, "a", {"description": "implement: T001"}, session="s1")
    _write_meta(tmp_path, "b", {"description": "review: branch"}, session="s1")
    _write_meta(tmp_path, "a", {"description": "implement: T002"}, session="s2")
    _write_meta(tmp_path, "b", {"description": "no convention"}, session="s2")

    data = _json(tmp_path)
    by_role = data["subagents_by_role"]
    assert {role: by_role[role]["agents"] for role in by_role} == {
        "implement": 2,
        "review": 1,
        "doc-review": 0,
        "unclassified": 1,
    }
    assert data["unclassified_subagents"] == 1
    for field in ("agents", "turns", "input_tokens", "output_tokens", "equivalent_cost"):
        assert sum(r[field] for r in by_role.values()) == pytest.approx(data["subagent_totals"][field])
    assert data["subagent_totals"]["agents"] == 4
    assert data["total_equivalent_cost"] == pytest.approx(
        data["totals"]["equivalent_cost"] + data["subagent_totals"]["equivalent_cost"]
    )


def test_text_separates_the_main_thread_from_the_subagents_by_role(subagent_dir: pathlib.Path) -> None:
    text = tm.format_text(tm.build_token_report(subagent_dir))

    # What the pinned format already had is still there, and still the main thread only.
    assert "Sessions: 1" in text
    assert "tool_chars" in text
    assert "Total input tokens (input + cache_w + cache_r): 215" in text  # 15 + 100 + 100
    main_total = next(line for line in text.splitlines() if line.startswith("TOTAL")).split()
    assert main_total[1:] == ["2", "15", "100", "100", "150", "1", "2"]  # turns, tokens, tools, tool_chars

    # The subagents come apart by role: agents, turns, input, cache_w, cache_r, output, cost.
    assert "Subagents by role" in text
    rows = _role_rows(text)
    assert rows["implement"] == ["1", "2", "5", "200", "200", "50", "525.00"]
    assert rows["review"] == ["1", "2", "5", "50", "300", "50", "347.50"]
    assert rows["unclassified"] == ["0", "0", "0", "0", "0", "0", "0.00"]
    assert rows["TOTAL"] == ["2", "4", "10", "250", "500", "100", "872.50"]
    assert "Unclassified subagents: 0" in text

    # Main thread, subagents and the sum are three different numbers.
    assert "main thread 900.00" in text
    assert "subagents 872.50" in text
    assert "total 1,772.50" in text
    assert "Top tools by result chars" in text and "Bash" in text


def test_text_has_no_misleading_sidechain_line_and_says_subagents_are_separate(
    subagent_dir: pathlib.Path, pinned_dir: pathlib.Path
) -> None:
    text = tm.format_text(tm.build_token_report(subagent_dir))
    assert "Subagent (sidechain) turns included" not in text  # subagent turns are not in the TOTAL row
    (line,) = [ln for ln in text.splitlines() if ln.startswith("Subagent turns:")]
    assert "Subagent turns: 4 " in line and "reported separately" in line

    # A legacy main transcript that flags its own turns as sidechain still counts them in the TOTAL.
    legacy = tm.format_text(tm.build_token_report(pinned_dir))
    assert "Subagent (sidechain) turns included" not in legacy
    assert "Subagent turns:" not in legacy
    (note,) = [ln for ln in legacy.splitlines() if "Sidechain-flagged" in ln]
    assert "included in TOTAL" in note and note.rstrip().endswith("1")


def test_text_declares_the_cost_an_approximation_and_states_the_weights(subagent_dir: pathlib.Path) -> None:
    text = tm.format_text(tm.build_token_report(subagent_dir))
    assert "approximation" in text
    for needle in ("cache read 0.1x", "input 1.0x", "output 5.0x", "cache write 1.25x (5 min)", "2.0x (1 h)"):
        assert needle in text


def test_text_weights_come_from_the_constants_not_from_literals(
    subagent_dir: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(tm, "WEIGHT_OUTPUT", 7.5)
    monkeypatch.setattr(tm, "WEIGHT_CACHE_WRITE_1H", 3.0)
    report = tm.build_token_report(subagent_dir)
    text = tm.format_text(report)
    assert "output 7.5x" in text and "3.0x (1 h)" in text
    assert "output 5.0x" not in text and "2.0x (1 h)" not in text
    weights = json.loads(tm.format_json(report))["cost_model"]["weights"]
    assert weights["output"] == 7.5 and weights["cache_write_1h"] == 3.0


def test_unclassified_row_is_not_fed_by_the_subagent_totals_pseudo_agent(tmp_path: pathlib.Path) -> None:
    """Only classified subagents exist: the TOTAL pseudo-agent's default role must not feed a row."""
    _session_with_agents(tmp_path, ["a", "b"])
    _write_meta(tmp_path, "a", {"description": "implement: T001"})
    _write_meta(tmp_path, "b", {"description": "review: T001"})
    report = tm.build_token_report(tmp_path)
    rows = _role_rows(tm.format_text(report))
    assert rows["implement"][0] == "1" and rows["review"][0] == "1"
    assert rows["unclassified"][0] == "0" and rows["unclassified"][1] == "0"
    assert rows["TOTAL"][0] == "2"
    assert report.to_dict()["subagents_by_role"]["unclassified"]["agents"] == 0
    assert report.to_dict()["unclassified_subagents"] == 0


def test_text_counts_unclassified_subagents_and_never_prints_the_description(tmp_path: pathlib.Path) -> None:
    _session_with_agents(tmp_path, ["a", "b", "c", "d"])
    _write_meta(tmp_path, "a", {"description": "implement: T001 d3scr1pt10n-secret"})
    _write_meta(tmp_path, "b", {"description": "Explore the repo d3scr1pt10n-secret"})
    _write_meta(tmp_path, "c", "{not json")
    # "d" has no meta.json at all
    text = tm.format_text(tm.build_token_report(tmp_path))
    assert "Unclassified subagents: 3" in text
    assert _role_rows(text)["unclassified"][0] == "3"
    assert "d3scr1pt10n-secret" not in text + tm.format_json(tm.build_token_report(tmp_path))


def test_report_without_subagents_says_zero_unclassified_and_still_has_the_cost_note(
    pinned_dir: pathlib.Path,
) -> None:
    text = tm.format_text(tm.build_token_report(pinned_dir))
    assert "Unclassified subagents: 0" in text
    assert _role_rows(text)["TOTAL"] == ["0", "0", "0", "0", "0", "0", "0.00"]
    assert "main thread 2,105.00" in text  # s1 1970 + s2 135
    assert "approximation" in text


def test_tool_result_bodies_stay_out_of_text_and_json(subagent_dir: pathlib.Path, pinned_dir: pathlib.Path) -> None:
    for directory, secret in ((subagent_dir, "subagent-secret-body"), (pinned_dir, "aaaaaaaaaa")):
        report = tm.build_token_report(directory)
        for rendered in (tm.format_text(report), tm.format_json(report), repr(report.to_dict())):
            assert secret not in rendered


def test_cli_tokens_text_and_json_report_subagents_by_role(subagent_dir: pathlib.Path) -> None:
    runner = CliRunner()
    text = runner.invoke(main, ["metrics", "--tokens", "--transcripts-dir", str(subagent_dir)])
    assert text.exit_code == 0, text.output
    assert "Subagents by role" in text.output and "approximation" in text.output
    assert _role_rows(text.output)["implement"][0] == "1"

    a = runner.invoke(
        main, ["metrics", "--tokens", "--transcripts-dir", str(subagent_dir), "--format", "json"]
    )
    b = runner.invoke(
        main, ["metrics", "--tokens", "--transcripts-dir", str(subagent_dir), "--format", "json"]
    )
    assert a.exit_code == 0, a.output
    assert a.output == b.output  # still byte-stable
    data = json.loads(a.output)
    assert data["subagents_by_role"]["review"]["agents"] == 1
    assert data["cost_model"]["approximation"] is True
    assert data["totals"]["total_input_tokens"] == 215  # the old keys keep their meaning


def test_cli_tokens_reports_unclassified_without_error_for_a_broken_meta_json(tmp_path: pathlib.Path) -> None:
    """Story 1 sc3: no ``subagents/`` dir, or an unreadable ``*.meta.json``, exits 0 and counts."""
    _session_with_agents(tmp_path, ["a"])
    _write_meta(tmp_path, "a", "[" * 1000)
    runner = CliRunner()
    broken = runner.invoke(main, ["metrics", "--tokens", "--transcripts-dir", str(tmp_path)])
    assert broken.exit_code == 0, broken.output
    assert "Unclassified subagents: 1" in broken.output

    plain = tmp_path / "plain"
    _write_transcript(plain / "s.jsonl", [_assistant("2026-09-16T10:00:00.000Z", message_id="msg_M", output=1)])
    none = runner.invoke(main, ["metrics", "--tokens", "--transcripts-dir", str(plain)])
    assert none.exit_code == 0, none.output
    assert "Unclassified subagents: 0" in none.output


# ---------------------------------------------------------------------
# Carry-over from T003 — a line nested deeper than the interpreter limit
# ---------------------------------------------------------------------


@pytest.mark.parametrize(
    "poison",
    [
        "[" * 1_000_000,  # RecursionError in the C scanner
        '{"a":' * 200_000,  # the same, through objects
        '{"message": {"usage": {"output_tokens": 1' + "0" * 5000 + "}}}",  # ValueError: > 4300-digit int
    ],
    ids=["array-depth", "object-depth", "huge-int"],
)
def test_a_pathological_transcript_line_is_skipped_not_fatal(tmp_path: pathlib.Path, poison: str) -> None:
    good = [
        _assistant("2026-09-16T10:00:01.000Z", message_id="msg_A", output=10),
        _assistant("2026-09-16T10:00:03.000Z", message_id="msg_B", output=20),
    ]
    main_path = tmp_path / "s.jsonl"
    main_path.write_text(
        json.dumps(good[0]) + "\n" + poison + "\n" + json.dumps(good[1]) + "\n", encoding="utf-8"
    )
    agent = tmp_path / "s" / "subagents" / "agent-a.jsonl"
    agent.parent.mkdir(parents=True)
    agent.write_text(
        poison + "\n" + json.dumps(_assistant("2026-09-16T10:00:04.000Z", message_id="msg_C", output=5)) + "\n",
        encoding="utf-8",
    )

    session = tm.read_session(main_path)  # must not raise
    assert session.turns == 2 and session.output_tokens == 30
    report = tm.build_token_report(tmp_path)  # must not raise either
    assert report.totals.turns == 2
    assert [a.output_tokens for a in report.sessions[0].subagents] == [5]
    assert "Sessions: 1" in tm.format_text(report)


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


# ---------------------------------------------------------------------
# Quality review of T005 — implausible usage values, table alignment
# ---------------------------------------------------------------------

_MAX_PLAUSIBLE = 2**63 - 1  # a usage field at or above 2**63 is not a token count


@pytest.mark.parametrize(
    "huge",
    [10**308, 10**309, int("1" + "0" * 400), int("9" * 4299)],
    ids=["1e308", "1e309", "401-digits", "4299-digits"],
)
def test_an_implausibly_large_usage_value_counts_as_zero_and_never_aborts_the_report(
    tmp_path: pathlib.Path, huge: int
) -> None:
    """Below the 4300-digit parser limit but beyond float range: ``WEIGHT * huge`` raised OverflowError.

    Two 10**308 values are each convertible to float; their sum is not.
    """
    _write_transcript(
        tmp_path / "s.jsonl",
        [
            _assistant("2026-09-16T10:00:01.000Z", message_id="msg_A", output=7, inp=huge, cache_r=huge),
            _assistant("2026-09-16T10:00:02.000Z", message_id="msg_B", output=huge, inp=huge, cache_w=huge),
            _assistant("2026-09-16T10:00:03.000Z", message_id="msg_C", output=0, inp=3),
        ],
    )
    _write_agent(
        tmp_path,
        "s",
        "agent-a.jsonl",
        [
            _assistant("2026-09-16T10:00:04.000Z", message_id="msg_D", output=2, inp=huge),
            _assistant("2026-09-16T10:00:05.000Z", message_id="msg_E", output=huge, inp=huge),
        ],
    )
    report = tm.build_token_report(tmp_path)  # must not raise
    text = tm.format_text(report)  # nor must the formats, which read equivalent_cost
    data = json.loads(tm.format_json(report))

    main = report.sessions[0]
    assert main.turns == 3  # the message is still a turn; only the implausible field is dropped
    assert (main.input_tokens, main.cache_creation_tokens, main.cache_read_tokens, main.output_tokens) == (3, 0, 0, 7)
    assert main.equivalent_cost == 3 + 5 * 7
    (agent,) = main.subagents
    assert (agent.turns, agent.input_tokens, agent.output_tokens) == (2, 0, 2)
    assert data["totals"]["equivalent_cost"] == 38.0
    assert data["subagent_totals"]["equivalent_cost"] == 10.0
    assert data["total_equivalent_cost"] == 48.0
    assert "main thread 38.00" in text and "total 48.00" in text


@pytest.mark.parametrize(
    ("value", "counted"),
    [
        (_MAX_PLAUSIBLE, _MAX_PLAUSIBLE),  # the largest value that is still a token count
        (2**63, 0),
        (-1, 0),
        (-5, 0),
        (0, 0),
    ],
)
def test_usage_value_bounds(tmp_path: pathlib.Path, value: int, counted: int) -> None:
    path = _write_transcript(
        tmp_path / "s.jsonl", [_assistant("2026-09-16T10:00:01.000Z", message_id="msg_A", output=0, inp=value)]
    )
    session = tm.read_session(path)
    assert session.input_tokens == counted
    assert session.turns == 1
    assert session.equivalent_cost == pytest.approx(float(counted))  # finite: never an OverflowError


def test_the_tier_detail_goes_through_the_same_bound(tmp_path: pathlib.Path) -> None:
    event = _assistant(
        "2026-09-16T10:00:01.000Z",
        message_id="msg_A",
        output=0,
        cache_w=100,
        detail=_tiers(five_minute=10**400, one_hour=10**309),
    )
    path = _write_transcript(tmp_path / "s.jsonl", [event])
    session = tm.read_session(path)  # must not raise
    # both tier values are implausible -> 0; the 100 written tokens fall back to the 5-minute rate
    assert session.equivalent_cost == 125.0


def _numbers_by_end(line: str) -> List[int]:
    """Right edge (end offset) of every whitespace-separated cell of ``line``."""
    return [m.end() for m in re.finditer(r"\S+", line)]


def test_subagent_table_stays_aligned_with_large_sums(tmp_path: pathlib.Path) -> None:
    """Widths come from the cells: 12,345,678 / 98,765,432 / 1,234,567,890 must not push a column."""
    _write_transcript(
        tmp_path / "s.jsonl", [_assistant("2026-09-16T10:00:00.000Z", message_id="msg_M", output=1)]
    )
    _write_agent(
        tmp_path,
        "s",
        "agent-a.jsonl",
        [
            _assistant(
                "2026-09-16T10:00:01.000Z",
                message_id="msg_A",
                inp=12_345_678,
                cache_w=98_765_432,
                cache_r=1_234_567_890,
                output=123_456_789,
            )
        ],
    )
    _write_agent(
        tmp_path,
        "s",
        "agent-b.jsonl",
        [_assistant("2026-09-16T10:00:02.000Z", message_id="msg_B", inp=7, cache_w=3, cache_r=1, output=2)],
    )
    _write_meta(tmp_path, "a", {"description": "implement: T001"})
    _write_meta(tmp_path, "b", {"description": "review: T001"})
    text = tm.format_text(tm.build_token_report(tmp_path))

    lines = text.splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith("Subagents by role"))
    header, rule, *rows = lines[start + 1 : start + 1 + 8]  # header, rule, 4 roles, rule, TOTAL
    assert header.split() == ["role", "agents", "turns", "input", "cache_w", "cache_r", "output", "cost"]
    assert set(rule) == {"-"}
    data_rows = [row for row in rows if set(row) != {"-"}]
    assert [row.split()[0] for row in data_rows] == ["implement", "review", "doc-review", "unclassified", "TOTAL"]
    # Every line has the same length, and every right-aligned column ends where its header ends.
    assert len({len(line) for line in [header, rule, *rows]}) == 1
    header_ends = _numbers_by_end(header)
    for row in data_rows:
        assert len(row.split()) == 8
        assert _numbers_by_end(row)[1:] == header_ends[1:]
        assert not row.startswith(" ")  # the role label is flush left
    # And the big numbers are all there, comma-grouped.
    assert "12,345,678" in text and "98,765,432" in text and "1,234,567,890" in text and "123,456,789" in text


def test_a_role_outside_the_convention_is_counted_as_unclassified_once(tmp_path: pathlib.Path) -> None:
    """``by_role`` and ``unclassified_subagents`` have a single definition of 'unclassified'."""
    session = tm.SessionTokens(
        session_id="s",
        file="s.jsonl",
        subagents=[
            tm.SubagentTokens(agent_id="a", turns=1, output_tokens=4, role=tm.ROLE_IMPLEMENT),
            tm.SubagentTokens(agent_id="b", turns=1, output_tokens=6, role="explore"),  # not produced by the reader
            tm.SubagentTokens(agent_id="c", turns=1, output_tokens=8, role=tm.ROLE_UNCLASSIFIED),
        ],
    )
    report = tm.TokenReport(transcripts_dir=str(tmp_path), sessions=[session])
    assert report.unclassified_subagents == 2
    by_role = report.subagents_by_role
    assert by_role[tm.ROLE_UNCLASSIFIED].agents == 2 and by_role[tm.ROLE_UNCLASSIFIED].output_tokens == 14
    assert by_role[tm.ROLE_IMPLEMENT].agents == 1
    assert sum(r.agents for r in by_role.values()) == report.subagent_count == 3


def test_message_usage_context_excludes_output() -> None:
    usage = tm._MessageUsage(input_tokens=10, cache_creation_tokens=200, cache_read_tokens=3000, output_tokens=99999)
    assert usage.context == 3210


def test_message_usage_from_event_carries_model_and_defaults_to_empty() -> None:
    assert tm._MessageUsage.from_event({}, sidechain=False, model="claude-sonnet-5").model == "claude-sonnet-5"
    assert tm._MessageUsage.from_event({}, sidechain=False).model == ""


def test_message_usage_merged_keeps_last_non_empty_model_and_field_max() -> None:
    a = tm._MessageUsage(input_tokens=5, output_tokens=1, model="m-a")
    b = tm._MessageUsage(input_tokens=3, output_tokens=9, model="")
    c = tm._MessageUsage(input_tokens=1, model="m-c")
    assert a.merged(b).model == "m-a"
    assert a.merged(c).model == "m-c"
    merged = a.merged(b)
    assert (merged.input_tokens, merged.output_tokens) == (5, 9)


def test_message_usage_merged_keeps_sidechain_from_either_side() -> None:
    main = tm._MessageUsage(input_tokens=1, sidechain=False)
    side = tm._MessageUsage(input_tokens=1, sidechain=True)
    assert main.merged(side).sidechain is True
    assert side.merged(main).sidechain is True
    assert main.merged(main).sidechain is False


def test_read_transcript_passes_model_and_drops_synthetic(tmp_path: pathlib.Path) -> None:
    def line(mid: str, model: str) -> str:
        return json.dumps({"type": "assistant", "message": {"id": mid, "model": model, "usage": {"input_tokens": 1}}})

    path = tmp_path / "s.jsonl"
    path.write_text(line("a", "claude-opus-4") + "\n" + line("b", "<synthetic>") + "\n")
    _, messages = tm._read_transcript(path)
    assert messages["a"].model == "claude-opus-4"
    assert messages["b"].model == ""


@pytest.mark.parametrize(
    ("context", "band"),
    [
        (0, "<50k"),
        (30_000, "<50k"),
        (49_999, "<50k"),
        (50_000, "50k-150k"),
        (120_000, "50k-150k"),
        (149_999, "50k-150k"),
        (150_000, "150k-200k"),
        (200_000, "150k-200k"),
        (200_001, ">200k"),
        (250_000, ">200k"),
    ],
)
def test_context_band_boundaries(context: int, band: str) -> None:
    assert tm.context_band(context) == band
    assert band in tm.BANDS


# ---------------------------------------------------------------------
# Spec 0031 T002 — bands and models per session and per subagent
# ---------------------------------------------------------------------

def _ctx_event(ts: str, *, message_id: Optional[str], context: int, model: Optional[str] = "claude-opus-5",
               output: int = 1, **usage: int) -> Dict[str, Any]:
    event = _assistant(ts, message_id=message_id, output=output, cache_r=context)
    if model is None:
        del event["message"]["model"]
    else:
        event["message"]["model"] = model
    event["message"]["usage"].update(usage)
    return event


def _ts(i: int) -> str:
    return f"2026-09-16T10:00:{i:02d}.000Z"


def _zero() -> Dict[str, int]:
    return {band: 0 for band in tm.BANDS}


def test_session_counts_requests_and_context_tokens_per_band(tmp_path: pathlib.Path) -> None:
    contexts = [30_000, 50_000, 120_000, 150_000, 200_000, 250_000]
    _write_transcript(
        tmp_path / "s.jsonl",
        [_ctx_event(_ts(i), message_id=f"m{i}", context=c) for i, c in enumerate(contexts)],
    )
    s = tm.read_session(tmp_path / "s.jsonl")
    assert s.band_requests == {"<50k": 1, "50k-150k": 2, "150k-200k": 2, ">200k": 1}
    assert s.band_context_tokens == {
        "<50k": 30_000, "50k-150k": 170_000, "150k-200k": 350_000, ">200k": 250_000,
    }
    assert sum(s.band_context_tokens.values()) == s.total_input_tokens


def test_bands_start_at_zero_for_every_label_and_are_not_shared(tmp_path: pathlib.Path) -> None:
    _write_transcript(tmp_path / "s.jsonl", [_ctx_event(_ts(1), message_id="a", context=10)])
    a = tm.read_session(tmp_path / "s.jsonl")
    b = tm.SessionTokens(session_id="x", file="")
    assert b.band_requests == _zero() and b.band_context_tokens == _zero() and b.model_tokens == {}
    assert a.band_requests["<50k"] == 1 and b.band_requests["<50k"] == 0


def test_missing_model_counts_as_unknown_and_tokens_are_kept_per_model(tmp_path: pathlib.Path) -> None:
    _write_transcript(
        tmp_path / "s.jsonl",
        [
            _ctx_event(_ts(1), message_id="a", context=100, output=5),
            _ctx_event(_ts(2), message_id="b", context=200, output=7, model=None),
            _ctx_event(_ts(3), message_id="c", context=300, output=9, model="<synthetic>"),
        ],
    )
    s = tm.read_session(tmp_path / "s.jsonl")
    assert s.model_tokens == {"claude-opus-5": 100, "unknown": 200 + 300}
    assert s.models == ["claude-opus-5"]  # unchanged: only real model names


def test_streaming_partials_without_message_id_land_in_the_band_of_the_max(tmp_path: pathlib.Path) -> None:
    # Same request, three partials with growing usage, no id: each counts as its own event
    # (as today); with an id, they merge by field maximum and fall in the band of that maximum.
    events = [
        _ctx_event(_ts(1), message_id="m", context=10_000, output=1),
        _ctx_event(_ts(2), message_id="m", context=0, output=5, cache_creation_input_tokens=0, input_tokens=60_000),
        _ctx_event(_ts(3), message_id="m", context=120_000, output=9),
    ]
    _write_transcript(tmp_path / "s.jsonl", events)
    s = tm.read_session(tmp_path / "s.jsonl")
    assert s.turns == 1
    # max per field (cache_read 120k, input 60k) = 180k, not the last partial (120k) nor the first (10k)
    assert s.band_requests == {"<50k": 0, "50k-150k": 0, "150k-200k": 1, ">200k": 0}
    assert s.band_context_tokens["150k-200k"] == 180_000
    noid = [dict(e) for e in events]
    for e in noid:
        e["message"] = {k: v for k, v in e["message"].items() if k != "id"}
    _write_transcript(tmp_path / "t.jsonl", noid)
    t = tm.read_session(tmp_path / "t.jsonl")
    assert t.turns == 3 and sum(t.band_requests.values()) == 3


def test_partial_usage_without_id_does_not_raise(tmp_path: pathlib.Path) -> None:
    event = {"type": "assistant", "timestamp": _ts(1), "message": {"usage": {"output_tokens": 4}}}
    _write_transcript(tmp_path / "s.jsonl", [event])
    s = tm.read_session(tmp_path / "s.jsonl")
    assert s.band_requests["<50k"] == 1 and s.model_tokens == {"unknown": 0}


def test_subagent_keeps_its_own_bands_and_models(tmp_path: pathlib.Path) -> None:
    _write_transcript(tmp_path / "s.jsonl", [_ctx_event(_ts(1), message_id="main", context=60_000)])
    _write_agent(
        tmp_path, "s", "agent-a.jsonl",
        [
            _ctx_event(_ts(2), message_id="a1", context=10_000, model="claude-sonnet-5"),
            _ctx_event(_ts(3), message_id="a2", context=160_000, model="claude-sonnet-5"),
            _ctx_event(_ts(4), message_id="a3", context=250_000, model=None),
        ],
    )
    main = tm.read_session(tmp_path / "s.jsonl")
    (sub,) = main.subagents
    assert sub.band_requests == {"<50k": 1, "50k-150k": 0, "150k-200k": 1, ">200k": 1}
    assert sub.band_context_tokens == {"<50k": 10_000, "50k-150k": 0, "150k-200k": 160_000, ">200k": 250_000}
    assert sub.model_tokens == {"claude-sonnet-5": 10_000 + 160_000, "unknown": 250_000}
    assert main.band_requests == {"<50k": 0, "50k-150k": 1, "150k-200k": 0, ">200k": 0}  # main only


def test_message_shared_by_main_and_subagent_counts_once_as_main_and_bands_sum_to_totals() -> None:
    report = tm.build_token_report(FIXTURES / "shared_message")
    (main,) = report.sessions
    (sub,) = main.subagents
    # main claims SHARED (60,010) and MAIN (171,005); the subagent keeps SUB (30,002) and SUB2 (230,002)
    assert main.turns == 2 and sub.turns == 2
    assert main.band_requests == {"<50k": 0, "50k-150k": 1, "150k-200k": 1, ">200k": 0}
    assert sub.band_requests == {"<50k": 1, "50k-150k": 0, "150k-200k": 0, ">200k": 1}
    assert main.model_tokens == {"claude-opus-5": 60_010 + 171_005}
    assert sub.model_tokens == {"claude-sonnet-5": 30_002 + 230_002}
    both = report.totals.total_input_tokens + report.subagent_totals.total_input_tokens
    assert sum(main.band_context_tokens.values()) + sum(sub.band_context_tokens.values()) == both
    assert sum(main.band_requests.values()) + sum(sub.band_requests.values()) == (
        report.totals.turns + report.subagent_totals.turns
    ) == 4


def test_bands_and_models_are_not_serialized_yet(tmp_path: pathlib.Path) -> None:
    d = tm.build_token_report(FIXTURES / "shared_message").to_dict()
    for name in ("band_requests", "band_context_tokens", "model_tokens"):
        assert name not in d["totals"] and name not in d["sessions"][0]
        assert name not in d["sessions"][0]["subagents"][0]


# ---------------------------------------------------------------------
# Spec 0031 T003 — shares by band, subagent, model and session
# ---------------------------------------------------------------------

def _share_report(tmp_path: pathlib.Path) -> tm.TokenReport:
    """Five sessions, two models. Costs (0.1 per context token + 5 per request):
    B 55020 (cheap main, heavy sonnet subagents), A 20010, D 14010, C 12015 (main only), E 505."""
    n = iter(range(1, 60))

    def main(session: str, contexts: List[int]) -> None:
        _write_transcript(
            tmp_path / f"{session}.jsonl",
            [_ctx_event(_ts(next(n)), message_id=f"{session}{i}", context=c) for i, c in enumerate(contexts)],
        )

    def agent(session: str, contexts: List[int]) -> None:
        _write_agent(
            tmp_path, session, f"agent-{session}.jsonl",
            [_ctx_event(_ts(next(n)), message_id=f"{session}s{i}", context=c, model="claude-sonnet-5")
             for i, c in enumerate(contexts)],
        )

    main("A", [100_000, 100_000])
    main("B", [10_000])
    agent("B", [200_000, 300_000, 40_000])
    main("C", [40_000, 40_000, 40_000])
    main("D", [20_000])
    agent("D", [120_000])
    main("E", [5_000])
    return tm.build_token_report(tmp_path)


def test_band_distribution_all_requests_and_main_thread(tmp_path: pathlib.Path) -> None:
    r = _share_report(tmp_path)
    assert r.band_requests == {"<50k": 7, "50k-150k": 3, "150k-200k": 1, ">200k": 1}
    assert r.band_context_tokens == {
        "<50k": 195_000, "50k-150k": 320_000, "150k-200k": 200_000, ">200k": 300_000,
    }
    assert r.main_band_requests == {"<50k": 6, "50k-150k": 2, "150k-200k": 0, ">200k": 0}
    assert r.main_band_context_tokens == {
        "<50k": 155_000, "50k-150k": 200_000, "150k-200k": 0, ">200k": 0,
    }
    assert sum(r.band_context_tokens.values()) == r.totals.total_input_tokens + r.subagent_totals.total_input_tokens


def test_subagent_share_in_requests_and_tokens(tmp_path: pathlib.Path) -> None:
    share = _share_report(tmp_path).subagent_share
    assert share["requests"] == pytest.approx(4 / 12)
    assert share["tokens"] == pytest.approx(660_000 / 1_015_000)


def test_subagent_share_is_zero_without_subagents_or_sessions(tmp_path: pathlib.Path) -> None:
    _write_transcript(tmp_path / "s.jsonl", [_ctx_event(_ts(1), message_id="m", context=1_000)])
    assert tm.build_token_report(tmp_path).subagent_share == {"requests": 0.0, "tokens": 0.0}
    only_empty = tm.TokenReport(transcripts_dir="", sessions=[])
    assert only_empty.subagent_share == {"requests": 0.0, "tokens": 0.0}


def test_model_shares_sorted_summing_to_the_total(tmp_path: pathlib.Path) -> None:
    r = _share_report(tmp_path)
    shares = r.model_shares
    assert [(m["model"], m["tokens"]) for m in shares] == [
        ("claude-sonnet-5", 660_000), ("claude-opus-5", 355_000),
    ]
    assert shares[0]["share"] == pytest.approx(660_000 / 1_015_000)
    assert sum(m["tokens"] for m in shares) == r.totals.total_input_tokens + r.subagent_totals.total_input_tokens
    assert sum(m["share"] for m in shares) == pytest.approx(1.0, abs=1e-9)


def test_model_shares_tie_by_name_and_omit_zero_tokens() -> None:
    def session(sid: str, models: Dict[str, int]) -> tm.SessionTokens:
        return tm.SessionTokens(session_id=sid, file="", model_tokens=models)

    r = tm.TokenReport("", [session("a", {"zeta": 10, "alpha": 10, "idle": 0})])
    assert [m["model"] for m in r.model_shares] == ["alpha", "zeta"]


def test_top_sessions_count_subagent_cost_of_the_same_session(tmp_path: pathlib.Path) -> None:
    r = _share_report(tmp_path)
    assert r.total_equivalent_cost == 101_560.0
    top = r.top_sessions()
    assert [t["session_id"] for t in top] == ["B", "A", "D"]  # C (main only, 12015) falls out
    assert [t["cost"] for t in top] == [55_020.0, 20_010.0, 14_010.0]
    assert [t["share"] for t in top] == pytest.approx([55_020 / 101_560, 20_010 / 101_560, 14_010 / 101_560])
    assert [t["session_id"] for t in r.top_sessions(top=1)] == ["B"]


def test_top_sessions_tie_by_id_and_empty_report() -> None:
    def session(sid: str) -> tm.SessionTokens:
        return tm.SessionTokens(session_id=sid, file="", input_tokens=100)

    r = tm.TokenReport("", [session("z"), session("b"), session("m"), session("a")])
    assert [t["session_id"] for t in r.top_sessions()] == ["a", "b", "m"]
    empty = tm.TokenReport("", [])
    assert empty.top_sessions() == [] and empty.model_shares == []
    assert empty.band_requests == {band: 0 for band in tm.BANDS}
    assert empty.main_band_context_tokens == {band: 0 for band in tm.BANDS}


def test_top_sessions_with_zero_total_cost_does_not_divide_by_zero() -> None:
    report = tm.TokenReport("", [tm.SessionTokens("a", "a.jsonl")])
    assert report.top_sessions() == [{"session_id": "a", "cost": 0.0, "share": 0.0}]


# ---------------------------------------------------------------------
# Spec 0031 T004 — context report in text and JSON
# ---------------------------------------------------------------------

# JSON of ``with_subagents/`` produced before T004 (without ``transcripts_dir``).
_GOLDEN_BEFORE_T004 = json.loads(
    '{"cost_model": {"approximation": true, "unit": "equivalent_input_tokens", "weights": {"cache_read": 0.1, '
    '"cache_write_1h": 2.0, "cache_write_5m": 1.25, "input": 1.0, "output": 5.0}}, "sessions": [{"by_tool": '
    '{"Bash": {"calls": 1, "result_chars": 2}}, "cache_creation_tokens": 100, "cache_read_tokens": 100, '
    '"ended_at": "2026-10-01T10:00:09.000Z", "equivalent_cost": 900.0, "file": "sess-main.jsonl", '
    '"input_tokens": 15, "models": ["claude-opus-5"], "output_tokens": 150, "session_id": "sess-main", '
    '"sidechain_turns": 4, "started_at": "2026-10-01T10:00:00.000Z", "subagents": [{"agent_id": "aaa", '
    '"cache_creation_tokens": 200, "cache_read_tokens": 200, "equivalent_cost": 525.0, "input_tokens": 5, '
    '"output_tokens": 50, "role": "implement", "turns": 2}, {"agent_id": "bbb", "cache_creation_tokens": 50, '
    '"cache_read_tokens": 300, "equivalent_cost": 347.5, "input_tokens": 5, "output_tokens": 50, '
    '"role": "review", "turns": 2}], "tool_calls": 1, "tool_result_chars": 2, "total_input_tokens": 215, '
    '"turns": 2}], "subagent_totals": {"agents": 2, "cache_creation_tokens": 250, "cache_read_tokens": 500, '
    '"equivalent_cost": 872.5, "input_tokens": 10, "output_tokens": 100, "turns": 4}, "subagents_by_role": '
    '{"doc-review": {"agents": 0, "cache_creation_tokens": 0, "cache_read_tokens": 0, "equivalent_cost": 0.0, '
    '"input_tokens": 0, "output_tokens": 0, "turns": 0}, '
    '"implement": {"agents": 1, "cache_creation_tokens": 200, "cache_read_tokens": 200, "equivalent_cost": '
    '525.0, "input_tokens": 5, "output_tokens": 50, "turns": 2}, "review": {"agents": 1, '
    '"cache_creation_tokens": 50, "cache_read_tokens": 300, "equivalent_cost": 347.5, "input_tokens": 5, '
    '"output_tokens": 50, "turns": 2}, "unclassified": {"agents": 0, "cache_creation_tokens": 0, '
    '"cache_read_tokens": 0, "equivalent_cost": 0.0, "input_tokens": 0, "output_tokens": 0, "turns": 0}}, '
    '"total_equivalent_cost": 1772.5, "totals": {"by_tool": {"Bash": {"calls": 1, "result_chars": 2}}, '
    '"cache_creation_tokens": 100, "cache_read_tokens": 100, "ended_at": null, "equivalent_cost": 900.0, '
    '"file": "", "input_tokens": 15, "models": [], "output_tokens": 150, "session_id": "TOTAL", '
    '"sidechain_turns": 4, "started_at": null, "tool_calls": 1, "tool_result_chars": 2, '
    '"total_input_tokens": 215, "turns": 2}, "unclassified_subagents": 0}'
)
_NEW_KEYS = {"context_distribution", "top_sessions", "model_shares", "subagent_share", "unclassified_share"}


def test_json_keeps_every_previous_key_and_value_and_adds_the_context_keys(subagent_dir: pathlib.Path) -> None:
    d = json.loads(tm.format_json(tm.build_token_report(subagent_dir)))
    assert set(d) == set(_GOLDEN_BEFORE_T004) | _NEW_KEYS | {"transcripts_dir"}
    for key, value in _GOLDEN_BEFORE_T004.items():
        assert d[key] == value, key


def test_json_context_distribution_has_the_four_bands_always(tmp_path: pathlib.Path) -> None:
    d = json.loads(tm.format_json(_share_report(tmp_path)))
    assert d["context_distribution"] == {
        "all": {
            "requests": {"<50k": 7, "50k-150k": 3, "150k-200k": 1, ">200k": 1},
            "context_tokens": {"<50k": 195_000, "50k-150k": 320_000, "150k-200k": 200_000, ">200k": 300_000},
        },
        "main_thread": {
            "requests": {"<50k": 6, "50k-150k": 2, "150k-200k": 0, ">200k": 0},
            "context_tokens": {"<50k": 155_000, "50k-150k": 200_000, "150k-200k": 0, ">200k": 0},
        },
    }
    assert [t["session_id"] for t in d["top_sessions"]] == ["B", "A", "D"]
    assert [m["model"] for m in d["model_shares"]] == ["claude-sonnet-5", "claude-opus-5"]
    assert d["subagent_share"]["requests"] == pytest.approx(4 / 12)


def test_json_of_an_empty_report_still_has_the_bands_at_zero() -> None:
    d = json.loads(tm.format_json(tm.TokenReport("x", [])))
    zero = {band: 0 for band in tm.BANDS}
    assert d["context_distribution"] == {
        "all": {"requests": zero, "context_tokens": zero},
        "main_thread": {"requests": zero, "context_tokens": zero},
    }
    assert d["top_sessions"] == [] and d["model_shares"] == []
    assert d["subagent_share"] == {"requests": 0.0, "tokens": 0.0}


def test_text_has_the_four_context_sections_with_exact_numbers(tmp_path: pathlib.Path) -> None:
    text = tm.format_text(_share_report(tmp_path))
    lines = text.splitlines()
    start = next(i for i, ln in enumerate(lines) if ln.startswith("Context distribution (requests and context"))
    assert "size of each request's context" in lines[start]
    rows = {ln.split()[0]: ln.split()[1:] for ln in lines[start + 1:start + 12] if ln.split()[:1] and
            ln.split()[0] in (*tm.BANDS, "TOTAL")}
    assert rows == {
        "<50k": ["7", "195,000", "6", "155,000"],
        "50k-150k": ["3", "320,000", "2", "200,000"],
        "150k-200k": ["1", "200,000", "0", "0"],
        ">200k": ["1", "300,000", "0", "0"],
        "TOTAL": ["12", "1,015,000", "8", "355,000"],
    }
    top = lines.index("Top sessions by cost (equivalent cost, main thread plus its subagents):")
    assert lines[top + 1].split() == ["session", "cost", "share"]
    assert [ln.split() for ln in lines[top + 2:top + 5]] == [
        ["B", "55,020.00", "54.2%"], ["A", "20,010.00", "19.7%"], ["D", "14,010.00", "13.8%"],
    ]
    models = lines.index("Tokens by model:")
    assert lines[models + 1].split() == ["model", "tokens", "share"]
    assert [ln.split() for ln in lines[models + 2:models + 4]] == [
        ["claude-sonnet-5", "660,000", "65.0%"], ["claude-opus-5", "355,000", "35.0%"],
    ]
    assert "Subagent share: 33.3% of requests, 65.0% of tokens" in lines
    # what was there before stays, and the new sections sit before the tool table
    assert text.index("Equivalent cost (approximation)") < text.index("Context distribution")


def test_text_top_session_id_is_cut_at_eight_characters(tmp_path: pathlib.Path) -> None:
    _write_transcript(tmp_path / "0123456789abcdef.jsonl", [_ctx_event(_ts(1), message_id="m", context=10)])
    text = tm.format_text(tm.build_token_report(tmp_path))
    assert "  01234567 " in text and "012345678" not in text.split("Top sessions by cost")[1]


def test_text_context_bands_sum_to_the_requests_and_input_tokens(tmp_path: pathlib.Path) -> None:
    r = _share_report(tmp_path)
    total = next(ln.split() for ln in tm.format_text(r).splitlines() if ln.startswith("TOTAL") and "1,015,000" in ln)
    assert int(total[1]) == r.totals.turns + r.subagent_totals.turns
    assert int(total[2].replace(",", "")) == r.totals.total_input_tokens + r.subagent_totals.total_input_tokens


def test_text_without_sessions_or_subagents_does_not_break(tmp_path: pathlib.Path) -> None:
    empty = tm.format_text(tm.TokenReport("x", []))
    assert "Context distribution" in empty and "Subagent share: 0.0% of requests, 0.0% of tokens" in empty
    assert empty.count("  (none)") == 2, "top sessions and models both print (none)"
    _write_transcript(tmp_path / "s.jsonl", [_ctx_event(_ts(1), message_id="m", context=1_000)])
    text = tm.format_text(tm.build_token_report(tmp_path))
    assert "Subagent share: 0.0% of requests, 0.0% of tokens" in text


def test_text_top_sessions_and_models_have_headers_and_aligned_columns(tmp_path: pathlib.Path) -> None:
    text = tm.format_text(tm.build_token_report(FIXTURES / "with_subagents"))
    assert "  session" in text and "  model" in text
    rows = [ln for ln in text.splitlines() if ln.startswith("  ") and ln.rstrip().endswith("%")]
    widths = {len(ln) for ln in rows}
    assert len(widths) <= 2, "model rows share one width"


# ---------------------------------------------------------------------
# Spec 0031, Story 3 sc1-3 — doc-review role and the unclassified warning
# ---------------------------------------------------------------------


def _agents_report(tmp_path: pathlib.Path, descriptions: List[Any]) -> tm.TokenReport:
    """One equal-cost subagent per description (``None``: no meta.json)."""
    names = [f"a{i}" for i in range(len(descriptions))]
    _session_with_agents(tmp_path, names)
    for name, description in zip(names, descriptions):
        if description is not None:
            _write_meta(tmp_path, name, {"description": description})
    return tm.build_token_report(tmp_path)


def test_review_prefix_does_not_capture_doc_review_and_vice_versa(tmp_path: pathlib.Path) -> None:
    report = _agents_report(tmp_path, ["review: branch", "doc-review: spec 0031", "implement: T010"])
    assert [a.role for a in report.sessions[0].subagents] == ["review", "doc-review", "implement"]


def test_doc_review_row_in_text_and_json(tmp_path: pathlib.Path) -> None:
    report = _agents_report(tmp_path, ["doc-review: spec", "Doc-Review: plan x", "review: b"])
    rows = _role_rows(tm.format_text(report))
    assert rows["doc-review"][0] == "2" and rows["review"][0] == "1"
    by_role = report.to_dict()["subagents_by_role"]
    assert set(by_role) == {"implement", "review", "doc-review", "unclassified"}
    assert by_role["doc-review"]["agents"] == 2
    assert report.unclassified_subagents == 0


def test_warning_when_unclassified_cost_passes_30_percent(tmp_path: pathlib.Path) -> None:
    report = _agents_report(tmp_path, ["implement: a", None, None, None, None, None, None, None, None, None])
    text = tm.format_text(report)
    assert report.unclassified_share == pytest.approx(0.9)
    warnings = [line for line in text.splitlines() if line.startswith("Warning: unclassified subagents")]
    assert len(warnings) == 1
    assert "are 90% of" in warnings[0] and "threshold 30%" in warnings[0] and '"doc-review:"' in warnings[0]
    lines = text.splitlines()
    unclassified_line = next(i for i, line in enumerate(lines) if line.startswith("Unclassified subagents:"))
    assert lines[unclassified_line + 1] == warnings[0]
    assert report.to_dict()["unclassified_share"] == pytest.approx(0.9)


def test_warning_shows_the_share_as_a_rounded_percentage(tmp_path: pathlib.Path) -> None:
    report = _agents_report(tmp_path, ["implement: a", "review: b", "doc-review: c"] + [None] * 10)
    assert "are 77% of subagent cost" in tm.format_text(report)


def test_no_warning_at_exactly_30_percent(tmp_path: pathlib.Path) -> None:
    report = _agents_report(tmp_path, ["implement: a"] * 7 + [None] * 3)
    assert report.unclassified_share == 0.3
    assert "Warning:" not in tm.format_text(report)
    assert report.to_dict()["unclassified_share"] == 0.3


def test_no_warning_and_zero_share_without_subagents(pinned_dir: pathlib.Path) -> None:
    report = tm.build_token_report(pinned_dir)
    assert report.unclassified_share == 0.0
    assert "Warning:" not in tm.format_text(report)
    assert report.to_dict()["unclassified_share"] == 0.0


@pytest.mark.parametrize(
    ("path", "slug"),
    [
        ("/Users/a/Workspace/maycrm/.claude/worktrees/0183-x", "-Users-a-Workspace-maycrm--claude-worktrees-0183-x"),
        ("/Users/a/my.project/sub_dir", "-Users-a-my-project-sub-dir"),
        ("/Users/a/with space/x", "-Users-a-with-space-x"),
    ],
)
def test_slug_for_maps_every_non_alphanumeric_character(tmp_path: pathlib.Path, monkeypatch, path: str, slug: str) -> None:
    """Claude Code names the transcript directory after the cwd with every non-alphanumeric char as ``-``."""
    monkeypatch.setattr(pathlib.Path, "resolve", lambda self, *a, **k: self)
    assert tm.slug_for(pathlib.Path(path)) == slug
