"""Documentation drift tests for the metrics feature.

Spec: ``specs/0015-aiadev-metrics/spec.md``.

These tests assert that the documentation surfaces describing the
``aiadev metrics`` subcommand exist and reference the canonical
artefacts. They are intentionally shape checks, not snapshots —
the docs may be reworded without breaking the assertions, but the
command name and key flags must remain documented.
"""

from __future__ import annotations

import pathlib


REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent


def test_metrics_reference_doc_exists() -> None:
    # ``docs/pipeline-reference.md`` is generated and lists ``/aia:*``
    # slash commands only, so the new CLI subcommand gets its own
    # hand-written doc at ``docs/metrics.md``.
    doc = (REPO_ROOT / "docs" / "metrics.md").read_text(encoding="utf-8")
    assert "aiadev metrics" in doc
    # Document at least one of the canonical flags.
    assert "--feature" in doc
    assert "--format" in doc
    # Document the cl-resolved decisions so the doc carries the same
    # contract the spec does (a reader on the doc should see why the
    # defaults are what they are).
    assert "90" in doc  # 90-day default window
    assert "schema_version" in doc  # json schema marker


def test_readme_has_metrics_usage_example() -> None:
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    assert "aiadev metrics" in readme


def test_changelog_unreleased_mentions_metrics() -> None:
    changelog = (REPO_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    # Extract the [Unreleased] section: everything from "## [Unreleased]"
    # up to (but not including) the next "## [" line.
    start = changelog.find("## [Unreleased]")
    assert start != -1, "CHANGELOG missing [Unreleased] header"
    rest = changelog[start + len("## [Unreleased]"):]
    end = rest.find("\n## [")
    section = rest[:end] if end != -1 else rest
    assert "metrics" in section.lower(), (
        f"[Unreleased] section does not mention 'metrics':\n{section[:200]}"
    )
