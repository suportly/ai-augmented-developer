"""Guarda: nada referencia recursos removidos pela spec 0030 sem substituto (Story 6 sc4)."""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REMOVED = re.compile(
    r"/aia:help\b|skills/help\b|skills/using-ai-augmented-developer|"
    r"using-ai-augmented-developer|\bAIADEV_HELP_PLAIN\b"
)
# Históricos e a própria guarda.
EXCLUDED_PREFIXES = ("specs/",)
EXCLUDED_FILES = {
    "CHANGELOG.md",
    # Guardas que afirmam a AUSÊNCIA dos recursos removidos.
    "tests/test_no_dangling_removed_refs.py",
    "tests/test_gemini_entrypoint.py",
    "tests/test_pipeline_state.py",
}
SUFFIXES = {".md", ".py", ".yaml", ".yml", ".json", ".toml", ".sh", ".ts", ".mdc"}


def _tracked_files() -> list[Path]:
    out = subprocess.run(
        ["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.splitlines()
    return [ROOT / name for name in out if (ROOT / name).is_file()]


def test_no_references_to_removed_resources():
    hits: list[str] = []
    for path in _tracked_files():
        rel = path.relative_to(ROOT).as_posix()
        if rel in EXCLUDED_FILES or rel.startswith(EXCLUDED_PREFIXES):
            continue
        if path.suffix not in SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for number, line in enumerate(text.splitlines(), 1):
            if REMOVED.search(line):
                hits.append(f"{rel}:{number}: {line.strip()[:100]}")
    assert not hits, "dangling references:\n" + "\n".join(hits[:60])
