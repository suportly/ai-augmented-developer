"""Click subcommand for ``aiadev learn`` (spec 0018).

Mines the pipeline audit trail for recurring failure patterns and proposes
reviewable guidance edits. Read-only by default, local, no network.

This module is the wiring: it walks the workspace (``specs/*/.review-log.jsonl``)
and formats output. Detection lives in :mod:`aiadev.learn`.
"""
from __future__ import annotations

import datetime
import json
import pathlib

import click

from .. import learn as _learn

# Default aggregation window, mirroring ``aiadev metrics``.
_DEFAULT_SINCE_DAYS = 90

# JSON output schema version. Additive fields bump this; the payload is a pure
# function of the trail (no execution timestamp) so CI diffs are stable.
JSON_SCHEMA_VERSION = 1


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


def _format_json(patterns: list[_learn.Pattern]) -> str:
    payload = {
        "schema_version": JSON_SCHEMA_VERSION,
        "patterns": [
            {
                "kind": p.kind,
                "subject": p.subject,
                "occurrences": p.occurrences,
                "features": list(p.features),
                "sufficient": p.sufficient,
                "notes": list(p.notes),
            }
            for p in patterns
        ],
    }
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


@click.command(name="learn", help="Minera o rastro do pipeline em busca de padrões de falha recorrentes.")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Formato de saída. json é estável (schema fixo, sem timestamp) para CI.",
)
@click.option(
    "--since",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    default=None,
    help="Janela de agregação (YYYY-MM-DD). Default: últimos 90 dias (espelha metrics).",
)
@click.option(
    "--show-bodies",
    is_flag=True,
    default=False,
    help="Inclui a prosa livre do reviewer (campo note). Fora do padrão por privacidade (Artigo VI).",
)
def learn_command(output_format: str, since: datetime.datetime | None, show_bodies: bool) -> None:
    """Report recurring failure patterns mined from the audit trail."""
    workspace = pathlib.Path.cwd()
    since_date = (
        since.date()
        if since is not None
        else datetime.date.today() - datetime.timedelta(days=_DEFAULT_SINCE_DAYS)
    )
    per_spec = _learn.collect_per_spec_entries(workspace, since=since_date)
    patterns = _learn.detect_all(per_spec, show_bodies=show_bodies)
    if output_format == "json":
        click.echo(_format_json(patterns), nl=False)
    else:
        click.echo(_format_text(patterns), nl=False)
