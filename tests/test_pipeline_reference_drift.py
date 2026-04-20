"""T010 — drift guard for docs/pipeline-reference.md.

Phase 4 is deferred; the token-count assertion is skipped until the
benchmark provider (T013) lands. Everything else is enforced:

- the reference lists the same pipeline commands named in root CLAUDE.md,
- the file is a clean regeneration of scripts/generate_pipeline_reference.py,
- the line budget (≤ 24 non-empty lines) holds.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "docs" / "pipeline-reference.md"
CLAUDE_MD = ROOT / "CLAUDE.md"
GENERATOR = ROOT / "scripts" / "generate_pipeline_reference.py"

REF_COMMAND_RE = re.compile(r"`/aiadev:([a-z][a-z0-9-]*)`")
# CLAUDE.md's "Skill to invoke" column uses bare backticked names.
CLAUDE_TABLE_RE = re.compile(r"\|\s*`([a-z][a-z0-9-]*)`\s*\|")


def _extract_ref_commands(body: str) -> set[str]:
    return set(REF_COMMAND_RE.findall(body))


# Skills that live in the quick-reference but are deliberately not in the
# CLAUDE.md pipeline table (the root table is a "when to invoke" cookbook;
# `help` is a leaf meta-skill that prints the table itself).
REFERENCE_ONLY = {"help"}

# Skills that appear in the CLAUDE.md table but are cross-cutting (not
# pipeline stages the help surface wants to advertise as steps).
CLAUDE_ONLY_NON_PIPELINE = {
    "test-driven-development",
    "systematic-debugging",
    "frontend-design",
    "constitution",
}


def _extract_claude_pipeline_commands(body: str) -> set[str]:
    """Pull bare skill names from backticked cells in CLAUDE.md, minus non-pipeline."""
    return {name for name in CLAUDE_TABLE_RE.findall(body)} - CLAUDE_ONLY_NON_PIPELINE


def test_reference_file_exists():
    assert REFERENCE.exists(), (
        "docs/pipeline-reference.md must be committed; run "
        "scripts/generate_pipeline_reference.py"
    )


def test_reference_matches_claude_md_pipeline_commands():
    ref_cmds = _extract_ref_commands(REFERENCE.read_text(encoding="utf-8")) - REFERENCE_ONLY
    claude_cmds = _extract_claude_pipeline_commands(CLAUDE_MD.read_text(encoding="utf-8"))
    missing_from_claude = ref_cmds - claude_cmds
    missing_from_reference = claude_cmds - ref_cmds
    assert not missing_from_claude, (
        f"pipeline-reference.md names commands absent from CLAUDE.md: "
        f"{sorted(missing_from_claude)}"
    )
    assert not missing_from_reference, (
        f"CLAUDE.md names commands absent from pipeline-reference.md: "
        f"{sorted(missing_from_reference)}"
    )


def test_reference_is_clean_regeneration(tmp_path):
    """Running the generator must produce the committed file byte-for-byte."""
    output = tmp_path / "pipeline-reference.md"
    result = subprocess.run(
        [sys.executable, str(GENERATOR), "--output", str(output)],
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.returncode == 0, result.stderr
    expected = REFERENCE.read_bytes()
    actual = output.read_bytes()
    assert expected == actual, (
        "docs/pipeline-reference.md is out of sync with the generator — "
        "run scripts/generate_pipeline_reference.py and commit the result"
    )


def test_reference_line_budget():
    """Terse-mode help budget: ≤ 24 non-empty lines."""
    body = REFERENCE.read_text(encoding="utf-8")
    non_empty = [ln for ln in body.splitlines() if ln.strip()]
    assert len(non_empty) <= 24, (
        f"pipeline-reference.md has {len(non_empty)} non-empty lines; "
        f"budget is 24"
    )


@pytest.mark.skip(reason="token-budget assertion lands with Phase 4 (T013 provider)")
def test_reference_token_budget():
    """Placeholder — ≤ 600 Sonnet 4.6 tokens once benchmark.provider ships."""
    # When T013 lands, import benchmark.provider.count_tokens and assert:
    # count_tokens(REFERENCE.read_text(), model="claude-sonnet-4-6") <= 600
    raise NotImplementedError
