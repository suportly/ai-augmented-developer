"""frontend-design quality (spec 0034)."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "presets" / "django-drf-react" / "skills" / "frontend-design" / "SKILL.md"
RAW = SKILL.read_text(encoding="utf-8")
_, FRONT, BODY = RAW.split("---\n", 2)
LOW = BODY.lower()
DESC = re.search(r"^description:\s*(.+)$", FRONT, re.M).group(1).strip()  # type: ignore[union-attr]

CURRENT_DESC = (
    "Create distinctive, production-grade frontend interfaces with high design quality. "
    "Use when building web components, pages, or React Native screens. "
    "Generates creative, polished code that avoids generic AI aesthetics."
)


def _has(*phrases: str) -> bool:
    return all(p in LOW for p in phrases)


def test_description_unchanged() -> None:
    assert DESC == CURRENT_DESC


def test_direction_recorded_before_any_component() -> None:
    assert _has("direction record", "before generating any component file")


def test_direction_record_is_short_and_complete() -> None:
    assert _has("at most 6 lines", "style, typography, palette", "reason for each")


def test_starts_from_existing_theme_tokens() -> None:
    assert _has("start from the existing theme tokens", "where it diverges")


def test_given_direction_only_maps_to_tokens() -> None:
    assert _has("already carries a direction", "brand or approved prototype", "only the mapping to tokens")


def test_no_tokens_proposes_minimal_set() -> None:
    assert _has("no theme tokens", "minimal tokens", "colors and fonts")


def test_verify_in_browser_captures_four_states() -> None:
    assert _has("verify in a browser", "success, empty, error and loading", "against the direction record")


def test_unforceable_state_not_verified_with_reason() -> None:
    assert _has("cannot be forced", "not verified", "reason")


def test_state_absent_by_design_not_applicable() -> None:
    assert _has("by design", "not applicable")


def test_dev_server_failure_reported() -> None:
    assert _has("dev server", "error output", "counts as not verified")


def test_no_browser_screen_not_seen() -> None:
    assert _has("no browser", "was not seen", "unverified", "not declare the screen done")


def test_captures_local_data_never_committed_no_installs() -> None:
    assert _has("test or local data", "never committed", "never install packages")


def _audit() -> str:
    m = re.search(r"^## [^\n]*audit[^\n]*\n(.*?)(?=^## |\Z)", BODY, re.M | re.S | re.I)
    assert m, "audit section missing"
    return m.group(1)


def test_audit_has_exactly_eight_numbered_signals() -> None:
    nums = re.findall(r"^(\d+)\. ", _audit(), re.M)
    assert nums == [str(i) for i in range(1, 9)]


def test_audit_marks_each_signal_present_or_absent_with_evidence() -> None:
    a = _audit().lower()
    assert "present or absent" in a and "snippet or capture" in a


def test_audit_rechecks_fixed_signal_before_delivering() -> None:
    a = _audit().lower()
    assert "fixed signal" in a and "re-check" in a and "before delivering" in a


def test_audit_keeps_required_signal_with_reason() -> None:
    a = _audit().lower()
    assert "the request requires" in a and "keep it" in a and "record the reason" in a


def test_checklist_requires_capture_of_each_state() -> None:
    chk = LOW.split("## checklist before submitting", 1)[1]
    assert "capture of each state" in chk and "loading" in chk and "error" in chk and "empty" in chk
    assert "state handled" not in chk


def test_body_within_1400_tokens() -> None:
    assert -(-len(BODY) // 4) <= 1400


def _unreleased() -> str:
    body = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    return body.split("## [0.29.0]", 1)[1].split("\n## [", 1)[0].lower()


def test_changelog_records_0034() -> None:
    sec = _unreleased()
    for needle in (
        "0034",
        "frontend-design",
        "art direction",
        "audit",
        "browser",
        "budget is unchanged",
        "strivex",
    ):
        assert needle in sec, needle
