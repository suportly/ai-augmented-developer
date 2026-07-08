"""Tests for ``aiadev.metrics_format`` — pure projections over ``MetricsReport``.

Spec: ``specs/0015-aiadev-metrics/spec.md``.
"""

from __future__ import annotations

import datetime
import json
import pathlib

import pytest

from aiadev.metrics import build_report


FIXTURES_ROOT = pathlib.Path(__file__).parent / "fixtures" / "metrics"


def _ws(scenario: str) -> pathlib.Path:
    return FIXTURES_ROOT / scenario


# ---------------------------------------------------------------------
# T009 — format_text
# ---------------------------------------------------------------------


class TestFormatText:
    def test_pristine_output_includes_first_pass_block(self) -> None:
        from aiadev.metrics_format import format_text

        report = build_report(_ws("pristine_first_pass"), feature="0001-x")
        out = format_text(report)
        assert "Janela:" in out
        assert "code-reviewer" in out
        # 3/3 approved first pass.
        assert "3/3" in out

    def test_empty_log_yields_review_trail_empty_message(self) -> None:
        from aiadev.metrics_format import format_text

        report = build_report(_ws("empty_log"), feature="0003-empty")
        out = format_text(report)
        # spec.md Created 2026-05-20 — must be inside default 90d window
        # for current test date; use explicit feature= which bypasses window.
        assert "review trail: vazio" in out.lower() or "review trail vazio" in out.lower()

    def test_text_includes_disclaimer_lines(self) -> None:
        from aiadev.metrics_format import format_text

        report = build_report(_ws("pristine_first_pass"), feature="0001-x")
        out = format_text(report)
        # At least one disclaimer line ("NÃO implica" / "NÃO significa") must appear.
        assert "NÃO" in out

    def test_text_for_pre_cutoff_shows_zero_coverage(self) -> None:
        from aiadev.metrics_format import format_text

        report = build_report(_ws("pre_cutoff_no_log"), feature="0001-old")
        out = format_text(report)
        assert "coverage=0" in out or "coverage: 0" in out.lower()
        # Tasks block still shows totals despite missing trail.
        assert "done: 2" in out or "done=2" in out.lower()


# ---------------------------------------------------------------------
# T010 — format_json schema v1
# ---------------------------------------------------------------------


class TestFormatJson:
    def test_pristine_json_is_valid_and_has_schema_version(self) -> None:
        from aiadev.metrics_format import format_json

        report = build_report(_ws("pristine_first_pass"), feature="0001-x")
        out = format_json(report)
        data = json.loads(out)
        assert data["schema_version"] == 1

    def test_json_schema_keys_are_snake_case(self) -> None:
        from aiadev.metrics_format import format_json

        report = build_report(_ws("pristine_first_pass"), feature="0001-x")
        data = json.loads(format_json(report))

        # Top-level (schema-defined) keys are snake_case. Reviewer names
        # inside ``per_reviewer_first_pass_rate`` are *data values* —
        # the framework's canonical name is "code-reviewer" with a
        # hyphen, matching the JSONL ``reviewer`` field, so those are
        # exempt from the schema-style rule.
        for key in data.keys():
            assert key == key.lower(), f"top-level key not lowercase: {key}"
            assert "-" not in key, f"top-level key has hyphen: {key}"
        # Spot-check nested schema dicts (not enum-keyed maps).
        for key in data["window"].keys():
            assert "-" not in key
        for key in data["tasks_by_status"].keys():
            assert "-" not in key

    def test_json_does_not_include_execution_timestamp(self) -> None:
        from aiadev.metrics_format import format_json

        report = build_report(_ws("pristine_first_pass"), feature="0001-x")
        data = json.loads(format_json(report))
        # Determinismo histórico: nada na saída pode depender de "agora".
        # Only data-driven timestamps are allowed; we forbid top-level
        # ``generated_at`` or ``executed_at`` style fields.
        for forbidden in ("generated_at", "executed_at", "run_at", "now"):
            assert forbidden not in data, f"json must not include {forbidden}"

    def test_json_floats_rounded_to_one_decimal(self) -> None:
        from aiadev.metrics_format import format_json

        report = build_report(_ws("pristine_first_pass"), feature="0001-x")
        data = json.loads(format_json(report))
        # coverage_percent is a float — confirm 1-decimal precision.
        cov = data["coverage_percent"]
        assert isinstance(cov, float)
        # Either an integer-valued float (100.0) or has at most 1 decimal.
        assert abs(cov * 10 - round(cov * 10)) < 1e-9

    def test_json_deterministic_for_same_input(self) -> None:
        from aiadev.metrics_format import format_json

        # Story 2 sc3: same input → same output. Run twice, byte-compare.
        # ``now`` is pinned so the test does not depend on the wall clock.
        report1 = build_report(
            _ws("pristine_first_pass"),
            feature="0001-x",
            now=datetime.date(2026, 5, 28),
        )
        report2 = build_report(
            _ws("pristine_first_pass"),
            feature="0001-x",
            now=datetime.date(2026, 5, 28),
        )
        assert format_json(report1) == format_json(report2)

    def test_json_deterministic_across_today_changes_when_now_pinned(self, monkeypatch) -> None:
        """Story 2 sc3 + Success Criterion #4: determinism vs. wall clock.

        The earlier implementation read ``datetime.date.today()``
        directly inside ``build_report``, so the JSON ``window.until``
        field drifted as soon as the calendar rolled. The fix injects
        ``now`` as an explicit parameter; the CLI freezes it once per
        invocation. This test mutates ``date.today`` between two
        calls **with ``now`` pinned** and confirms output is identical.
        """
        from aiadev import metrics as _metrics_mod
        from aiadev.metrics_format import format_json

        class _FrozenDate(datetime.date):
            _today = datetime.date(2026, 5, 28)

            @classmethod
            def today(cls) -> datetime.date:
                return cls._today

        # First call: today=2026-05-28 (irrelevant — now pinned).
        monkeypatch.setattr(_metrics_mod.datetime, "date", _FrozenDate)
        r1 = build_report(
            _ws("pristine_first_pass"),
            feature="0001-x",
            now=datetime.date(2026, 5, 28),
        )
        out1 = format_json(r1)

        # Second call: pretend today is six months later. Output must
        # not move because ``now`` is still pinned.
        _FrozenDate._today = datetime.date(2026, 11, 28)
        r2 = build_report(
            _ws("pristine_first_pass"),
            feature="0001-x",
            now=datetime.date(2026, 5, 28),
        )
        out2 = format_json(r2)

        assert out1 == out2