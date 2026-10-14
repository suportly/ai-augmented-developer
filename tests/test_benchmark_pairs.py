"""T057 — benchmark harness: before/after pairs, median cost ratio, first-pass rule (spec 0030, SC #8)."""
from __future__ import annotations

import importlib.util
import json
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "benchmark_pairs.py"


@pytest.fixture(scope="module")
def bench():
    assert SCRIPT.is_file(), f"expected {SCRIPT} to exist"
    spec = importlib.util.spec_from_file_location("benchmark_pairs", SCRIPT)
    module = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def _session(path: pathlib.Path, sid: str, input_tokens: int) -> str:
    """One assistant message: cost = input_tokens * 1.0 (WEIGHT_INPUT)."""
    lines = [
        {"type": "user", "timestamp": "2026-09-15T10:00:00.000Z", "sessionId": sid,
         "message": {"role": "user", "content": "go"}},
        {"type": "assistant", "timestamp": "2026-09-15T10:00:01.000Z", "sessionId": sid,
         "message": {"id": f"m-{sid}", "model": "claude-opus-5",
                     "usage": {"input_tokens": input_tokens, "output_tokens": 0},
                     "content": [{"type": "text", "text": "ok"}]}},
    ]
    path.write_text("\n".join(json.dumps(x) for x in lines) + "\n", encoding="utf-8")
    return path.name


def _review_log(path: pathlib.Path, verdicts: list[str]) -> str:
    rows = [
        {"task_id": f"T{i:03d}", "reviewer": "code-reviewer", "verdict": v,
         "timestamp": f"2026-09-15T11:00:{i:02d}Z"}
        for i, v in enumerate(verdicts)
    ]
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    return path.name


def _pairs(tmp_path, costs, before_ok=10, after_ok=10, total=10):
    """costs: list of (before_cost, after_cost); the first pair's arms get two sessions."""
    pairs = []
    for i, (b, a) in enumerate(costs):
        arms = {}
        for arm, cost, ok in (("before", b, before_ok), ("after", a, after_ok)):
            if i == 0:  # split in two sessions: the sum must be per feature
                s1 = _session(tmp_path / f"{arm}{i}a.jsonl", f"{arm}{i}a", cost // 2)
                s2 = _session(tmp_path / f"{arm}{i}b.jsonl", f"{arm}{i}b", cost - cost // 2)
                sessions = [s1, s2]
            else:
                sessions = [_session(tmp_path / f"{arm}{i}.jsonl", f"{arm}{i}", cost)]
            log = ""
            if i == 0:  # reviews live in the first pair only
                log = _review_log(
                    tmp_path / f"{arm}.review.jsonl",
                    ["APPROVED"] * ok + ["CHANGES_REQUESTED"] * (total - ok),
                )
            arms[arm] = {"sessions": sessions, **({"review_log": log} if log else {})}
        pairs.append({"feature": f"f{i}", **arms})
    f = tmp_path / "pairs.json"
    f.write_text(json.dumps(pairs), encoding="utf-8")
    return f


def test_sums_cost_per_feature_over_all_sessions(bench, tmp_path):
    f = _pairs(tmp_path, [(1000, 500)] * 5)
    result = bench.evaluate(bench.load_pairs(f))
    first = result["pairs"][0]
    assert first["before_cost"] == 1000 and first["after_cost"] == 500
    assert first["ratio"] == 0.5


def test_median_odd_and_even(bench):
    assert bench.median([0.9, 0.5, 1.2]) == 0.9
    assert bench.median([0.5, 0.7, 0.9, 1.5]) == 0.8


def test_rule_passes(bench, tmp_path):
    f = _pairs(tmp_path, [(1000, 800)] * 5, before_ok=9, after_ok=9)
    result = bench.evaluate(bench.load_pairs(f))
    assert result["verdict"] == "PASS"
    assert result["median_ratio"] == 0.8
    assert result["first_pass"]["delta_pp"] == 0.0
    assert bench.main([str(f)]) == 0


def test_fails_on_ratio_at_or_above_one(bench, tmp_path):
    f = _pairs(tmp_path, [(1000, 1000)] * 5)
    assert bench.evaluate(bench.load_pairs(f))["verdict"] == "FAIL"
    assert bench.main([str(f)]) == 1


def test_fails_on_first_pass_drop_over_five_points(bench, tmp_path):
    f = _pairs(tmp_path, [(1000, 500)] * 5, before_ok=10, after_ok=9)  # -10 pp
    result = bench.evaluate(bench.load_pairs(f))
    assert result["first_pass"]["delta_pp"] == -10.0
    assert result["verdict"] == "FAIL"


def test_five_points_drop_exactly_passes(bench, tmp_path):
    f = _pairs(tmp_path, [(1000, 500)] * 5, before_ok=20, after_ok=19, total=20)  # -5 pp
    assert bench.evaluate(bench.load_pairs(f))["verdict"] == "PASS"


def test_insufficient_pairs(bench, tmp_path, capsys):
    f = _pairs(tmp_path, [(1000, 500)] * 4)
    assert bench.main([str(f)]) == 2
    assert "insufficient pairs" in capsys.readouterr().err
    assert bench.main([str(f), "--allow-fewer"]) == 0


def test_json_format(bench, tmp_path, capsys):
    f = _pairs(tmp_path, [(1000, 500)] * 5)
    assert bench.main([str(f), "--format", "json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["verdict"] == "PASS" and len(data["pairs"]) == 5


def test_missing_session_file_is_an_error(bench, tmp_path, capsys):
    f = _pairs(tmp_path, [(1000, 500)] * 5)
    (tmp_path / "before1.jsonl").unlink()
    assert bench.main([str(f)]) == 2
    assert "before1.jsonl" in capsys.readouterr().err
