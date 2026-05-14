"""T010 (Story 4) — the ``help`` skill is state-aware.

The skill must inspect ``specs/`` via ``pipeline_state.recommend_next_command``
and prepend a ``Próximo passo:`` line to the verbatim reference table. A
``--plain`` flag (or ``AIADEV_HELP_PLAIN`` env truthy) opts out and falls
back to the legacy byte-for-byte ``cat`` of ``docs/pipeline-reference.md``.

These are *content* assertions on the SKILL.md file — the skill is a
Markdown directive read by the agent at runtime, not Python code. The
runtime behavior is exercised separately by ``test_pipeline_state.py``
(the underlying module) and by the e2e pipeline test.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "help" / "SKILL.md"


def _read_skill() -> str:
    return SKILL.read_text(encoding="utf-8")


def test_skill_calls_pipeline_state_recommend_next_command():
    body = _read_skill()
    assert "from aiadev.pipeline_state import recommend_next_command" in body, (
        "skill must invoke recommend_next_command from aiadev.pipeline_state"
    )
    assert "python -c" in body or "python3 -c" in body, (
        "skill must shell out to python -c to call the recommender"
    )


def test_skill_prepends_proximo_passo_line():
    body = _read_skill()
    assert "Próximo passo:" in body, (
        "skill must describe prepending a 'Próximo passo:' line before "
        "the verbatim reference (Story 4 AC-1..AC-5, AC-7)"
    )


def test_skill_documents_plain_flag():
    body = _read_skill()
    assert "--plain" in body, (
        "skill must document the --plain opt-out flag (Story 4 AC-6 / sc6)"
    )


def test_skill_documents_env_var_truthy_parsing():
    body = _read_skill()
    assert "AIADEV_HELP_PLAIN" in body, (
        "skill must mention the AIADEV_HELP_PLAIN env var (Story 4 sc6)"
    )
    # Truthy parsing list must appear somewhere in the skill.
    for token in ("1", "true", "yes", "on"):
        assert token in body, (
            f"skill must list '{token}' as a truthy AIADEV_HELP_PLAIN value"
        )


def test_skill_uses_git_branch_show_current_for_branch_scoping():
    body = _read_skill()
    assert "git branch --show-current" in body, (
        "skill must scope the recommendation to the current branch via "
        "`git branch --show-current` (Story 4 AC-8 / sc8)"
    )


def test_skill_remains_a_leaf():
    body = _read_skill()
    assert "Do not invoke any other skill" in body, (
        "help is still a leaf in the pipeline graph — calling a Python "
        "module is not invoking another skill"
    )


def test_skill_describes_all_done_handoff():
    body = _read_skill()
    # The recommender returns either /aiadev:requesting-code-review or
    # /aiadev:finishing-a-branch when all tasks are done. The skill itself
    # only needs to acknowledge the recommender owns this transition; it
    # does not have to enumerate the two commands. We assert at least one
    # of them is mentioned so reviewers have a anchor when reading.
    assert (
        "/aiadev:requesting-code-review" in body
        or "/aiadev:finishing-a-branch" in body
    ), (
        "skill must reference the all-done handoff target so readers can "
        "trace Story 4 AC-7 / sc7 from the skill body"
    )


def test_skill_preserves_verbatim_reference_default():
    body = _read_skill()
    assert "docs/pipeline-reference.md" in body, (
        "skill must still name the generated reference file"
    )
    assert "verbatim" in body.lower(), (
        "skill must still instruct verbatim return of the reference"
    )


def test_skill_under_one_hundred_lines():
    body = _read_skill()
    line_count = len(body.splitlines())
    assert line_count <= 100, (
        f"help SKILL.md must stay under 100 lines (got {line_count})"
    )


def test_skill_ends_with_trailing_newline():
    body = _read_skill()
    assert body.endswith("\n"), "SKILL.md must end with a trailing newline"
