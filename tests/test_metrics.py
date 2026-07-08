"""Tests for ``aiadev.metrics`` — the core calculator module.

Spec: ``specs/0015-aiadev-metrics/spec.md``.

These tests run against the fixture trees built in T001
(``tests/fixtures/metrics/<scenario>/specs/``). Each test names which
scenario it exercises and which spec acceptance scenario it covers.
"""

from __future__ import annotations

import dataclasses
import datetime
import pathlib

import pytest


FIXTURES_ROOT = pathlib.Path(__file__).parent / "fixtures" / "metrics"


def _workspace(scenario: str) -> pathlib.Path:
    return FIXTURES_ROOT / scenario


# ---------------------------------------------------------------------
# T002 — MetricsReport dataclass + iter_specs_in_window + read_spec_header
# ---------------------------------------------------------------------


class TestMetricsReportShape:
    def test_metrics_report_is_frozen_dataclass_with_expected_fields(self) -> None:
        from aiadev.metrics import MetricsReport

        assert dataclasses.is_dataclass(MetricsReport)
        params = dataclasses.fields(MetricsReport)
        names = {f.name for f in params}
        # Fields locked in plan ADR / Phase 1 spec.
        for field in (
            "window",
            "n_specs_in_window",
            "coverage_percent",
            "per_reviewer_first_pass_rate",
            "tasks_by_status",
            "tasks_with_rework",
            "specify_to_last_commit_median_days",
            "unresolved_clarifications_count",
            "disclaimer_lines",
            "unknown_status_count",
        ):
            assert field in names, f"MetricsReport missing field: {field}"
        # Frozen: cannot mutate after construction.
        assert MetricsReport.__dataclass_params__.frozen is True


class TestIterSpecsInWindow:
    def test_iter_specs_filters_on_created_date(self) -> None:
        from aiadev.metrics import iter_specs_in_window

        ws = _workspace("pristine_first_pass")
        # The fixture spec was Created: 2026-05-10.
        in_window = list(
            iter_specs_in_window(
                ws,
                since=datetime.date(2026, 5, 1),
                until=datetime.date(2026, 5, 31),
            )
        )
        assert len(in_window) == 1

        out_of_window = list(
            iter_specs_in_window(
                ws,
                since=datetime.date(2025, 1, 1),
                until=datetime.date(2025, 12, 31),
            )
        )
        assert out_of_window == []

    def test_iter_specs_handles_workspace_without_specs_dir(self, tmp_path: pathlib.Path) -> None:
        from aiadev.metrics import iter_specs_in_window

        result = list(
            iter_specs_in_window(
                tmp_path,
                since=datetime.date(2026, 1, 1),
                until=datetime.date(2026, 12, 31),
            )
        )
        assert result == []


class TestReadSpecHeader:
    def test_reads_canonical_header(self) -> None:
        from aiadev.metrics import read_spec_header

        ws = _workspace("pristine_first_pass")
        spec_md = ws / "specs" / "0001-x" / "spec.md"
        h = read_spec_header(spec_md)
        assert h["spec_id"] == 11
        assert h["status"] == "Merged"
        assert h["created"] == datetime.date(2026, 5, 10)

    def test_tolerates_non_canonical_status_value(self) -> None:
        from aiadev.metrics import read_spec_header

        ws = _workspace("non_canonical_status")
        spec_md = ws / "specs" / "0004-pr-open" / "spec.md"
        h = read_spec_header(spec_md)
        # "PR Open" is outside the current canonical enum; bucket as "other".
        assert h["status"] == "other"
        # Raw value preserved for diagnostics.
        assert h["status_raw"] == "PR Open"

    def test_prefix_matches_decorated_canonical_status(self, tmp_path: pathlib.Path) -> None:
        # Real repo convention: merged specs decorate the Status with
        # provenance, e.g. "Merged — `ed0554f` (v0.19.0)" (see spec 0014).
        from aiadev.metrics import read_spec_header

        spec_md = tmp_path / "spec.md"
        spec_md.write_text(
            "**Created:** 2026-06-01\n"
            "**Status:** Merged — `ed0554f` (v0.19.0)\n"
            "**Spec ID:** 0014\n",
            encoding="utf-8",
        )
        h = read_spec_header(spec_md)
        assert h["status"] == "Merged"
        assert h["status_raw"].startswith("Merged —")

    def test_prefix_match_requires_word_boundary(self, tmp_path: pathlib.Path) -> None:
        # "Drafting" must NOT canonicalise to "Draft".
        from aiadev.metrics import read_spec_header

        spec_md = tmp_path / "spec.md"
        spec_md.write_text(
            "**Created:** 2026-06-01\n"
            "**Status:** Drafting\n"
            "**Spec ID:** 0042\n",
            encoding="utf-8",
        )
        h = read_spec_header(spec_md)
        assert h["status"] == "other"

    def test_raises_on_unparseable_spec_id(self, tmp_path: pathlib.Path) -> None:
        from aiadev.metrics import read_spec_header

        broken = tmp_path / "spec.md"
        broken.write_text("# missing required header fields\n", encoding="utf-8")
        with pytest.raises(ValueError):
            read_spec_header(broken)


# ---------------------------------------------------------------------
# T003 — read_review_log
# ---------------------------------------------------------------------


class TestReadReviewLog:
    def test_missing_file_returns_empty_list(self, tmp_path: pathlib.Path) -> None:
        from aiadev.metrics import read_review_log

        assert read_review_log(tmp_path / "nope.jsonl") == []

    def test_empty_file_returns_empty_list(self) -> None:
        from aiadev.metrics import read_review_log

        log = _workspace("empty_log") / "specs" / "0003-empty" / ".review-log.jsonl"
        assert read_review_log(log) == []

    def test_skips_blank_and_malformed_lines(self, tmp_path: pathlib.Path) -> None:
        from aiadev.metrics import read_review_log

        log = tmp_path / ".review-log.jsonl"
        log.write_text(
            "\n"
            '{"reviewer": "code-reviewer", "verdict": "APPROVED", "task_id": "T001", "timestamp": "2026-05-12T00:00:00Z", "has_why_no_issues_block": true}\n'
            "not-json-at-all\n"
            "\n"
            '{"reviewer": "code-reviewer", "verdict": "APPROVED", "task_id": "T002", "timestamp": "2026-05-13T00:00:00Z", "has_why_no_issues_block": true}\n',
            encoding="utf-8",
        )
        entries = read_review_log(log)
        assert len(entries) == 2
        assert entries[0]["task_id"] == "T001"
        assert entries[1]["task_id"] == "T002"

    def test_returns_entries_in_file_order(self) -> None:
        from aiadev.metrics import read_review_log

        log = _workspace("with_rework") / "specs" / "0002-y" / ".review-log.jsonl"
        entries = read_review_log(log)
        # Ordem do arquivo é determinística — o orquestrador escreve em ordem de dispatch.
        assert [e["timestamp"] for e in entries] == sorted(e["timestamp"] for e in entries)


# ---------------------------------------------------------------------
# T004 — first_pass_rate_by_reviewer (cl-6)
# ---------------------------------------------------------------------


class TestFirstPassRate:
    def test_pristine_all_approved_first_pass(self) -> None:
        from aiadev.metrics import first_pass_rate_by_reviewer, read_review_log

        entries = read_review_log(
            _workspace("pristine_first_pass") / "specs" / "0001-x" / ".review-log.jsonl"
        )
        rates = first_pass_rate_by_reviewer(entries)
        # 3 code-reviewer dispatches (T001/T002/T003), all APPROVED first pass.
        assert rates["code-reviewer"] == (3, 3)
        # 1 spec-document-reviewer dispatch, approved.
        assert rates["spec-document-reviewer"] == (1, 1)
        # 1 plan-document-reviewer dispatch, approved.
        assert rates["plan-document-reviewer"] == (1, 1)

    def test_with_rework_drops_code_reviewer_first_pass(self) -> None:
        from aiadev.metrics import first_pass_rate_by_reviewer, read_review_log

        entries = read_review_log(
            _workspace("with_rework") / "specs" / "0002-y" / ".review-log.jsonl"
        )
        rates = first_pass_rate_by_reviewer(entries)
        # 3 distinct (task, code-reviewer) pairs: T001 (approved 1st), T002 (CR 1st), T003 (approved 1st).
        # T002's first chronological entry is CHANGES_REQUESTED → not first-pass.
        approved, total = rates["code-reviewer"]
        assert total == 3
        assert approved == 2

    def test_groups_branch_review_by_reviewer_only(self) -> None:
        from aiadev.metrics import first_pass_rate_by_reviewer

        # Two branch-review entries for the same reviewer should collapse
        # to one (task_id, reviewer) pair when task_id == "branch-review".
        # (The fixture only has one branch-review entry per reviewer, so
        # we construct a synthetic case here.)
        entries = [
            {"reviewer": "spec-document-reviewer", "verdict": "CHANGES_REQUESTED", "task_id": "branch-review", "timestamp": "2026-05-01T00:00:00Z", "has_why_no_issues_block": False},
            {"reviewer": "spec-document-reviewer", "verdict": "APPROVED", "task_id": "branch-review", "timestamp": "2026-05-02T00:00:00Z", "has_why_no_issues_block": True},
        ]
        rates = first_pass_rate_by_reviewer(entries)
        # Single pair, first entry is CR → not first-pass approved.
        assert rates["spec-document-reviewer"] == (0, 1)

    def test_per_reviewer_type_isolated(self) -> None:
        from aiadev.metrics import first_pass_rate_by_reviewer

        entries = [
            {"reviewer": "code-reviewer", "verdict": "APPROVED", "task_id": "T001", "timestamp": "2026-05-01T00:00:00Z", "has_why_no_issues_block": True},
            {"reviewer": "spec-document-reviewer", "verdict": "CHANGES_REQUESTED", "task_id": "branch-review", "timestamp": "2026-05-02T00:00:00Z", "has_why_no_issues_block": False},
        ]
        rates = first_pass_rate_by_reviewer(entries)
        assert rates["code-reviewer"] == (1, 1)
        assert rates["spec-document-reviewer"] == (0, 1)


# ---------------------------------------------------------------------
# T005 — task_rework_counts
# ---------------------------------------------------------------------


class TestTaskReworkCounts:
    def test_with_rework_fixture_returns_t002_at_top(self) -> None:
        from aiadev.metrics import read_review_log, task_rework_counts

        entries = read_review_log(
            _workspace("with_rework") / "specs" / "0002-y" / ".review-log.jsonl"
        )
        rework = task_rework_counts(entries)
        # T002 has 3 code-reviewer rounds (CR, CR, APPROVED); T001 and T003
        # each have 1 round (APPROVED) — only T002 should appear.
        # Tuple shape: (task_id, rounds, changes_requested_count).
        assert rework == [("T002", 3, 2)]

    def test_pristine_fixture_has_no_rework(self) -> None:
        from aiadev.metrics import read_review_log, task_rework_counts

        entries = read_review_log(
            _workspace("pristine_first_pass") / "specs" / "0001-x" / ".review-log.jsonl"
        )
        assert task_rework_counts(entries) == []

    def test_only_counts_code_reviewer_entries(self) -> None:
        from aiadev.metrics import task_rework_counts

        # Spec-document reviewer rework on branch-review should be ignored
        # (rework counts are per-task, code review only).
        entries = [
            {"reviewer": "spec-document-reviewer", "verdict": "CHANGES_REQUESTED", "task_id": "branch-review", "timestamp": "2026-05-01T00:00:00Z", "has_why_no_issues_block": False},
            {"reviewer": "spec-document-reviewer", "verdict": "APPROVED", "task_id": "branch-review", "timestamp": "2026-05-02T00:00:00Z", "has_why_no_issues_block": True},
            {"reviewer": "code-reviewer", "verdict": "APPROVED", "task_id": "T001", "timestamp": "2026-05-03T00:00:00Z", "has_why_no_issues_block": True},
        ]
        assert task_rework_counts(entries) == []

    def test_sorts_descending_by_rounds(self) -> None:
        from aiadev.metrics import task_rework_counts

        # T005: 4 rounds (3 CR + 1 APPROVED), T003: 2 rounds (1 CR + 1 APPROVED).
        entries = [
            {"reviewer": "code-reviewer", "verdict": "CHANGES_REQUESTED", "task_id": "T003", "timestamp": "2026-05-01T00:00:00Z", "has_why_no_issues_block": False},
            {"reviewer": "code-reviewer", "verdict": "APPROVED", "task_id": "T003", "timestamp": "2026-05-02T00:00:00Z", "has_why_no_issues_block": True},
            {"reviewer": "code-reviewer", "verdict": "CHANGES_REQUESTED", "task_id": "T005", "timestamp": "2026-05-03T00:00:00Z", "has_why_no_issues_block": False},
            {"reviewer": "code-reviewer", "verdict": "CHANGES_REQUESTED", "task_id": "T005", "timestamp": "2026-05-04T00:00:00Z", "has_why_no_issues_block": False},
            {"reviewer": "code-reviewer", "verdict": "CHANGES_REQUESTED", "task_id": "T005", "timestamp": "2026-05-05T00:00:00Z", "has_why_no_issues_block": False},
            {"reviewer": "code-reviewer", "verdict": "APPROVED", "task_id": "T005", "timestamp": "2026-05-06T00:00:00Z", "has_why_no_issues_block": True},
        ]
        # Tuple shape: (task_id, total_rounds, changes_requested_count).
        assert task_rework_counts(entries) == [("T005", 4, 3), ("T003", 2, 1)]


class TestTasksReachedReview:
    def test_counts_distinct_task_ids_with_at_least_one_code_review(self) -> None:
        from aiadev.metrics import tasks_reached_review

        entries = [
            {"reviewer": "code-reviewer", "verdict": "APPROVED", "task_id": "T001", "timestamp": "2026-05-01T00:00:00Z", "has_why_no_issues_block": True},
            {"reviewer": "code-reviewer", "verdict": "CHANGES_REQUESTED", "task_id": "T002", "timestamp": "2026-05-02T00:00:00Z", "has_why_no_issues_block": False},
            {"reviewer": "code-reviewer", "verdict": "APPROVED", "task_id": "T002", "timestamp": "2026-05-03T00:00:00Z", "has_why_no_issues_block": True},
        ]
        assert tasks_reached_review(entries) == 2

    def test_ignores_branch_review_entries(self) -> None:
        from aiadev.metrics import tasks_reached_review

        entries = [
            {"reviewer": "code-reviewer", "verdict": "APPROVED", "task_id": "branch-review", "timestamp": "2026-05-01T00:00:00Z", "has_why_no_issues_block": True},
        ]
        assert tasks_reached_review(entries) == 0

    def test_ignores_non_code_reviewer_entries(self) -> None:
        from aiadev.metrics import tasks_reached_review

        entries = [
            {"reviewer": "spec-document-reviewer", "verdict": "APPROVED", "task_id": "T001", "timestamp": "2026-05-01T00:00:00Z", "has_why_no_issues_block": True},
        ]
        assert tasks_reached_review(entries) == 0


# ---------------------------------------------------------------------
# T006 — tasks_by_status integration
# ---------------------------------------------------------------------


class TestTasksByStatus:
    def test_counts_each_canonical_bucket(self) -> None:
        from aiadev.metrics import tasks_by_status

        ws = _workspace("empty_log")
        spec_dir = ws / "specs" / "0003-empty"
        # Fixture has T001 in_progress, T002 pending, T003 pending.
        counts = tasks_by_status(spec_dir)
        assert counts == {"pending": 2, "in_progress": 1, "blocked": 0, "done": 0}

    def test_missing_tasks_md_returns_all_zero(self, tmp_path: pathlib.Path) -> None:
        from aiadev.metrics import tasks_by_status

        counts = tasks_by_status(tmp_path)
        assert counts == {"pending": 0, "in_progress": 0, "blocked": 0, "done": 0}

    def test_pristine_fixture_all_done(self) -> None:
        from aiadev.metrics import tasks_by_status

        counts = tasks_by_status(_workspace("pristine_first_pass") / "specs" / "0001-x")
        assert counts == {"pending": 0, "in_progress": 0, "blocked": 0, "done": 3}


# ---------------------------------------------------------------------
# T007 — git-based metrics with injectable input
# ---------------------------------------------------------------------


class TestClarifyIterationCount:
    def test_counts_added_cl_markers_across_versions(self) -> None:
        from aiadev.metrics import clarify_iteration_count

        # Two commits: the first introduces cl-1 and cl-2; the second
        # resolves cl-1. The "iteration count" we care about is the
        # number of distinct cl-N ids ever introduced — that is the
        # number of clarify rounds the spec went through.
        git_log_output = (
            "commit aaa\n"
            "Author: x\n"
            "Date:   2026-05-01\n"
            "\n"
            "    initial spec\n"
            "\n"
            "diff --git a/specs/0015-aiadev-metrics/spec.md b/specs/0015-aiadev-metrics/spec.md\n"
            "+- [NEEDS CLARIFICATION:cl-1 ...]\n"
            "+- [NEEDS CLARIFICATION:cl-2 ...]\n"
            "\n"
            "commit bbb\n"
            "Author: x\n"
            "Date:   2026-05-02\n"
            "\n"
            "    resolve cl-1\n"
            "\n"
            "diff --git a/specs/0015-aiadev-metrics/spec.md b/specs/0015-aiadev-metrics/spec.md\n"
            "-- [NEEDS CLARIFICATION:cl-1 ...]\n"
        )
        assert clarify_iteration_count(15, git_log_output) == 2

    def test_unrelated_spec_id_returns_zero(self) -> None:
        from aiadev.metrics import clarify_iteration_count

        git_log_output = (
            "diff --git a/specs/0015-aiadev-metrics/spec.md b/specs/0015-aiadev-metrics/spec.md\n"
            "+- [NEEDS CLARIFICATION:cl-1 ...]\n"
        )
        # We're asking about spec 14, not 15.
        assert clarify_iteration_count(14, git_log_output) == 0

    def test_empty_output_returns_zero(self) -> None:
        from aiadev.metrics import clarify_iteration_count

        assert clarify_iteration_count(15, "") == 0


class TestSpecifyToLastCommitDays:
    def test_extracts_day_delta_from_log(self) -> None:
        from aiadev.metrics import specify_to_last_commit_days

        # The log lists commits newest-first (`git log` default).
        # First commit on spec.md → 2026-04-01; last commit on the spec
        # dir → 2026-04-15. Delta = 14 days.
        git_log_output = (
            "commit zzz\n"
            "Date:   2026-04-15\n"
            "\n"
            "    feat(0015): later change\n"
            "\n"
            "specs/0015-aiadev-metrics/plan.md\n"
            "\n"
            "commit aaa\n"
            "Date:   2026-04-01\n"
            "\n"
            "    feat(0015): create spec\n"
            "\n"
            "specs/0015-aiadev-metrics/spec.md\n"
        )
        result = specify_to_last_commit_days(15, git_log_output)
        assert result == 14

    def test_no_history_returns_none(self) -> None:
        from aiadev.metrics import specify_to_last_commit_days

        assert specify_to_last_commit_days(15, "") is None

    def test_indented_body_line_mentioning_path_does_not_trigger(self) -> None:
        """Regression: a commit body line mentioning ``specs/0001-x/…`` must NOT count as a touch.

        Earlier the parser stripped each line before the prefix test,
        so a 4-space-indented commit message body that referenced a
        spec path was conflated with a real ``--name-only`` row.
        Reviewer reproduced the bug against this repo's history.
        """
        from aiadev.metrics import specify_to_last_commit_days

        # commit body mentions specs/0001-x/... but only specs/0002-y/
        # is actually touched (flush-left under the message).
        git_log_output = (
            "commit aaa\n"
            "Author: x\n"
            "Date:   2026-04-01\n"
            "\n"
            "    feat(0002): unrelated spec touched\n"
            "    \n"
            "    See history of specs/0001-x/{spec.md} for context.\n"
            "\n"
            "specs/0002-y/spec.md\n"
        )
        # Spec 1 was only MENTIONED in the body, not touched.
        assert specify_to_last_commit_days(1, git_log_output) is None
        # Spec 2 WAS touched — sanity check the parser still finds it.
        assert specify_to_last_commit_days(2, git_log_output) == 0


# ---------------------------------------------------------------------
# T008 — build_report top-level composition
# ---------------------------------------------------------------------


class TestBuildReport:
    def test_single_feature_pristine_yields_full_first_pass(self) -> None:
        from aiadev.metrics import build_report

        report = build_report(
            _workspace("pristine_first_pass"),
            feature="0001-x",
        )
        assert report.n_specs_in_window == 1
        assert report.coverage_percent == 100.0
        # All 3 code-reviewer pairs APPROVED first pass.
        approved, total = report.per_reviewer_first_pass_rate["code-reviewer"]
        assert (approved, total) == (3, 3)
        # All 3 tasks done.
        assert report.tasks_by_status == {"pending": 0, "in_progress": 0, "blocked": 0, "done": 3}
        assert report.tasks_with_rework == []
        # Disclaimer lines must be non-empty (anti-Goodhart).
        assert len(report.disclaimer_lines) >= 1

    def test_single_feature_pre_cutoff_coverage_zero(self) -> None:
        from aiadev.metrics import build_report

        report = build_report(
            _workspace("pre_cutoff_no_log"),
            feature="0001-old",
        )
        assert report.n_specs_in_window == 1
        # No .review-log.jsonl → coverage 0%.
        assert report.coverage_percent == 0.0
        # No review entries → no per-reviewer data.
        assert report.per_reviewer_first_pass_rate == {}
        # Tasks count still works (cl-2 scenario from the spec).
        assert report.tasks_by_status["done"] == 2

    def test_aggregate_window_with_mixed_coverage(self) -> None:
        # A synthetic workspace combining pristine + pre-cutoff would
        # have 2 specs, 1 with log. We replicate the structure via tmp.
        from aiadev.metrics import build_report
        import shutil

        # Build a tiny workspace from two fixtures.
        from pathlib import Path
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            tmp_ws = Path(td)
            (tmp_ws / "specs").mkdir()
            shutil.copytree(
                _workspace("pristine_first_pass") / "specs" / "0001-x",
                tmp_ws / "specs" / "0011-pristine",
            )
            shutil.copytree(
                _workspace("pre_cutoff_no_log") / "specs" / "0001-old",
                tmp_ws / "specs" / "0009-legacy",
            )
            report = build_report(
                tmp_ws,
                since=datetime.date(2026, 1, 1),
                until=datetime.date(2026, 12, 31),
            )
        assert report.n_specs_in_window == 2
        # 1 of 2 has review log → 50%.
        assert report.coverage_percent == 50.0

    def test_window_excludes_specs_outside_dates(self) -> None:
        from aiadev.metrics import build_report

        # pristine fixture spec.md Created: 2026-05-10. Window before that.
        report = build_report(
            _workspace("pristine_first_pass"),
            since=datetime.date(2025, 1, 1),
            until=datetime.date(2025, 12, 31),
        )
        assert report.n_specs_in_window == 0
        assert report.coverage_percent == 0.0

    @staticmethod
    def _write_spec(
        ws: pathlib.Path,
        dirname: str,
        *,
        spec_id: int,
        status: str,
        entries: list[str] | None = None,
    ) -> None:
        spec_dir = ws / "specs" / dirname
        spec_dir.mkdir(parents=True)
        (spec_dir / "spec.md").write_text(
            f"**Created:** 2026-05-15\n"
            f"**Status:** {status}\n"
            f"**Spec ID:** {spec_id:04d}\n",
            encoding="utf-8",
        )
        if entries is not None:
            (spec_dir / ".review-log.jsonl").write_text(
                "".join(line + "\n" for line in entries), encoding="utf-8"
            )

    def test_aggregate_keeps_pairs_from_different_specs_distinct(
        self, tmp_path: pathlib.Path
    ) -> None:
        """Regression: pooling entries across specs collided ``(task_id,
        reviewer)`` pairs — two specs' T003 (or two branch-review
        sentinels) counted as ONE first attempt instead of two.
        """
        from aiadev.metrics import build_report

        self._write_spec(
            tmp_path,
            "0021-a",
            spec_id=21,
            status="Merged",
            entries=[
                '{"timestamp": "2026-05-16T10:00:00Z", "reviewer": "spec-reviewer", '
                '"verdict": "APPROVED", "has_why_no_issues_block": true, "task_id": "branch-review"}',
                '{"timestamp": "2026-05-16T11:00:00Z", "reviewer": "code-reviewer", '
                '"verdict": "APPROVED", "has_why_no_issues_block": true, "task_id": "T003"}',
            ],
        )
        self._write_spec(
            tmp_path,
            "0022-b",
            spec_id=22,
            status="Implemented",
            entries=[
                '{"timestamp": "2026-05-17T10:00:00Z", "reviewer": "spec-reviewer", '
                '"verdict": "APPROVED", "has_why_no_issues_block": true, "task_id": "branch-review"}',
                '{"timestamp": "2026-05-17T11:00:00Z", "reviewer": "code-reviewer", '
                '"verdict": "CHANGES_REQUESTED", "has_why_no_issues_block": false, "task_id": "T003"}',
                '{"timestamp": "2026-05-17T12:00:00Z", "reviewer": "code-reviewer", '
                '"verdict": "APPROVED", "has_why_no_issues_block": true, "task_id": "T003"}',
            ],
        )

        report = build_report(
            tmp_path,
            since=datetime.date(2026, 1, 1),
            until=datetime.date(2026, 12, 31),
        )
        # Two branch-review first attempts (one per spec), both approved.
        assert report.per_reviewer_first_pass_rate["spec-reviewer"] == (2, 2)
        # Two T003 first attempts: spec A approved, spec B changes-requested.
        assert report.per_reviewer_first_pass_rate["code-reviewer"] == (1, 2)
        # Rework rows are qualified by spec dir so they stay distinguishable.
        assert report.tasks_with_rework == [("0022-b/T003", 2, 1)]
        # T003 reached review in BOTH specs.
        assert report.tasks_reached_review == 2

    def test_aggregate_filters_to_implemented_or_merged(
        self, tmp_path: pathlib.Path
    ) -> None:
        """Spec success criterion 2: aggregate sample = Status in
        {Implemented, Merged}. Drafts drop silently; non-canonical
        statuses drop but are surfaced via ``unknown_status_count``.
        """
        from aiadev.metrics import build_report

        self._write_spec(tmp_path, "0031-merged", spec_id=31, status="Merged", entries=[])
        self._write_spec(tmp_path, "0032-draft", spec_id=32, status="Draft")
        self._write_spec(tmp_path, "0033-legacy", spec_id=33, status="PR Open — #34")

        report = build_report(
            tmp_path,
            since=datetime.date(2026, 1, 1),
            until=datetime.date(2026, 12, 31),
        )
        assert report.n_specs_in_window == 1
        assert report.coverage_percent == 100.0
        assert report.unknown_status_count == 1

    def test_feature_mode_bypasses_status_filter(self, tmp_path: pathlib.Path) -> None:
        from aiadev.metrics import build_report

        self._write_spec(tmp_path, "0032-draft", spec_id=32, status="Draft")
        report = build_report(tmp_path, feature="0032-draft")
        assert report.n_specs_in_window == 1
