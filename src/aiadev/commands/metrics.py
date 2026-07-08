"""Click subcommand for ``aiadev metrics``.

Spec: ``specs/0015-aiadev-metrics/spec.md``.

This module owns only:
- flag parsing (``--feature``, ``--since``, ``--format``, ``--tasks``,
  ``--show-bodies``);
- the ``subprocess.run(["git", "log", ...])`` call that feeds the
  core's git-based metrics;
- the exit-code policy (ADR-7: ``0`` ok, ``1`` parse error, ``2`` no
  data in window).

The aggregation lives in ``aiadev.metrics``; the formatters live in
``aiadev.metrics_format``. This module is the wiring.
"""

from __future__ import annotations

import datetime
import pathlib
import subprocess
import sys
from typing import Optional

import click

from .. import metrics as _metrics
from .. import metrics_format as _format


# Last spec id authored BEFORE the ``.review-log.jsonl`` substrate
# shipped. Spec 0014 introduced the JSONL (see
# ``specs/0014-bmad-inspired-evolutions/spec.md`` Story 3), so every
# spec with id ≤ 13 predates the trail and a missing log file is
# expected — that combination triggers the "pre-cutoff" exit-2 path
# documented in plan ADR-7.
#
# NOTE: this is NOT the same as ``schemas/spec-recon.schema.json``'s
# ``cutover_spec_id`` (which is 10 — the recon-section grandfather
# line). The two cutoffs evolve independently; do not collapse them.
_REVIEW_LOG_CUTOFF_LAST_SPEC_ID = 13


def _collect_git_log(workspace: pathlib.Path) -> str:
    """Best-effort fetch of ``git log --date=short -p --name-only`` over ``specs/``.

    Returns an empty string when git is unavailable, the workspace is
    not a git repo, or the call fails for any reason — git-derived
    metrics degrade gracefully to ``None``. We never let a git failure
    block the main report.

    A single fetch feeds both consumers:

    * :func:`aiadev.metrics.specify_to_last_commit_days` looks only at
      flush-left lines (``--name-only`` paths) and ignores indented
      message-body and diff-context lines.
    * :func:`aiadev.metrics.clarify_iteration_count` looks at the
      patch body (``-p``), keying on ``^diff --git`` boundaries and
      ``^\\+`` added lines.

    The two patterns are disjoint, so one log payload serves both.
    """
    try:
        proc = subprocess.run(
            ["git", "log", "--date=short", "-p", "--name-only", "--", "specs/"],
            cwd=workspace,
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (FileNotFoundError, subprocess.SubprocessError):
        return ""
    if proc.returncode != 0:
        return ""
    return proc.stdout


def _resolve_feature(workspace: pathlib.Path, slug: str) -> Optional[pathlib.Path]:
    return _metrics._find_feature_dir(workspace, slug)


@click.command(
    "metrics",
    help=(
        "Agrega métricas do audit trail do framework "
        "(specs/<branch>/.review-log.jsonl, tasks.md, spec headers, git log) "
        "e emite indicadores estruturados."
    ),
)
@click.option(
    "--feature",
    "feature",
    default=None,
    help="Slug ou diretório da feature (e.g. 0001-x ou x). Quando omitido, agrega sobre a janela.",
)
@click.option(
    "--since",
    "since",
    default=None,
    type=click.DateTime(formats=["%Y-%m-%d"]),
    help="Início da janela (YYYY-MM-DD). Default: hoje - 90 dias.",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Formato de saída. Default: text.",
)
@click.option(
    "--tasks",
    "show_tasks",
    is_flag=True,
    default=False,
    help="Inclui listing por-task de rework (Story 3).",
)
@click.option(
    "--show-bodies",
    "show_bodies",
    is_flag=True,
    default=False,
    help=(
        "Imprime a prosa livre (note) das entries em .review-log.jsonl. "
        "Off por padrão (privacy). Só tem efeito com --feature; no modo "
        "agregado é ignorado."
    ),
)
def metrics_command(
    feature: Optional[str],
    since: Optional[datetime.datetime],
    output_format: str,
    show_tasks: bool,
    show_bodies: bool,
) -> None:
    """``aiadev metrics`` entry point."""
    workspace = pathlib.Path.cwd()
    today = datetime.date.today()
    since_date = since.date() if since else today - datetime.timedelta(days=90)
    until_date = today

    git_log_output = _collect_git_log(workspace)

    # ``now=today`` is passed to ``build_report`` so the calendar
    # reference is captured at the top of this single CLI invocation
    # (rather than implicitly re-read inside ``build_report``). Two
    # runs at different instants are still allowed to differ — but
    # within a run, the value is frozen, which is what the determinism
    # tests assert.

    if feature is not None:
        # Single-feature mode: bypass window check.
        feature_dir = _resolve_feature(workspace, feature)
        if feature_dir is None:
            click.echo(f"Feature '{feature}' not found under {workspace / 'specs'}", err=True)
            sys.exit(1)
        try:
            report = _metrics.build_report(
                workspace,
                feature=feature,
                since=since_date,
                until=until_date,
                now=today,
                git_log_output=git_log_output,
            )
        except ValueError as exc:
            click.echo(f"erro de parse: {exc}", err=True)
            sys.exit(1)

        # Collect review entries (for --show-bodies and trail detection).
        log_path = feature_dir / ".review-log.jsonl"
        entries = _metrics.read_review_log(log_path)

        # Read the spec header to know whether the feature predates the
        # ``.review-log.jsonl`` cutoff (spec id ≤ 13, see
        # ``_REVIEW_LOG_CUTOFF_LAST_SPEC_ID`` above — NOT the schema
        # recon cutover, which is 10).
        try:
            header = _metrics.read_spec_header(feature_dir / "spec.md")
        except ValueError:
            click.echo(
                f"spec.md em {feature_dir} tem header não-parseável; abortando.",
                err=True,
            )
            sys.exit(1)

        is_pre_cutoff = header["spec_id"] <= _REVIEW_LOG_CUTOFF_LAST_SPEC_ID

        if not log_path.exists() and is_pre_cutoff:
            # Story 1 sc2: legacy feature, no trail expected, exit 2.
            _emit(report, output_format, show_tasks, show_bodies, entries)
            click.echo(
                "Nota: feature anterior ao cutoff 0014; review trail indisponível. "
                "Status de tasks ainda foi reportado.",
                err=True,
            )
            sys.exit(2)

        # Post-cutoff feature with no/empty log: Story 1 sc3, exit 0
        # with the "review trail: vazio" message handled by the formatter.
        _emit(report, output_format, show_tasks, show_bodies, entries)
        sys.exit(0)

    # Aggregate mode.
    try:
        report = _metrics.build_report(
            workspace,
            since=since_date,
            until=until_date,
            now=today,
            git_log_output=git_log_output,
        )
    except ValueError as exc:
        click.echo(f"erro de parse: {exc}", err=True)
        sys.exit(1)

    if report.n_specs_in_window == 0:
        click.echo(
            f"Nenhum spec com Status Implemented/Merged no intervalo "
            f"[{since_date}, {until_date}] (specs em andamento não entram "
            f"no agregado; use --feature para inspecioná-los). "
            f"Cutoff de review trail: spec 0014.",
            err=True,
        )
        sys.exit(2)

    _emit(report, output_format, show_tasks, show_bodies, [])
    sys.exit(0)


def _emit(
    report: "_metrics.MetricsReport",
    output_format: str,
    show_tasks: bool,
    show_bodies: bool,
    entries: list[dict],
) -> None:
    if output_format == "json":
        out = _format.format_json(
            report,
            show_tasks=show_tasks,
            show_bodies=show_bodies,
            review_entries=entries if show_bodies else None,
        )
    else:
        out = _format.format_text(
            report,
            show_tasks=show_tasks,
            show_bodies=show_bodies,
            review_entries=entries if show_bodies else None,
        )
    click.echo(out, nl=False)
