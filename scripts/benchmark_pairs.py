#!/usr/bin/env python3
"""Benchmark harness: before/after pairs of one micro-feature (spec 0030, SC #8).

Input is a JSON (or YAML) list of pairs; relative paths resolve against the
file's directory, absolute paths and ``~`` are accepted::

    [{"feature": "micro-1",
      "before": {"sessions": ["~/.claude/projects/<proj>/<id>.jsonl", ...],
                 "review_log": "runs/before-1.review-log.jsonl"},
      "after":  {"sessions": [...], "review_log": "..."}}, ...]

Per arm the cost is the sum of the equivalent cost (``aiadev.token_metrics``)
of every session, main thread plus subagents. First-pass approval is
approved-on-first-attempt / reviews over every reviewer of the arm
(``aiadev.metrics.first_pass_rate_by_reviewer``).

Rule (spec 0030): at least 5 pairs, the median of after/before cost ratios is
< 1.0 and the aggregate first-pass approval drops at most 5 percentage points.

Exit: 0 PASS, 1 FAIL, 2 invalid input (including fewer than 5 pairs).
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path
from typing import Any

MIN_PAIRS = 5
MAX_DROP_PP = 5.0


def _bootstrap_src() -> None:
    src = str(Path(__file__).resolve().parents[1] / "src")
    if src not in sys.path:
        sys.path.append(src)


def median(values: list[float]) -> float:
    return statistics.median(values)


def _resolve(base: Path, raw: Any) -> Path:
    if not isinstance(raw, str) or not raw:
        raise ValueError(f"invalid path entry: {raw!r}")
    p = Path(raw).expanduser()
    return p if p.is_absolute() else base / p


def load_pairs(path: Path) -> list[dict]:
    """Parse the pairs file into ``[{feature, before, after}]`` with absolute paths."""
    import yaml

    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ValueError(f"cannot read pairs file {path}: {exc}") from exc
    if not isinstance(data, list):
        raise ValueError("pairs file must hold a list of pairs")
    pairs = []
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            raise ValueError(f"pair #{i + 1} is not a mapping")
        pair: dict[str, Any] = {"feature": str(item.get("feature") or f"pair-{i + 1}")}
        for arm in ("before", "after"):
            body = item.get(arm)
            sessions = body.get("sessions") if isinstance(body, dict) else None
            if not isinstance(sessions, list) or not sessions:
                raise ValueError(f"pair {pair['feature']}: {arm}.sessions must be a non-empty list")
            log = body.get("review_log")
            pair[arm] = {
                "sessions": [_resolve(path.parent, s) for s in sessions],
                "review_log": _resolve(path.parent, log) if log else None,
            }
        pairs.append(pair)
    return pairs


def _arm_cost(sessions: list[Path]) -> float:
    from aiadev.token_metrics import read_session

    total = 0.0
    for p in dict.fromkeys(sessions):  # a session listed twice counts once
        if not p.is_file():
            raise ValueError(f"session file not found: {p}")
        s = read_session(p)
        total += s.equivalent_cost + sum(a.equivalent_cost for a in s.subagents)
    return round(total, 2)


def _arm_first_pass(logs: list[Path | None]) -> tuple[int, int]:
    from aiadev.metrics import first_pass_rate_by_reviewer, read_review_log

    approved = reviews = 0
    for log in logs:
        if log is None:
            continue
        if not log.is_file():
            raise ValueError(f"review log not found: {log}")
        try:
            rates = first_pass_rate_by_reviewer(read_review_log(log))
        except (KeyError, TypeError) as exc:
            raise ValueError(f"malformed review log {log}: missing {exc}") from exc
        approved += sum(a for a, _ in rates.values())
        reviews += sum(t for _, t in rates.values())
    return approved, reviews


def evaluate(pairs: list[dict]) -> dict:
    rows = []
    for pair in pairs:
        before = _arm_cost(pair["before"]["sessions"])
        after = _arm_cost(pair["after"]["sessions"])
        if before <= 0:
            raise ValueError(f"pair {pair['feature']}: before cost is zero")
        rows.append({
            "feature": pair["feature"],
            "before_cost": before,
            "after_cost": after,
            "ratio": round(after / before, 4),
        })
    fp = {}
    for arm in ("before", "after"):
        approved, reviews = _arm_first_pass([p[arm]["review_log"] for p in pairs])
        if reviews == 0:
            raise ValueError(f"no reviews in the {arm} arm: first-pass approval is undefined")
        fp[arm] = {"approved": approved, "reviews": reviews,
                   "rate_pct": round(100 * approved / reviews, 2)}
    fp["delta_pp"] = round(fp["after"]["rate_pct"] - fp["before"]["rate_pct"], 2)
    med = round(median([r["ratio"] for r in rows]), 4)
    ok = med < 1.0 and fp["delta_pp"] >= -MAX_DROP_PP
    return {"pairs": rows, "median_ratio": med, "first_pass": fp,
            "verdict": "PASS" if ok else "FAIL"}


def format_text(result: dict) -> str:
    lines = [f"{'feature':<24}{'before':>14}{'after':>14}{'ratio':>8}"]
    for r in result["pairs"]:
        lines.append(f"{r['feature']:<24}{r['before_cost']:>14,.2f}{r['after_cost']:>14,.2f}{r['ratio']:>8.4f}")
    fp = result["first_pass"]
    lines += [
        f"median ratio (after/before): {result['median_ratio']:.4f}  (rule: < 1.0)",
        f"first-pass before: {fp['before']['approved']}/{fp['before']['reviews']} = {fp['before']['rate_pct']}%",
        f"first-pass after:  {fp['after']['approved']}/{fp['after']['reviews']} = {fp['after']['rate_pct']}%",
        f"first-pass delta: {fp['delta_pp']:+.2f} pp  (rule: >= -{MAX_DROP_PP:g})",
        f"verdict: {result['verdict']}",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("pairs", type=Path, help="JSON/YAML file with the pairs")
    ap.add_argument("--format", choices=("text", "json"), default="text")
    ap.add_argument("--allow-fewer", action="store_true",
                    help=f"accept fewer than {MIN_PAIRS} pairs (exploratory run)")
    args = ap.parse_args(argv)
    _bootstrap_src()
    try:
        pairs = load_pairs(args.pairs)
        if len(pairs) < MIN_PAIRS and not args.allow_fewer:
            raise ValueError(f"insufficient pairs: {len(pairs)} < {MIN_PAIRS} (use --allow-fewer to explore)")
        result = evaluate(pairs)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2) if args.format == "json" else format_text(result))
    return 0 if result["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
