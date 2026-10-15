"""``aiadev next`` — spec 0030 T029 (D6, Story 2 scenario 5)."""
from __future__ import annotations

import shutil
import time
from pathlib import Path

import pytest
from click.testing import CliRunner

from aiadev.cli import main

FIXTURES = Path(__file__).parent / "fixtures" / "pipeline_state"


def _run(ws: Path, monkeypatch: pytest.MonkeyPatch, *args: str):
    monkeypatch.chdir(ws)
    return CliRunner().invoke(main, ["next", *args])


def test_next_prints_state_and_next_step_for_feature(monkeypatch) -> None:
    result = _run(FIXTURES / "half_done", monkeypatch, "--feature", "0001-x")

    assert result.exit_code == 0, result.output
    out = result.output
    assert "0001-x" in out
    assert "spec: yes" in out
    assert "open markers: 0" in out
    assert "plan: yes" in out
    assert "tasks: 1/2 done, pending: 1" in out
    assert "/aia:implement" in out


def test_next_reports_open_markers(monkeypatch) -> None:
    result = _run(FIXTURES / "draft_spec", monkeypatch, "--feature", "0001-x")

    assert result.exit_code == 0
    assert "open markers: 1\n" in result.output
    assert "/aia:clarify" in result.output


def test_next_without_spec_recommends_specify_exit_0(monkeypatch) -> None:
    result = _run(FIXTURES / "planned", monkeypatch, "--feature", "0099-nope")

    assert result.exit_code == 0, result.output
    assert "spec: no" in result.output
    assert "/aia:specify" in result.output


def test_marker_without_cl_id_counts_and_agrees_with_preflight(tmp_path, monkeypatch) -> None:
    from aiadev.pipeline_state import recommend_next_command
    from aiadev.preflight import _count_needs_clarification

    ws = tmp_path / "ws"
    shutil.copytree(FIXTURES / "planned", ws)
    spec = ws / "specs" / "0001-x" / "spec.md"
    text = spec.read_text(encoding="utf-8") + "\n- [NEEDS CLARIFICATION: foo]\n"
    spec.write_text(text, encoding="utf-8")

    result = _run(ws, monkeypatch, "--feature", "0001-x")

    assert _count_needs_clarification(text) == 1
    assert "open markers: 1\n" in result.output
    assert "next: /aia:clarify" in result.output
    assert recommend_next_command(ws, feature="0001-x")["command"] == "/aia:clarify"


def test_next_without_feature_picks_most_recent_spec_like_recommend(
    tmp_path, monkeypatch
) -> None:
    import os

    from aiadev.pipeline_state import recommend_next_command

    ws = tmp_path / "ws"
    shutil.copytree(FIXTURES / "planned" / "specs" / "0001-x", ws / "specs" / "0001-a")
    shutil.copytree(FIXTURES / "draft_spec" / "specs" / "0001-x", ws / "specs" / "0002-b")
    os.utime(ws / "specs" / "0001-a", (1_000, 1_000))
    os.utime(ws / "specs" / "0002-b", (2_000, 2_000))

    result = _run(ws, monkeypatch)

    assert "feature: 0002-b" in result.output
    assert f"next: {recommend_next_command(ws)['command']}" in result.output
    assert "next: /aia:clarify" in result.output


def test_next_without_feature_uses_default_selection(monkeypatch) -> None:
    result = _run(FIXTURES / "planned", monkeypatch)

    assert result.exit_code == 0
    assert "/aia:tasks" in result.output


def test_next_stale_review_goes_to_code_review(tmp_path, monkeypatch) -> None:
    ws = tmp_path / "ws"
    shutil.copytree(FIXTURES / "review_yaml_stale", ws)
    (ws / ".aiadev").mkdir()
    shutil.copy(ws / "dot-aiadev" / "review.yaml", ws / ".aiadev" / "review.yaml")

    result = _run(ws, monkeypatch, "--feature", "0001-x")

    assert result.exit_code == 0
    assert "/aia:requesting-code-review" in result.output


def test_next_escapes_markup_from_files(tmp_path, monkeypatch) -> None:
    ws = tmp_path / "ws"
    spec = ws / "specs" / "0001-[bold]x"
    spec.mkdir(parents=True)
    result = _run(ws, monkeypatch, "--feature", "0001-[bold]x")

    assert result.exit_code == 0
    assert "0001-[bold]x" in result.output


def test_next_real_read_error_exits_2(tmp_path, monkeypatch) -> None:
    ws = tmp_path / "ws"
    spec = ws / "specs" / "0001-x"
    spec.mkdir(parents=True)
    (spec / "spec.md").write_text("# s\n", encoding="utf-8")
    spec.chmod(0)
    try:
        import os

        if os.access(spec, os.R_OK):
            pytest.skip("permissions not enforced")
        result = _run(ws, monkeypatch, "--feature", "0001-x")
    finally:
        spec.chmod(0o755)

    assert result.exit_code == 2, result.output


def test_next_within_200ms_on_fixtures(monkeypatch) -> None:
    monkeypatch.chdir(FIXTURES / "all_done")
    runner = CliRunner()
    start = time.perf_counter()
    result = runner.invoke(main, ["next", "--feature", "0001-x"])
    elapsed = time.perf_counter() - start

    assert result.exit_code == 0
    assert elapsed < 0.200, f"{elapsed * 1000:.1f} ms"


# --- spec 0031 T008: context lines -------------------------------------------------


def _usage_line(tokens: int) -> str:
    import json

    return json.dumps(
        {
            "type": "assistant",
            "message": {
                "id": f"m{tokens}",
                "role": "assistant",
                "usage": {
                    "input_tokens": 1,
                    "cache_creation_input_tokens": 0,
                    "cache_read_input_tokens": tokens - 1,
                },
            },
        }
    )


def _transcripts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, ws: Path
) -> Path:
    """Point HOME at tmp and return the transcript dir for ``ws``."""
    from aiadev.token_metrics import slug_for

    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("AIADEV_CONTEXT_WARN", raising=False)
    directory = home / ".claude" / "projects" / slug_for(ws)
    directory.mkdir(parents=True)
    return directory


def _session(directory: Path, name: str, tokens: int, age_s: int) -> Path:
    import os

    path = directory / f"{name}.jsonl"
    path.write_text(_usage_line(tokens) + "\n", encoding="utf-8")
    stamp = time.time() - age_s
    os.utime(path, (stamp, stamp))
    return path


def _ws(tmp_path: Path) -> Path:
    ws = tmp_path / "ws"
    shutil.copytree(FIXTURES / "all_done", ws)
    return ws


def test_next_prints_context_and_checkpoint_after_reason(tmp_path, monkeypatch) -> None:
    ws = _ws(tmp_path)
    _session(_transcripts(tmp_path, monkeypatch, ws), "abcdef123456", 412_000, 180)

    result = _run(ws, monkeypatch, "--feature", "0001-x")

    assert result.exit_code == 0, result.output
    lines = result.output.splitlines()
    ctx = [i for i, ln in enumerate(lines) if ln.startswith("context: ")]
    assert len(ctx) == 1
    assert lines[ctx[0]] == "context: 412k tokens (session abcdef12, 3 min ago)"
    assert lines[ctx[0] + 1].startswith("checkpoint:")
    reason = next(i for i, ln in enumerate(lines) if ln.startswith("reason:"))
    assert reason < ctx[0]


def test_next_below_threshold_only_context(tmp_path, monkeypatch) -> None:
    ws = _ws(tmp_path)
    _session(_transcripts(tmp_path, monkeypatch, ws), "s1", 100_000, 30)

    result = _run(ws, monkeypatch, "--feature", "0001-x")

    assert "context: 100k tokens" in result.output
    assert "checkpoint:" not in result.output


def test_next_warn_env_above_context_hides_checkpoint(tmp_path, monkeypatch) -> None:
    ws = _ws(tmp_path)
    _session(_transcripts(tmp_path, monkeypatch, ws), "s1", 412_000, 30)
    monkeypatch.setenv("AIADEV_CONTEXT_WARN", "500000")

    result = _run(ws, monkeypatch, "--feature", "0001-x")

    assert "context: 412k tokens" in result.output
    assert "checkpoint:" not in result.output


def test_next_without_transcript_output_unchanged(tmp_path, monkeypatch) -> None:
    ws = _ws(tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path / "empty-home"))
    baseline = _run(ws, monkeypatch, "--feature", "0001-x")

    directory = _transcripts(tmp_path, monkeypatch, ws)  # exists but empty
    assert not list(directory.iterdir())
    empty_dir = _run(ws, monkeypatch, "--feature", "0001-x")

    assert baseline.exit_code == empty_dir.exit_code == 0
    assert baseline.output == empty_dir.output
    assert "context:" not in baseline.output


def test_next_two_active_sessions_one_line_each(tmp_path, monkeypatch) -> None:
    ws = _ws(tmp_path)
    directory = _transcripts(tmp_path, monkeypatch, ws)
    _session(directory, "aaaaaaaa-big", 412_000, 60)
    _session(directory, "bbbbbbbb-small", 90_000, 120)

    result = _run(ws, monkeypatch, "--feature", "0001-x")

    lines = result.output.splitlines()
    assert sum(ln.startswith("context: ") for ln in lines) == 2
    assert sum(ln.startswith("checkpoint:") for ln in lines) == 1
    big = next(i for i, ln in enumerate(lines) if "412k" in ln)
    assert lines[big + 1].startswith("checkpoint:")


def test_next_escapes_markup_in_context_lines(tmp_path, monkeypatch) -> None:
    ws = _ws(tmp_path)
    _session(_transcripts(tmp_path, monkeypatch, ws), "[bold]x-session", 10_000, 5)

    result = _run(ws, monkeypatch, "--feature", "0001-x")

    assert "(session [bold]x-," in result.output


def test_next_50mb_transcript_within_200ms(tmp_path, monkeypatch) -> None:
    ws = _ws(tmp_path)
    path = _transcripts(tmp_path, monkeypatch, ws) / "big.jsonl"
    import json

    filler = (
        json.dumps({"type": "user", "message": {"role": "user", "content": [
            {"type": "tool_result", "content": "x" * 8000}]}}) + "\n"
    ).encode()
    block = filler * 128  # ~1 MB
    with path.open("wb") as fh:
        for _ in range(50):
            fh.write(block)
        fh.write((_usage_line(412_000) + "\n").encode())
    assert path.stat().st_size >= 50 * 10**6

    monkeypatch.chdir(ws)
    runner = CliRunner()
    start = time.perf_counter()
    result = runner.invoke(main, ["next", "--feature", "0001-x"])
    elapsed = time.perf_counter() - start
    print(f"50MB next: {elapsed * 1000:.1f} ms")

    assert result.exit_code == 0, result.output
    assert "context: 412k tokens" in result.output
    assert elapsed < 0.200, f"{elapsed * 1000:.1f} ms"


def test_next_deeply_nested_line_does_not_break(tmp_path, monkeypatch) -> None:
    ws = _ws(tmp_path)
    path = _session(_transcripts(tmp_path, monkeypatch, ws), "deep", 1, 5)
    path.write_text(
        _usage_line(200_000) + "\n" + "[" * 200_000 + "\n", encoding="utf-8"
    )

    result = _run(ws, monkeypatch, "--feature", "0001-x")

    assert result.exit_code == 0, result.output
    assert "context: 200k tokens" in result.output
