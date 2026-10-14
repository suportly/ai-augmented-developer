"""T050 — terse-mode foi removido: sem rule, schema, módulo nem menção nos agents."""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_terse_rule_and_schema_are_gone() -> None:
    assert not (ROOT / "rules" / "terse-mode.md").exists()
    assert not (ROOT / "schemas" / "terse-output.schema.json").exists()


def test_aiadev_config_module_is_gone() -> None:
    assert not (ROOT / "src" / "aiadev" / "config.py").exists()
    assert importlib.util.find_spec("aiadev.config") is None


def test_no_agent_mentions_terse() -> None:
    for path in sorted((ROOT / "agents").glob("*.md")):
        body = path.read_text(encoding="utf-8")
        assert not re.search(r"\bterse\b", body, re.IGNORECASE), path.name


def test_review_gate_has_no_terse_shape() -> None:
    gate = (ROOT / "skills/requesting-code-review/references/review-gate.md").read_text(
        encoding="utf-8"
    )
    assert "terse" not in gate.lower()
    assert "🟢" not in gate
