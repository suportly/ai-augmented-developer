"""find-skills (spec 0032 T001): rules pinned by key phrases."""
from __future__ import annotations

import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = (ROOT / "skills" / "find-skills" / "SKILL.md").read_text(encoding="utf-8")
_, FRONT, BODY = RAW.split("---\n", 2)
DESC = re.search(r"^description:\s*(.+)$", FRONT, re.M).group(1).strip()  # type: ignore[union-attr]
LOW = BODY.lower()


def test_description_within_30_tokens() -> None:
    assert math.ceil(len(DESC) / 4) <= 30


def test_body_within_budget() -> None:
    assert math.ceil(len(BODY) / 4) <= 650


def test_no_announce_at_start() -> None:
    assert "announce at start" not in LOW


def test_no_vendor_or_stack_names() -> None:
    banned = ["vercel", "anthropic", "microsoft", "react", "next.js", "django",
             "python", "skills.sh", "github.com"]
    for word in banned:
        assert word not in RAW.lower(), word


def test_never_auto_confirm_flag() -> None:
    assert "never add `-y`/`--yes`" in LOW
    assert not re.search(r"(^|\s)(-y|--yes)\b", BODY.replace("`-y`/`--yes`", ""))


def test_search_command() -> None:
    assert "npx skills find" in BODY


def test_present_name_what_source_command() -> None:
    assert re.search(r"name[^\n]*what it does[^\n]*source[^\n]*npx skills add <source>", LOW)


def test_only_install_after_user_confirms() -> None:
    assert "only after the user confirms" in LOW
    assert "only recommend" in LOW


def test_verification_thresholds() -> None:
    assert "1,000 installs or more" in LOW
    assert "fewer than 100 installs" in LOW
    assert "fewer than 100 stars" in LOW


def test_unconfirmed_data_caveat() -> None:
    assert "could not be confirmed" in LOW


def test_read_candidate_and_flag_risks() -> None:
    assert "read the candidate's `skill.md`" in LOW
    for risk in ("network commands", "writes outside the project", "package installs"):
        assert risk in LOW, risk


def test_generic_terms_only() -> None:
    assert "generic domain terms only" in LOW
    for leak in ("client names", "paths", "secrets", "code snippets"):
        assert leak in LOW, leak


def test_nothing_found_path() -> None:
    assert re.search(r"nothing (relevant )?(is )?found[^\n]*offer to do the task directly", LOW)


def test_no_network_or_cli_path() -> None:
    assert re.search(r"no network or cli[^\n]*could not search[^\n]*without the skill", LOW)
