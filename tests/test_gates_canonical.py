"""D13 (spec 0030): each gate that must not be lost keeps its key phrase in
its canonical file. Regexes tolerate line reflow and case."""
from __future__ import annotations

import pathlib
import re

import pytest

GATES = [
    ("RED observed for the right reason", "skills/test-driven-development/SKILL.md",
     r"fail\s+for\s+the\s+right\s+reason"),
    ("RED verified before GREEN", "skills/test-driven-development/SKILL.md",
     r"verify\s+red"),
    ("Constitution Check with evidence", "skills/plan/SKILL.md",
     r"constitution\s+check[\s\S]{0,400}?concrete\s+evidence"),
    ("Constitution Check blank rows block", "skills/plan/SKILL.md",
     r"blank\s+rows\s+block"),
    ("Constitution Check evidence column", "templates/plan-template.md",
     r"\|\s*Article\s*\|[^\n]*\|\s*Evidence\s*\|"),
    ("review.yaml approved before PR", "skills/finishing-a-branch/SKILL.md",
     r"review\.yaml[\s\S]{0,200}?status:\s*approved"),
    ("root cause before fix", "skills/systematic-debugging/SKILL.md",
     r"no\s+fix\s+without\s+root\s+cause"),
    ("escalate after 3 failed fixes", "skills/systematic-debugging/SKILL.md",
     r"3\s+failed\s+fix\s+attempts[^\n]{0,80}stop"),
    ("secret files excluded from product inference", "skills/product/SKILL.md",
     r"never\s+read\s+secret\s+files[\s\S]*?\.env[\s\S]*?\*\.pem[\s\S]*?\*\.key"
     r"[\s\S]*?id_rsa[\s\S]*?credentials"),
]


@pytest.mark.parametrize("gate,path,pattern", GATES, ids=[g[0] for g in GATES])
def test_gate_phrase_in_canonical_file(
    framework_root: pathlib.Path, gate: str, path: str, pattern: str
) -> None:
    text = (framework_root / path).read_text(encoding="utf-8")
    assert re.search(pattern, text, flags=re.IGNORECASE), f"{gate}: not found in {path}"
