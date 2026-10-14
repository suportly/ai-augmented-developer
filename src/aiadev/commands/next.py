"""``aiadev next`` — print pipeline state and the next step.

Spec: ``specs/0030-lean-pipeline`` (T029, D6, Story 2 scenario 5).
Exit 0 always for a recommendation (a feature without a spec recommends
``/aia:specify``); exit 2 only for a real read error (``OSError``).
"""
from __future__ import annotations

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.markup import escape

from ..pipeline_state import PipelineSnapshot, pipeline_snapshot


def _state_lines(snap: PipelineSnapshot) -> list[str]:
    lines = []
    if snap.feature is not None:
        lines.append(f"feature: {snap.feature}")
    lines.append(f"spec: {'yes' if snap.has_spec else 'no'}")
    lines.append(f"open markers: {snap.open_markers}")
    lines.append(f"plan: {'yes' if snap.has_plan else 'no'}")
    if snap.tasks_total is None or snap.tasks_pending is None:
        lines.append("tasks: none")
    else:
        done = snap.tasks_total - snap.tasks_pending
        lines.append(
            f"tasks: {done}/{snap.tasks_total} done, pending: {snap.tasks_pending}"
        )
    return lines


@click.command("next", help="Show the pipeline state and the next step.")
@click.option("--feature", type=str, help="Feature directory name under specs/.")
def next_command(feature: str | None) -> None:
    console = Console(highlight=False, soft_wrap=True)
    try:
        snap = pipeline_snapshot(Path.cwd(), feature=feature)
    except (OSError, UnicodeDecodeError) as exc:
        click.echo(f"ERROR: cannot read pipeline state: {exc}", err=True)
        sys.exit(2)
    for line in _state_lines(snap):
        console.print(escape(line))
    console.print(f"next: {escape(snap.command)}")
    console.print(f"reason: {escape(snap.reason)}")
