"""RED tests for ``aiadev.task_context`` (Story 1, spec 0014).

Covers Story 1 acceptance criteria AC-1 (compose produces the
task-context file with all five sub-items) and AC-4 (staleness
detection) from ``specs/0014-bmad-inspired-evolutions/spec.md``.

AC-2 and AC-3 are content-tests on ``skills/implement/SKILL.md`` and
belong to T019 — not exercised here.

The module ``aiadev.task_context`` does not exist yet — every test in
this file MUST fail at import time with ``ModuleNotFoundError`` until
T018 lands. See ``.claude/rules/testing.md``: write the test first.

Production note: the staleness check in ``aiadev.task_context`` uses
``git log -- <file>`` to find the newest commit touching each
referenced file. The tests below override that with file mtime via the
injectable ``newest_modification`` callable so the suite stays
hermetic — no git repo required inside ``tmp_path``.
"""
from __future__ import annotations

import os
import shutil
import time
from pathlib import Path
from typing import Callable

import pytest

from aiadev.task_context import compose, is_stale  # noqa: E402  RED: module does not exist yet

FIXTURES = Path(__file__).parent / "fixtures" / "task_context"
SAMPLE = FIXTURES / "sample"
BRANCH = "feature/x"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    """Copy the sample mini-project into a writable tmpdir.

    The staleness tests mutate file mtimes; copying isolates each run.
    """
    dest = tmp_path / "workspace"
    shutil.copytree(SAMPLE, dest)
    return dest


def _compose_path(workspace_root: Path, task_id: str) -> Path:
    """Resolve the single task-context file matching ``task_id``."""
    task_context_dir = workspace_root / "specs" / "0001-x" / "task-context"
    matches = sorted(task_context_dir.glob(f"{task_id}-*.md"))
    assert matches, f"no task-context file for {task_id} in {task_context_dir}"
    assert len(matches) == 1, f"expected exactly one match, got {matches!r}"
    return matches[0]


# ---------------------------------------------------------------------------
# AC-1: compose produces the task-context file with all five sub-items.
# ---------------------------------------------------------------------------


def test_compose_creates_task_context_file_at_expected_path(
    workspace: Path,
) -> None:
    result = compose(workspace, "T002")

    expected_dir = workspace / "specs" / "0001-x" / "task-context"
    assert result.exists(), f"compose did not create {result}"
    assert result.parent == expected_dir, (
        f"task-context file should live in {expected_dir}, got {result.parent}"
    )
    assert result.name.startswith("T002-"), (
        f"file name should start with 'T002-', got {result.name!r}"
    )
    assert result.suffix == ".md", f"expected .md extension, got {result.suffix!r}"


def test_compose_includes_spec_slice_for_task(workspace: Path) -> None:
    result = compose(workspace, "T002")

    rendered = result.read_text(encoding="utf-8")
    assert "story-1-scenario-1-marker" in rendered, (
        "spec slice must include Story 1 sc1 (referenced by T002)"
    )
    assert "story-1-scenario-2-marker" in rendered, (
        "spec slice must include Story 1 sc2 (referenced by T002)"
    )
    assert "story-1-scenario-3-marker" not in rendered, (
        "spec slice must NOT include Story 1 sc3 (not referenced by T002)"
    )
    assert "story-2-scenario-1-marker" not in rendered, (
        "spec slice must NOT include Story 2 sc1 (other story)"
    )


def test_compose_includes_plan_slice_for_task(workspace: Path) -> None:
    result = compose(workspace, "T002")

    rendered = result.read_text(encoding="utf-8")
    assert "T002-plan-marker" in rendered, (
        "plan slice must include the T002 block from plan.md"
    )
    assert "T001-plan-marker" not in rendered, (
        "plan slice must NOT include unrelated T001 block"
    )
    assert "T003-plan-marker" not in rendered, (
        "plan slice must NOT include unrelated T003 block"
    )


def test_compose_includes_modify_excerpt_capped_at_40_lines(
    workspace: Path,
) -> None:
    result = compose(workspace, "T002")

    rendered = result.read_text(encoding="utf-8")
    # T002 references `modify: src/foo.py`, a 60-line file. The excerpt
    # the helper pastes for that file must be capped at 40 lines.
    foo_source = (workspace / "src" / "foo.py").read_text(encoding="utf-8")
    foo_lines = foo_source.splitlines()
    assert len(foo_lines) > 40, (
        f"sanity: fixture src/foo.py should be >40 lines, got {len(foo_lines)}"
    )

    # The rendered file must contain at least the first line of foo.py
    # (so we know an excerpt was included), but must NOT contain the
    # last line (line 60-ish) because the cap kicked in.
    assert foo_lines[0] in rendered, (
        f"expected first line of foo.py {foo_lines[0]!r} in excerpt"
    )
    last_line = foo_lines[-1]
    # The very last line of the file is the closing of `hello()`. If it
    # made it past the cap, the cap is broken.
    assert last_line not in rendered, (
        f"line {len(foo_lines)} of foo.py {last_line!r} appeared in "
        f"excerpt — the 40-line cap is broken"
    )


def test_compose_lists_create_and_test_paths_without_excerpt(
    workspace: Path,
) -> None:
    result = compose(workspace, "T003")

    rendered = result.read_text(encoding="utf-8")
    # T003: create src/bar.py + test tests/test_bar.py.
    assert "src/bar.py" in rendered, (
        "task-context for T003 must list the create: path"
    )
    assert "tests/test_bar.py" in rendered, (
        "task-context for T003 must list the test: path"
    )

    # No excerpt for the create: path — the file does not exist yet.
    bar_path = workspace / "src" / "bar.py"
    assert not bar_path.exists(), "fixture sanity: src/bar.py must NOT exist"
    # Heuristic: a real excerpt block would include a code fence right
    # after the create: path mention. Look for the path followed by a
    # nearby fenced code block; assert it is absent.
    bar_index = rendered.find("src/bar.py")
    nearby = rendered[bar_index : bar_index + 200]
    assert "```" not in nearby, (
        f"create: path must not be followed by a code-fenced excerpt; "
        f"nearby slice was {nearby!r}"
    )


def test_compose_includes_tdd_checklist(workspace: Path) -> None:
    result = compose(workspace, "T002")

    rendered = result.read_text(encoding="utf-8").lower()
    # The TDD checklist must mention the canonical RED→GREEN cycle.
    # We don't pin exact wording — just the keywords the implementer
    # needs to recognise the rule set.
    keywords = ("red", "green", "test")
    for keyword in keywords:
        assert keyword in rendered, (
            f"TDD checklist must mention {keyword!r}; rendered does not"
        )


def test_compose_points_to_previous_task_context_when_present(
    workspace: Path,
) -> None:
    # Pre-create the T001 task-context so T002's compose can point at it.
    task_context_dir = workspace / "specs" / "0001-x" / "task-context"
    task_context_dir.mkdir(parents=True, exist_ok=True)
    previous = task_context_dir / "T001-bootstrap.md"
    previous.write_text("# placeholder T001\n", encoding="utf-8")

    result = compose(workspace, "T002")

    rendered = result.read_text(encoding="utf-8")
    assert "T001-bootstrap.md" in rendered, (
        "previous-task-context section must reference the T001 file"
    )


def test_compose_first_task_has_none_for_previous_pointer(
    workspace: Path,
) -> None:
    # Fresh workspace: no prior task-context file exists.
    task_context_dir = workspace / "specs" / "0001-x" / "task-context"
    assert not task_context_dir.exists() or not list(task_context_dir.glob("T*.md")), (
        "fixture sanity: no prior task-context files for first compose"
    )

    result = compose(workspace, "T001")

    rendered = result.read_text(encoding="utf-8").lower()
    assert "none" in rendered, (
        "previous-task-context section must say 'none' for the first task"
    )


# ---------------------------------------------------------------------------
# AC-4: staleness detection.
# ---------------------------------------------------------------------------


def _newest_mtime(path: Path) -> float:
    """Test-only fake of the production git-log probe: just use mtime."""
    return path.stat().st_mtime


def test_is_stale_returns_false_when_task_context_newer_than_referenced_files(
    workspace: Path,
) -> None:
    task_context_path = compose(workspace, "T002")

    # Force the task-context file mtime to be strictly newer than the
    # referenced source files.
    foo = workspace / "src" / "foo.py"
    older = time.time() - 60
    os.utime(foo, (older, older))
    newer = time.time()
    os.utime(task_context_path, (newer, newer))

    stale = is_stale(task_context_path, newest_modification=_newest_mtime)

    assert stale is False, (
        f"is_stale must return False when task-context is newer than "
        f"all referenced files; got {stale!r}"
    )


def test_is_stale_returns_true_when_referenced_file_modified_after_task_context(
    workspace: Path,
) -> None:
    task_context_path = compose(workspace, "T002")

    # Force the task-context file mtime to be older than src/foo.py.
    older = time.time() - 60
    os.utime(task_context_path, (older, older))
    foo = workspace / "src" / "foo.py"
    newer = time.time()
    os.utime(foo, (newer, newer))

    stale = is_stale(task_context_path, newest_modification=_newest_mtime)

    assert stale is True, (
        f"is_stale must return True when a referenced file is newer "
        f"than the task-context; got {stale!r}"
    )


def test_is_stale_accepts_injectable_newest_modification_callable(
    workspace: Path,
) -> None:
    task_context_path = compose(workspace, "T002")

    # Callable signature contract: (Path) -> float (epoch seconds).
    fake: Callable[[Path], float] = lambda _path: time.time() + 3600  # noqa: E731

    stale = is_stale(task_context_path, newest_modification=fake)

    # An injected probe that always reports "one hour in the future"
    # must mark the task-context as stale.
    assert stale is True, (
        "is_stale must honour the injected newest_modification callable; "
        f"got {stale!r}"
    )
