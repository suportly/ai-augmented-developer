"""T051 — nenhuma referência remanescente ao terse-mode removido na 0030."""
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NEEDLES = ("aiadev_terse", "aiadev.tersemode", "terse-mode", "terse_mode")
SUFFIXES = {".md", ".py", ".yaml", ".yml", ".json"}
# CHANGELOG é histórico; specs/ guarda o registro; os dois testes fixam a remoção/aviso.
# Os slugs 0009-token-economy-terse-mode em docs/coverage-* são o id da spec histórica.
ALLOWED = {
    "CHANGELOG.md",
    "tests/test_no_terse_assets.py",
    "tests/test_sync_terse_notice.py",
    "tests/test_no_terse_references.py",
    "src/aiadev/commands/sync.py",  # aviso do T052
    "docs/coverage-baseline.md",
    "docs/coverage-exceptions.yaml",
}


def _tracked() -> list[str]:
    out = subprocess.run(
        ["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout
    return [p for p in out.splitlines() if p]


def test_no_tracked_file_references_terse_mode() -> None:
    offenders = []
    for rel in _tracked():
        path = ROOT / rel
        if rel in ALLOWED or rel.startswith("specs/") or path.suffix not in SUFFIXES:
            continue
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        if any(n in text for n in NEEDLES):
            offenders.append(rel)
    assert not offenders, offenders


def test_credits_keeps_caveman_with_removal_note() -> None:
    body = (ROOT / "CREDITS.md").read_text(encoding="utf-8")
    assert "caveman" in body.lower()
    assert "0030" in body
