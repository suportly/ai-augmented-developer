"""``aiadev preflight`` — verify a feature dir before running a pipeline skill.

Spec: ``specs/0010-pipeline-preflight-checks/spec.md``. Stories 3.1-3.3 plus
the spec's Breaking-Changes ``--all`` flag.
"""
from __future__ import annotations

import pathlib
import sys

import click

from ..preflight import PIPELINE_SKILLS, check


@click.command(
    "preflight",
    help=(
        "Verify upstream artifacts for SKILL against feature directory --feature. "
        "Exits non-zero with a single-line diagnostic to stderr on failure."
    ),
)
@click.argument("skill", required=False)
@click.option(
    "--feature",
    "feature",
    type=str,
    help="Feature directory name under specs/ (e.g. 0010-pipeline-preflight-checks).",
)
@click.option(
    "--all",
    "all_features",
    is_flag=True,
    help="Iterate every specs/*/ directory; mutually exclusive with --feature.",
)
def preflight_command(
    skill: str | None,
    feature: str | None,
    all_features: bool,
) -> None:
    if all_features and feature:
        raise click.UsageError("--all is mutually exclusive with --feature")
    if not all_features and not feature:
        raise click.UsageError("either --feature <slug> or --all is required")

    if skill is not None and skill not in PIPELINE_SKILLS:
        click.echo(
            f"unknown skill {skill!r}; expected one of: "
            + ", ".join(s for s in PIPELINE_SKILLS if s != "specify"),
            err=True,
        )
        sys.exit(2)

    repo_root = pathlib.Path.cwd()
    targets: list[pathlib.Path]
    if all_features:
        specs_dir = repo_root / "specs"
        targets = sorted(p for p in specs_dir.iterdir() if p.is_dir()) if specs_dir.is_dir() else []
    else:
        assert feature is not None
        targets = [repo_root / "specs" / feature]

    exit_code = 0
    for feature_dir in targets:
        skill_for_dir = skill or _highest_stage(feature_dir)
        issues = check(skill_for_dir, feature_dir, repo_root=repo_root)
        for issue in issues:
            click.echo(issue.message, err=True)
            if issue.would_abort:
                exit_code = 1

    sys.exit(exit_code)


def _highest_stage(feature_dir: pathlib.Path) -> str:
    """Return the latest pipeline stage whose artifact is present.

    Used by ``--all`` when no explicit skill name is given: we check the
    directory through the highest stage it claims to have completed.
    """
    if (feature_dir / "tasks.md").is_file():
        return "implement"
    if (feature_dir / "plan.md").is_file():
        return "tasks"
    if (feature_dir / "spec.md").is_file():
        return "plan"
    return "specify"
