"""Guarda: o preset ``lean`` não instala conteúdo de stack (spec 0030, Story 4 sc1)."""
from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
STACK_WORDS = re.compile(
    r"\b(django|celery|drf|react|mui|expo)\b|manage\.py|select_related|on_commit",
    re.IGNORECASE,
)


def _budget_module():
    spec = importlib.util.spec_from_file_location(
        "instruction_budget", ROOT / "scripts" / "instruction_budget.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def lean_install(tmp_path_factory):
    dest = tmp_path_factory.mktemp("lean")
    _budget_module().install_preset("lean", dest)
    return dest


def _stack_hits(base: Path, patterns: tuple[str, ...]) -> list[str]:
    hits: list[str] = []
    for pattern in patterns:
        for path in sorted(base.glob(pattern)):
            if not path.is_file():
                continue
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                match = STACK_WORDS.search(line)
                if match:
                    hits.append(f"{path.relative_to(base)}:{number}: {match.group(0)}")
    return hits


def test_lean_skills_and_agents_have_no_stack_words(lean_install):
    hits = _stack_hits(
        lean_install,
        (".claude/skills/**/*.md", ".claude/agents/*.md"),
    )
    assert not hits, "stack content leaked into lean:\n" + "\n".join(hits[:40])
