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
