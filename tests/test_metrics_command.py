"""Tests for ``aiadev metrics`` (Click subcommand layer).

Spec: ``specs/0015-aiadev-metrics/spec.md``.
"""

from __future__ import annotations

import json
import pathlib
import shutil

import pytest
from click.testing import CliRunner

from aiadev.cli import main


FIXTURES_ROOT = pathlib.Path(__file__).parent / "fixtures" / "metrics"


def _copy_workspace(scenario: str, dest: pathlib.Path) -> pathlib.Path:
    """Copy a fixture workspace into ``dest`` so the CLI has a real cwd."""
    shutil.copytree(FIXTURES_ROOT / scenario, dest / scenario)
    return dest / scenario


# ---------------------------------------------------------------------
# T011 — Subcommand registration + --feature
# ---------------------------------------------------------------------


class TestMetricsSubcommandRegistration:
    def test_metrics_is_registered(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["metrics", "--help"])
        assert result.exit_code == 0
        assert "Janela" in result.output or "metrics" in result.output.lower()

    def _run_in_workspace(
        self,
        fixture: str,
        args: list[str],
        tmp_path: pathlib.Path,
    ):
        """Copy the fixture into tmp_path, cd to it, and invoke the CLI."""
        ws = tmp_path / "wd"
        ws.mkdir()
        shutil.copytree(FIXTURES_ROOT / fixture / "specs", ws / "specs")
        runner = CliRunner()
        # CliRunner doesn't natively chdir; use os.chdir for the call.
        import os
        cwd_before = os.getcwd()
        os.chdir(ws)
        try:
            return runner.invoke(main, args), ws
        finally:
            os.chdir(cwd_before)

    def test_feature_pristine_exit_zero(self, tmp_path: pathlib.Path) -> None:
        result, _ = self._run_in_workspace(
            "pristine_first_pass", ["metrics", "--feature", "0001-x"], tmp_path
        )
        assert result.exit_code == 0, result.output
        assert "code-reviewer" in result.output

    def test_feature_pre_cutoff_exit_two(self, tmp_path: pathlib.Path) -> None:
        result, _ = self._run_in_workspace(
            "pre_cutoff_no_log", ["metrics", "--feature", "0001-old"], tmp_path
        )
        assert result.exit_code == 2, result.output
        # Mensagem cita o cutoff explicitamente (no stdout do format_text
        # ou no stderr injetado pelo CLI).
        combined = result.output + (result.stderr if result.stderr_bytes is not None else "")
        assert "0014" in combined or "cutoff" in combined.lower()

    def test_feature_empty_log_exit_zero(self, tmp_path: pathlib.Path) -> None:
        result, _ = self._run_in_workspace(
            "empty_log", ["metrics", "--feature", "0003-empty"], tmp_path
        )
        assert result.exit_code == 0, result.output
        assert "vazio" in result.output.lower()

    def test_feature_not_found_exit_one(self, tmp_path: pathlib.Path) -> None:
        result, _ = self._run_in_workspace(
            "pristine_first_pass", ["metrics", "--feature", "nonexistent"], tmp_path
        )
        assert result.exit_code == 1
        combined = result.output + (result.stderr if result.stderr_bytes is not None else "")
        assert "not found" in combined.lower() or "não encontrado" in combined.lower()

    def test_spec_id_12_without_log_exits_two(self, tmp_path: pathlib.Path) -> None:
        """Regression: spec id 0011-0013 predate 0014's .review-log.jsonl substrate.

        The earlier implementation used the spec-recon cutoff (10) here,
        so a spec with id 12 and no log incorrectly fell through to
        the "in-flight feature" branch (exit 0) instead of the
        "pre-cutoff legacy" branch (exit 2). cl-2 / Story 1 sc2 cares
        about the right boundary.
        """
        ws = tmp_path / "wd"
        spec_dir = ws / "specs" / "0012-vsc-explorer"
        spec_dir.mkdir(parents=True)
        (spec_dir / "spec.md").write_text(
            "**Branch:** `feature/legacy-12`\n"
            "**Created:** 2026-03-15\n"
            "**Status:** Implemented\n"
            "**Spec ID:** 0012\n",
            encoding="utf-8",
        )
        (spec_dir / "tasks.md").write_text(
            "### T001 — sample\n\n- **Status:** done\n", encoding="utf-8"
        )
        # No .review-log.jsonl — predates spec 0014's substrate.

        runner = CliRunner()
        import os
        cwd_before = os.getcwd()
        os.chdir(ws)
        try:
            result = runner.invoke(main, ["metrics", "--feature", "0012-vsc-explorer"])
        finally:
            os.chdir(cwd_before)
        assert result.exit_code == 2, result.output
        combined = result.output + (result.stderr if result.stderr_bytes is not None else "")
        assert "0014" in combined or "cutoff" in combined.lower()

    def test_post_cutoff_feature_without_log_exits_zero(self, tmp_path: pathlib.Path) -> None:
        """Post-cutoff feature that has not yet collected reviews must NOT trip exit 2.

        Story 1 sc3 in the spec: in-flight feature (post-0014, log
        absent or empty) reports "review trail: vazio" and exits 0.
        Regression guard against the earlier bug where any missing
        log triggered the pre-cutoff exit-2 branch.
        """
        ws = tmp_path / "wd"
        spec_dir = ws / "specs" / "0099-in-flight"
        spec_dir.mkdir(parents=True)
        (spec_dir / "spec.md").write_text(
            "**Branch:** `feature/in-flight`\n"
            "**Created:** 2026-05-01\n"
            "**Status:** Draft\n"
            "**Spec ID:** 0099\n",
            encoding="utf-8",
        )
        (spec_dir / "tasks.md").write_text(
            "### T001 — sample\n\n- **Status:** pending\n", encoding="utf-8"
        )
        # Deliberately no .review-log.jsonl.

        runner = CliRunner()
        import os
        cwd_before = os.getcwd()
        os.chdir(ws)
        try:
            result = runner.invoke(main, ["metrics", "--feature", "0099-in-flight"])
        finally:
            os.chdir(cwd_before)
        assert result.exit_code == 0, result.output
        assert "vazio" in result.output.lower()


# ---------------------------------------------------------------------
# T012 — --since + --format
# ---------------------------------------------------------------------


class TestMetricsSinceAndFormat:
    def _aggregate_run(self, fixture: str, extra_args: list[str], tmp_path: pathlib.Path):
        ws = tmp_path / "wd"
        ws.mkdir()
        shutil.copytree(FIXTURES_ROOT / fixture / "specs", ws / "specs")
        runner = CliRunner()
        import os
        cwd_before = os.getcwd()
        os.chdir(ws)
        try:
            return runner.invoke(main, ["metrics", *extra_args])
        finally:
            os.chdir(cwd_before)

    def test_since_filters_on_created(self, tmp_path: pathlib.Path) -> None:
        # pristine fixture Created 2026-05-10. Setting --since 2027-01-01
        # excludes it → exit 2.
        result = self._aggregate_run(
            "pristine_first_pass", ["--since", "2027-01-01"], tmp_path
        )
        assert result.exit_code == 2, result.output

    def test_format_json_emits_valid_json(self, tmp_path: pathlib.Path) -> None:
        result = self._aggregate_run(
            "pristine_first_pass",
            ["--feature", "0001-x", "--format", "json"],
            tmp_path,
        )
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert data["schema_version"] == 1
        assert data["n_specs_in_window"] == 1

    def test_text_output_shows_window_in_first_line(self, tmp_path: pathlib.Path) -> None:
        result = self._aggregate_run(
            "pristine_first_pass",
            ["--feature", "0001-x", "--since", "2026-01-01"],
            tmp_path,
        )
        assert result.exit_code == 0, result.output
        first_line = result.output.splitlines()[0]
        assert "Janela:" in first_line
        assert "2026-01-01" in first_line


# ---------------------------------------------------------------------
# T013 — --tasks + --show-bodies + exit codes
# ---------------------------------------------------------------------


class TestMetricsTasksAndBodies:
    def _run(self, fixture: str, args: list[str], tmp_path: pathlib.Path):
        ws = tmp_path / "wd"
        ws.mkdir()
        shutil.copytree(FIXTURES_ROOT / fixture / "specs", ws / "specs")
        runner = CliRunner()
        import os
        cwd_before = os.getcwd()
        os.chdir(ws)
        try:
            return runner.invoke(main, ["metrics", *args])
        finally:
            os.chdir(cwd_before)

    def test_tasks_lists_rework_descending(self, tmp_path: pathlib.Path) -> None:
        result = self._run(
            "with_rework", ["--feature", "0002-y", "--tasks"], tmp_path
        )
        assert result.exit_code == 0, result.output
        assert "T002" in result.output
        # Story 3 sc1 explicit wording.
        assert "3 review rounds (2 changes_requested → approved)" in result.output

    def test_tasks_emits_reached_review_header_when_partial(self, tmp_path: pathlib.Path) -> None:
        """Story 3 sc3: when not all tasks made it through code review,
        emit ``M/N tasks reached review`` so the reader sees the sample is partial.

        Build a synthetic feature: 4 tasks total, only T002 received any
        code-reviewer entries. Header must say ``1/4 tasks reached review``.
        """
        ws = tmp_path / "wd"
        spec_dir = ws / "specs" / "0050-partial"
        spec_dir.mkdir(parents=True)
        (spec_dir / "spec.md").write_text(
            "**Branch:** `feature/partial`\n**Created:** 2026-05-15\n"
            "**Status:** Draft\n**Spec ID:** 0050\n",
            encoding="utf-8",
        )
        (spec_dir / "tasks.md").write_text(
            "### T001 — a\n\n- **Status:** pending\n\n"
            "### T002 — b\n\n- **Status:** done\n\n"
            "### T003 — c\n\n- **Status:** pending\n\n"
            "### T004 — d\n\n- **Status:** pending\n",
            encoding="utf-8",
        )
        (spec_dir / ".review-log.jsonl").write_text(
            '{"timestamp": "2026-05-16T10:00:00Z", "reviewer": "code-reviewer", '
            '"verdict": "CHANGES_REQUESTED", "has_why_no_issues_block": false, '
            '"task_id": "T002", "note": "x"}\n'
            '{"timestamp": "2026-05-16T11:00:00Z", "reviewer": "code-reviewer", '
            '"verdict": "APPROVED", "has_why_no_issues_block": true, '
            '"task_id": "T002", "note": "ok"}\n',
            encoding="utf-8",
        )

        runner = CliRunner()
        import os
        cwd_before = os.getcwd()
        os.chdir(ws)
        try:
            result = runner.invoke(main, ["metrics", "--feature", "0050-partial", "--tasks"])
        finally:
            os.chdir(cwd_before)
        assert result.exit_code == 0, result.output
        assert "1/4 tasks reached review" in result.output

    def test_tasks_no_rework_yields_friendly_message(self, tmp_path: pathlib.Path) -> None:
        result = self._run(
            "pristine_first_pass", ["--feature", "0001-x", "--tasks"], tmp_path
        )
        assert result.exit_code == 0, result.output
        assert "todas as tasks aprovadas em 1ª passada" in result.output

    def test_show_bodies_includes_note_field(self, tmp_path: pathlib.Path) -> None:
        result = self._run(
            "with_rework",
            ["--feature", "0002-y", "--show-bodies"],
            tmp_path,
        )
        assert result.exit_code == 0, result.output
        # The fixture's CHANGES_REQUESTED entries have note "missing edge case test".
        assert "missing edge case test" in result.output

    def test_no_show_bodies_omits_note_field(self, tmp_path: pathlib.Path) -> None:
        result = self._run(
            "with_rework", ["--feature", "0002-y"], tmp_path
        )
        assert result.exit_code == 0, result.output
        assert "missing edge case test" not in result.output

    def test_show_bodies_in_json_includes_bodies_key(self, tmp_path: pathlib.Path) -> None:
        result = self._run(
            "with_rework",
            ["--feature", "0002-y", "--format", "json", "--show-bodies"],
            tmp_path,
        )
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert "bodies" in data
        assert any("missing edge case test" in (b.get("note") or "") for b in data["bodies"])

    def test_no_data_in_window_exit_two(self, tmp_path: pathlib.Path) -> None:
        # Aggregate run with no specs in the (impossible) future window.
        result = self._run(
            "pristine_first_pass", ["--since", "2099-01-01"], tmp_path
        )
        assert result.exit_code == 2