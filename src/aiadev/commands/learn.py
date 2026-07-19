"""Click subcommand for ``aiadev learn`` (spec 0018).

Mines the pipeline audit trail for recurring failure patterns and proposes
reviewable guidance edits. Read-only by default, local, no network.

This module is the wiring: it walks the workspace (``specs/*/.review-log.jsonl``)
and formats output. Detection lives in :mod:`aiadev.learn`.
"""
from __future__ import annotations

import pathlib

import click

from .. import learn as _learn


def _format_text(patterns: list[_learn.Pattern]) -> str:
    if not patterns:
        return "Nenhum padrão recorrente encontrado no rastro.\n"
    lines = ["Padrões recorrentes de falha (mais evidenciados primeiro):", ""]
    for p in patterns:
        evidence = ", ".join(p.features)
        if p.sufficient:
            lines.append(
                f"- [{p.kind}] {p.subject} — {p.occurrences} "
                f"({evidence})"
            )
        else:
            lines.append(
                f"- [{p.kind}] {p.subject} — evidência insuficiente "
                f"({p.occurrences}: {evidence})"
            )
        for note in p.notes:
            lines.append(f"    note: {note}")
    lines.append("")
    return "\n".join(lines)


@click.command(name="learn", help="Minera o rastro do pipeline em busca de padrões de falha recorrentes.")
@click.option(
    "--show-bodies",
    is_flag=True,
    default=False,
    help="Inclui a prosa livre do reviewer (campo note). Fora do padrão por privacidade (Artigo VI).",
)
def learn_command(show_bodies: bool) -> None:
    """Report recurring failure patterns mined from the audit trail."""
    workspace = pathlib.Path.cwd()
    per_spec = _learn.collect_per_spec_entries(workspace)
    patterns = _learn.detect_all(per_spec, show_bodies=show_bodies)
    click.echo(_format_text(patterns), nl=False)
