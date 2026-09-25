"""Shape and content-neutrality tests for the product-context templates.

These templates (``mission-template.md``, and later ``tech-stack-template.md``,
``roadmap-template.md``) are generic and rendered by the ``product`` skill
into ``specs/_product/`` in a consumer project. They must carry no concrete
product content — only placeholders, guidance comments, headings, and
structural skeleton (lists/tables/anchors).
"""
from __future__ import annotations

import pathlib
import re

import pytest

PLACEHOLDER_RE = re.compile(r"\{\{[A-Z0-9_]+\}\}")
HEADING_RE = re.compile(r"^#{1,6}\s")
SECTION_ANCHOR_RE = re.compile(r"^<!--\s*section:.*-->$")
HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
# Lines whose only non-whitespace content is list/table/rule punctuation,
# e.g. "-", "|", "|---|", "| --- | --- |", "* ".
SKELETON_RE = re.compile(r"^[\s\-\|\*:]+$")


def _non_template_lines(text: str) -> list[str]:
    """Return lines that look like concrete (non-template) content.

    Strips HTML comments (including multi-line ones) first, then filters
    out blank lines, headings, lines containing a ``{{UPPER_SNAKE}}``
    placeholder, ``<!-- section: ... -->`` anchors, horizontal rules
    (``---``), and list/table skeleton lines whose only content is
    punctuation. Whatever remains is suspect concrete/product content.
    """
    stripped = HTML_COMMENT_RE.sub("", text)
    offenders: list[str] = []
    for raw_line in stripped.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if HEADING_RE.match(line):
            continue
        if PLACEHOLDER_RE.search(line):
            continue
        if SECTION_ANCHOR_RE.match(line):
            continue
        if line == "---":
            continue
        if SKELETON_RE.match(line):
            continue
        offenders.append(raw_line)
    return offenders


@pytest.fixture
def mission_template_path(framework_root: pathlib.Path) -> pathlib.Path:
    return framework_root / "templates" / "mission-template.md"


def test_mission_template_shape(mission_template_path: pathlib.Path) -> None:
    assert mission_template_path.is_file(), "templates/mission-template.md is missing"
    text = mission_template_path.read_text(encoding="utf-8")

    assert "**Language:**" in text, "missing Language: header"

    required_anchors = ["Why", "For whom", "Problem", "Out of scope"]
    for name in required_anchors:
        anchor = f"<!-- section: {name} -->"
        assert anchor in text, f"missing section anchor {anchor!r}"


def test_mission_template_has_no_product_content(
    mission_template_path: pathlib.Path,
) -> None:
    assert mission_template_path.is_file(), "templates/mission-template.md is missing"
    text = mission_template_path.read_text(encoding="utf-8")

    offenders = _non_template_lines(text)
    assert offenders == [], f"template contains concrete content: {offenders!r}"


@pytest.mark.parametrize(
    "line",
    [
        "- Acme Corp is our main customer",
        "Our product helps gyms manage members.",
        "> Built with Django and React.",
        "| Python | chosen for speed |",
    ],
)
def test_non_template_lines_flags_concrete_content(line: str) -> None:
    assert _non_template_lines(line) == [line]


@pytest.mark.parametrize(
    "line",
    [
        "- {{AUDIENCE_1}}",
        "## Why",
        "<!-- section: Why -->",
        "<!-- guidance that mentions Acme Corp is fine inside a comment -->",
        "|---|---|",
        "---",
    ],
)
def test_non_template_lines_accepts_template_skeleton(line: str) -> None:
    assert _non_template_lines(line) == []


@pytest.fixture
def tech_stack_template_path(framework_root: pathlib.Path) -> pathlib.Path:
    return framework_root / "templates" / "tech-stack-template.md"


def test_tech_stack_template_shape(tech_stack_template_path: pathlib.Path) -> None:
    assert tech_stack_template_path.is_file(), "templates/tech-stack-template.md is missing"
    text = tech_stack_template_path.read_text(encoding="utf-8")

    assert "**Language:**" in text, "missing Language: header"

    required_anchors = ["Languages", "Frameworks", "Decisions"]
    for name in required_anchors:
        anchor = f"<!-- section: {name} -->"
        assert anchor in text, f"missing section anchor {anchor!r}"

    for label in ("**Choice:**", "**Why:**", "**Rejected alternatives:**"):
        assert label in text, f"Decisions section missing field label {label!r}"


def test_tech_stack_template_has_no_product_content(
    tech_stack_template_path: pathlib.Path,
) -> None:
    assert tech_stack_template_path.is_file(), "templates/tech-stack-template.md is missing"
    text = tech_stack_template_path.read_text(encoding="utf-8")

    offenders = _non_template_lines(text)
    assert offenders == [], f"template contains concrete content: {offenders!r}"


def test_tech_stack_template_documents_role_split(
    tech_stack_template_path: pathlib.Path,
) -> None:
    assert tech_stack_template_path.is_file(), "templates/tech-stack-template.md is missing"
    text = tech_stack_template_path.read_text(encoding="utf-8")

    assert "introspect" in text, "must document that the first version comes from introspect()"
    assert "auto-stack" in text, "must document the <!-- aiadev:auto-stack --> role split"


@pytest.fixture
def roadmap_template_path(framework_root: pathlib.Path) -> pathlib.Path:
    return framework_root / "templates" / "roadmap-template.md"


ROADMAP_ENTRY_RE = re.compile(
    r"^### R\{\{[A-Z0-9_]+\}\} — .+\n"
    r"(?:.*\n)*?"
    r"- \*\*Status:\*\*.*\n"
    r"- \*\*Spec:\*\*.*\n"
    r"- \*\*Depends on:\*\*.*$",
    re.MULTILINE,
)


def test_roadmap_template_entry_grammar(roadmap_template_path: pathlib.Path) -> None:
    assert roadmap_template_path.is_file(), "templates/roadmap-template.md is missing"
    text = roadmap_template_path.read_text(encoding="utf-8")

    assert "**Language:**" in text, "missing Language: header"

    anchor = "<!-- section: Entries -->"
    assert anchor in text, f"missing section anchor {anchor!r}"

    assert ROADMAP_ENTRY_RE.search(text), (
        "expected a '### R{{...}} — ...' heading followed by "
        "'- **Status:**', '- **Spec:**', '- **Depends on:**' in order"
    )

    for status in ("planned", "in-progress", "done", "dropped"):
        assert status in text, f"missing status value {status!r} in closed set"


def test_roadmap_template_has_no_product_content(
    roadmap_template_path: pathlib.Path,
) -> None:
    assert roadmap_template_path.is_file(), "templates/roadmap-template.md is missing"
    text = roadmap_template_path.read_text(encoding="utf-8")

    offenders = _non_template_lines(text)
    assert offenders == [], f"template contains concrete content: {offenders!r}"


@pytest.mark.parametrize(
    ("template", "consumer"),
    [
        ("mission-template.md", "specify"),
        ("tech-stack-template.md", "plan"),
        ("roadmap-template.md", "specify"),
    ],
)
def test_templates_readme_lists_product_templates(
    framework_root: pathlib.Path, template: str, consumer: str
) -> None:
    readme = (framework_root / "templates" / "README.md").read_text(encoding="utf-8")
    rows = [line for line in readme.splitlines() if line.startswith("|") and f"`{template}`" in line]
    assert rows, f"templates/README.md table has no row for {template}"
    assert "`product`" in rows[0], f"{template} row must name `product` as producer"
    assert f"`{consumer}`" in rows[0], f"{template} row must name `{consumer}` as consumer"


@pytest.mark.parametrize("name", ["mission", "tech-stack"])
def test_template_marker_grammar_matches_skill(framework_root: pathlib.Path, name: str) -> None:
    text = (framework_root / "templates" / f"{name}-template.md").read_text(encoding="utf-8")
    assert "[NEEDS CLARIFICATION: cl-N" not in text
    assert "[NEEDS CLARIFICATION:cl-N" in text
