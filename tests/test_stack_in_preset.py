"""T039 — stack knowledge lives in the preset, not in the generic skills
(spec 0030, Story 4, plan D1/D11).

Each of the five generic skills carries one anchor line that points at
``references/stack.md``; the stack content itself ships as that file from
``presets/django-drf-react`` and lands beside the generic ``SKILL.md``.
"""
from __future__ import annotations

import importlib.util
import pathlib
import re

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SKILLS = (
    "test-driven-development",
    "systematic-debugging",
    "finishing-a-branch",
    "requesting-code-review",
    "plan",
)
ANCHOR = (
    "If `references/stack.md` exists beside this file, read it for "
    "stack-specific guidance."
)
STACK_WORDS = re.compile(
    r"django|drf|celery|react|\bmui\b|expo|manage\.py|select_related|on_commit"
    r"|pytest|jest|factory_boy|litellm|ruff|tanstack|tsc\b|npm\b|npx\b|redis",
    re.IGNORECASE,
)


@pytest.fixture(scope="module")
def installer():
    spec = importlib.util.spec_from_file_location(
        "instruction_budget", ROOT / "scripts" / "instruction_budget.py"
    )
    module = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module.install_preset


@pytest.fixture(scope="module")
def django_project(installer, tmp_path_factory):
    dest = tmp_path_factory.mktemp("django")
    installer("django-drf-react", dest)
    return dest


@pytest.fixture(scope="module")
def lean_project(installer, tmp_path_factory):
    dest = tmp_path_factory.mktemp("lean")
    installer("lean", dest)
    return dest


@pytest.mark.parametrize("skill", SKILLS)
def test_generic_skill_has_anchor_and_no_stack_words(skill):
    text = (ROOT / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
    assert text.count(ANCHOR) == 1
    leaks = sorted({m.group(0).lower() for m in STACK_WORDS.finditer(text)})
    assert not leaks, f"stack words left in generic {skill}: {leaks}"


@pytest.mark.parametrize("skill", SKILLS)
def test_preset_installs_stack_md_beside_single_generic_skill(django_project, skill):
    base = django_project / ".claude" / "skills" / skill
    assert (base / "references" / "stack.md").is_file()
    skill_md = (base / "SKILL.md").read_text(encoding="utf-8")
    generic = (ROOT / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
    body = generic.split("---", 2)[2].strip()
    assert skill_md.count(ANCHOR) == 1
    assert body.splitlines()[0] in skill_md
    assert len(list(base.glob("SKILL*.md"))) == 1


@pytest.mark.parametrize("skill", SKILLS)
def test_lean_has_no_stack_md(lean_project, skill):
    assert not (
        lean_project / ".claude" / "skills" / skill / "references" / "stack.md"
    ).exists()


def test_preset_stack_md_keeps_stack_content():
    joined = "\n".join(
        (ROOT / "presets/django-drf-react/skills" / s / "references/stack.md").read_text(
            encoding="utf-8"
        )
        for s in SKILLS
    )
    for needle in (
        "select_related", "on_commit", "CELERY_TASK_ALWAYS_EAGER", "factory_boy",
        "force_authenticate", "@testing-library/react-native", "manage.py showmigrations",
        "queryKey", "celery -A config inspect", "ota-update", "ruff check",
        "EncryptedTextField", "UserManager", "useState", "TanStack",
    ):
        assert needle in joined, needle


# --- T040: reviewer agents carry no stack -----------------------------------

AGENT_STACK_WORDS = re.compile(
    r"\b(django|celery|drf|react|mui|expo)\b|manage\.py|select_related|on_commit"
    r"|EncryptedTextField|permission_classes|get_queryset",
    re.IGNORECASE,
)
AGENT_READ_LINES = {
    "code-reviewer": (
        "If `references/stack.md` of the `requesting-code-review` skill exists, "
        "read it for stack-specific checks."
    ),
    "plan-document-reviewer": (
        "If `references/stack.md` of the `plan` skill exists, "
        "read it for stack-specific checks."
    ),
}


@pytest.mark.parametrize("agent", sorted(AGENT_READ_LINES))
def test_reviewer_agent_has_no_stack_words_and_reads_stack_md(agent):
    text = (ROOT / "agents" / f"{agent}.md").read_text(encoding="utf-8")
    assert AGENT_STACK_WORDS.findall(text) == []
    assert AGENT_READ_LINES[agent] in text


def test_code_reviewer_stack_sections_moved_to_preset():
    stack = (
        ROOT / "presets/django-drf-react/skills/requesting-code-review"
        / "references/stack.md"
    ).read_text(encoding="utf-8")
    for needle in (
        "### Django/DRF Patterns",
        "`transaction.on_commit()` used before Celery task dispatch",
        "### Celery Tasks",
        "Exponential backoff on retry",
        "### TypeScript/React",
        "No `useEffect` for data fetching (TanStack Query used)",
    ):
        assert needle in stack
