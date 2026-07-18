"""Tests for T010: first wave of ``paths:`` scoping on ``rules/testing.md``.

Story 2 sc1 + cl-6 of specs/0016-agent-skills-interop/spec.md: the first
(and, for now, only) rule to declare ``paths:`` in its frontmatter is
``rules/testing.md``. cl-6 explicitly resolves this as a **minimal first
wave** — every other rule under ``rules/`` stays global (either no
frontmatter at all, or frontmatter without a ``paths:`` key). Assigning
``paths:`` to any other rule is a deliberate, future spec decision, not
an incidental side effect of this task.

This module guards that decision two ways:

1. ``rules/testing.md`` frontmatter parses and has exactly the four
   globs from cl-6, and no longer carries ``alwaysApply``.
2. Every *other* rule file in ``rules/`` is enumerated explicitly today
   (by filename) and asserted to have no ``paths:`` key. If a future
   change adds a new rule file or adds ``paths:`` to an existing one
   without updating this test, the failure message points back at
   spec 0016 cl-6 so it reads as a conscious decision, not a silent
   drift.
"""
from __future__ import annotations

import pathlib

import yaml

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
RULES_DIR = REPO_ROOT / "rules"

EXPECTED_TESTING_PATHS = [
    "tests/**",
    "**/*.test.*",
    "**/*_test.*",
    "conftest.py",
]

# The full rules/ inventory as of spec 0016 cl-6, and whether each file is
# expected to declare frontmatter / a paths: key. Adding a file here (or to
# rules/) without updating this table is exactly the drift this test exists
# to catch.
RULES_WITHOUT_FRONTMATTER = {
    "slash-commands.md",
    "terse-mode.md",
}
RULES_WITH_FRONTMATTER_NO_PATHS = {
    "api-conventions.md",
    "code-style.md",
    "git-workflow.md",
    "security.md",
    # spec 0017: global rule for citing graph facts + confidence labels.
    "graph-facts.md",
}
RULE_WITH_PATHS = "testing.md"

EXPECTED_INVENTORY = (
    RULES_WITHOUT_FRONTMATTER
    | RULES_WITH_FRONTMATTER_NO_PATHS
    | {RULE_WITH_PATHS}
)


def _read_frontmatter(path: pathlib.Path) -> dict | None:
    """Return the parsed YAML frontmatter dict, or None if there is none."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return None
    _, _, rest = text.partition("---\n")
    fm_text, sep, _ = rest.partition("\n---\n")
    if not sep:
        return None
    parsed = yaml.safe_load(fm_text)
    assert isinstance(parsed, dict), f"{path.name}: frontmatter did not parse to a dict"
    return parsed


class TestTestingRuleHasPathsScoping:
    """rules/testing.md declares paths: and drops alwaysApply (cl-6)."""

    def test_frontmatter_parses(self) -> None:
        fm = _read_frontmatter(RULES_DIR / "testing.md")
        assert fm is not None, "rules/testing.md must keep a YAML frontmatter block"

    def test_has_exactly_the_four_cl6_globs(self) -> None:
        fm = _read_frontmatter(RULES_DIR / "testing.md")
        assert fm["paths"] == EXPECTED_TESTING_PATHS

    def test_no_always_apply_key(self) -> None:
        fm = _read_frontmatter(RULES_DIR / "testing.md")
        assert "alwaysApply" not in fm

    def test_description_preserved(self) -> None:
        fm = _read_frontmatter(RULES_DIR / "testing.md")
        assert fm["description"] == (
            "Test-first workflow, naming, and structure baseline for every stack."
        )

    def test_body_key_phrases_unchanged(self) -> None:
        """Sanity check that only frontmatter changed, not the body.

        cl-6 / T010 scope this task to a frontmatter-only edit. Rather than
        shelling out to git (forbidden for this task — no git side effects),
        assert a few stable, distinctive phrases from the body survive
        untouched. A human should still eyeball ``git diff rules/testing.md``
        to confirm the body is byte-identical, as noted in the task.
        """
        text = (RULES_DIR / "testing.md").read_text(encoding="utf-8")
        for phrase in (
            "The AI-Augmented Developer constitution (Article II) mandates test-first",
            "Write the test **before** the implementation.",
            "Do NOT write tests that:",
            "Mocking what you own. If you wrote the class, test it for real.",
            "`time.sleep` in tests. Use freezegun / fake clock / poll-until.",
        ):
            assert phrase in text, f"expected unchanged body phrase missing: {phrase!r}"


class TestOtherRulesStayGlobal:
    """Every rule other than testing.md has no paths: key (cl-6 minimal wave).

    The inventory below is enumerated explicitly (not derived from a glob
    over rules/*.md) so that adding a new rule file, or adding paths: to an
    existing one, fails loudly here instead of silently expanding scope.
    """

    def test_inventory_matches_current_rules_directory(self) -> None:
        actual = {p.name for p in RULES_DIR.glob("*.md")}
        assert actual == EXPECTED_INVENTORY, (
            "rules/ inventory changed since spec 0016 cl-6 was written. "
            "Update EXPECTED_INVENTORY (and the paths:-status tables) in "
            "tests/test_rules_content.py deliberately, then re-confirm "
            "whether the new/changed file should get paths: per cl-6's "
            "'minimal first wave' decision (specs/0016-agent-skills-interop/"
            "spec.md)."
        )

    def test_files_without_frontmatter_have_none(self) -> None:
        for name in sorted(RULES_WITHOUT_FRONTMATTER):
            fm = _read_frontmatter(RULES_DIR / name)
            assert fm is None, (
                f"rules/{name} unexpectedly gained a YAML frontmatter block. "
                "If this was intentional, see spec 0016 cl-6 before adding "
                "paths: to it."
            )

    def test_files_with_frontmatter_have_no_paths_key(self) -> None:
        for name in sorted(RULES_WITH_FRONTMATTER_NO_PATHS):
            fm = _read_frontmatter(RULES_DIR / name)
            assert fm is not None, f"rules/{name} should still have frontmatter"
            assert "paths" not in fm, (
                f"rules/{name} unexpectedly declares paths:. Spec 0016 cl-6 "
                "scoped the first paths: wave to rules/testing.md only — "
                "adding paths: to another rule is a conscious follow-up "
                "spec decision, not an incidental change."
            )
            assert fm.get("alwaysApply") is True, (
                f"rules/{name} should remain alwaysApply: true (global rule)"
            )
