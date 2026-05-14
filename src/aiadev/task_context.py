"""Compose per-task context files for the implement loop.

Implements Story 1 of ``specs/0014-bmad-inspired-evolutions/spec.md``:
the orchestrator can produce a self-contained per-task brief at
``<workspace>/specs/<branch>/task-context/<TID>-<slug>.md`` that the
implementer subagent reads instead of opening spec.md / plan.md /
tasks.md / source files individually.

Stdlib only. No I/O at import time.

The staleness check defaults to file mtime so consumers can run it in
any tree (no git repo required); the production wiring will swap in a
git-log probe via the injectable ``newest_modification`` callable.
"""
from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from typing import Callable, Iterable

from aiadev.review_log import branch_dir_for_workspace

_TEMPLATE_RELATIVE = Path("templates") / "task-context-template.md"

_EXCERPT_LINE_CAP = 40

_TDD_CHECKLIST_FALLBACK = (
    "- [ ] Write the failing test first; observe it failing for the "
    "right reason (RED).\n"
    "- [ ] Write the minimum code to make the test pass (GREEN).\n"
    "- [ ] Refactor while tests stay green.\n"
    "- [ ] Commit (one task = one commit)."
)

_TASK_HEADING_RE = re.compile(r"^### (T\d+)\s+[—-]\s+(.+?)\s*$")

_FILE_BULLET_RE = re.compile(
    r"^\s*-\s*(create|modify|test):\s*`?([^`\s]+)`?\s*$"
)

_SPEC_SCENARIOS_RE = re.compile(
    r"^\s*-\s*\*\*Spec scenarios:\*\*\s*(.+?)\s*$"
)

_STORY_HEADING_RE = re.compile(r"^###\s+Story\s+(\d+)\b")

_SCENARIO_LINE_RE = re.compile(r"^\s*(\d+)\.\s+(.*)$")

_SCENARIO_REF_RE = re.compile(r"sc(\d+)", re.IGNORECASE)

_STORY_REF_RE = re.compile(r"Story\s+(\d+)", re.IGNORECASE)


def compose(workspace_path: Path, task_id: str) -> Path:
    """Render the per-task context file and return its path.

    Reads spec.md, plan.md, tasks.md and the source files referenced
    by ``task_id``'s Files: list, slices each one to the relevant
    region, and writes the rendered template to
    ``<workspace>/specs/<branch>/task-context/<TID>-<slug>.md``.
    """
    branch_dir = branch_dir_for_workspace(workspace_path)
    tasks_text = (branch_dir / "tasks.md").read_text(encoding="utf-8")
    spec_text = (branch_dir / "spec.md").read_text(encoding="utf-8")
    plan_text = (branch_dir / "plan.md").read_text(encoding="utf-8")

    title, files, scenarios_line = _extract_task_block(tasks_text, task_id)
    spec_slice = _extract_spec_slice(spec_text, scenarios_line)
    plan_slice = _extract_plan_slice(plan_text, task_id)
    files_section = _render_files_section(workspace_path, files)
    tdd_checklist = _load_tdd_checklist()
    previous_pointer = _previous_task_pointer(branch_dir, task_id)

    template_path = _resolve_template_path(workspace_path)
    rendered = template_path.read_text(encoding="utf-8")

    branch_label = _branch_label(spec_text, branch_dir)
    spec_rel = "../spec.md"
    plan_rel = "../plan.md"

    rendered = (
        rendered
        .replace("{{TASK_ID}}", task_id)
        .replace("{{TASK_TITLE}}", title)
        .replace("{{BRANCH}}", branch_label)
        .replace("{{DATE}}", date.today().isoformat())
        .replace("{{SPEC_PATH}}", spec_rel)
        .replace("{{PLAN_PATH}}", plan_rel)
        .replace("{{SPEC_SLICE}}", spec_slice)
        .replace("{{PLAN_SLICE}}", plan_slice)
        .replace("{{FILES_TO_MODIFY_WITH_EXCERPTS}}", files_section)
        .replace("{{TDD_CHECKLIST}}", tdd_checklist)
        .replace("{{PREVIOUS_TASK_CONTEXT_POINTER}}", previous_pointer)
    )

    out_dir = branch_dir / "task-context"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{task_id}-{_slugify(title)}.md"
    if not rendered.endswith("\n"):
        rendered += "\n"
    out_path.write_text(rendered, encoding="utf-8")
    return out_path


def is_stale(
    task_context_path: Path,
    *,
    newest_modification: Callable[[Path], float] | None = None,
) -> bool:
    """Return True when any file referenced by the task-context is newer.

    The default probe reads filesystem mtime; production callers inject
    a git-log probe so the comparison reflects committed history rather
    than working-tree edits.
    """
    if newest_modification is None:
        newest_modification = lambda path: path.stat().st_mtime  # noqa: E731

    text = task_context_path.read_text(encoding="utf-8")
    workspace_root = _workspace_root_from_task_context(task_context_path)
    referenced = _referenced_files(text, workspace_root)
    base_mtime = task_context_path.stat().st_mtime
    for path in referenced:
        if not path.exists():
            continue
        if newest_modification(path) > base_mtime:
            return True
    return False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _extract_task_block(
    tasks_text: str, task_id: str
) -> tuple[str, list[tuple[str, str]], str]:
    """Return ``(title, files, scenarios_line)`` for ``task_id``."""
    lines = tasks_text.splitlines()
    start: int | None = None
    title = ""
    for index, line in enumerate(lines):
        match = _TASK_HEADING_RE.match(line)
        if match and match.group(1) == task_id:
            start = index
            title = match.group(2).strip()
            break
    if start is None:
        raise LookupError(f"task {task_id} not found in tasks.md")
    end = len(lines)
    for index in range(start + 1, len(lines)):
        if lines[index].startswith("### "):
            end = index
            break
    block = lines[start:end]
    files: list[tuple[str, str]] = []
    scenarios_line = ""
    for line in block:
        file_match = _FILE_BULLET_RE.match(line)
        if file_match:
            files.append((file_match.group(1), file_match.group(2)))
            continue
        scenarios_match = _SPEC_SCENARIOS_RE.match(line)
        if scenarios_match:
            scenarios_line = scenarios_match.group(1).strip()
    return title, files, scenarios_line


def _extract_spec_slice(spec_text: str, scenarios_line: str) -> str:
    """Return the bullet list of scenarios referenced by ``scenarios_line``."""
    if not scenarios_line:
        return "_No spec scenarios referenced by this task._"
    story_match = _STORY_REF_RE.search(scenarios_line)
    if not story_match:
        return "_Could not parse Spec scenarios line._"
    story_id = int(story_match.group(1))
    wanted = {int(match.group(1)) for match in _SCENARIO_REF_RE.finditer(scenarios_line)}
    if not wanted:
        return "_Could not parse Spec scenarios line._"

    scenarios = _scenarios_for_story(spec_text, story_id)
    bullets: list[str] = []
    for number, body in scenarios:
        if number in wanted:
            bullets.append(f"- {body}")
    if not bullets:
        return "_No matching scenarios found in spec.md._"
    return "\n".join(bullets)


def _scenarios_for_story(spec_text: str, story_id: int) -> list[tuple[int, str]]:
    """Yield ``(scenario_number, scenario_text)`` for the given story."""
    lines = spec_text.splitlines()
    in_story = False
    scenarios: list[tuple[int, str]] = []
    for line in lines:
        story_match = _STORY_HEADING_RE.match(line)
        if story_match:
            in_story = int(story_match.group(1)) == story_id
            continue
        if not in_story:
            continue
        if line.startswith("### ") or line.startswith("## "):
            break
        scenario_match = _SCENARIO_LINE_RE.match(line)
        if scenario_match:
            scenarios.append(
                (int(scenario_match.group(1)), scenario_match.group(2).strip())
            )
    return scenarios


def _extract_plan_slice(plan_text: str, task_id: str) -> str:
    """Return the plan.md block whose heading mentions ``task_id``."""
    lines = plan_text.splitlines()
    for index, line in enumerate(lines):
        if line.startswith("#### ") and task_id in line:
            end = len(lines)
            for forward in range(index + 1, len(lines)):
                if lines[forward].startswith("#### ") or lines[forward].startswith("### ") or lines[forward].startswith("## "):
                    end = forward
                    break
            return "\n".join(lines[index:end]).rstrip() + "\n"
    return f"_No plan.md block found for {task_id}._"


def _render_files_section(
    workspace_path: Path, files: Iterable[tuple[str, str]]
) -> str:
    """Render the Files section bullets, with capped excerpts for modify."""
    files = list(files)
    if not files:
        return "_No files declared for this task._"
    parts: list[str] = []
    for kind, rel_path in files:
        if kind == "modify":
            file_path = workspace_path / rel_path
            excerpt = _read_excerpt(file_path, _EXCERPT_LINE_CAP)
            parts.append(
                f"- modify: `{rel_path}`\n\n  ```\n{excerpt}\n  ```"
            )
        else:
            parts.append(f"- {kind}: `{rel_path}`")
    return "\n".join(parts)


def _read_excerpt(path: Path, cap: int) -> str:
    """Return up to ``cap`` lines from ``path`` indented for a code fence."""
    if not path.is_file():
        return "  (file not found)"
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()[:cap]
    return "\n".join(f"  {line}" for line in lines)


def _load_tdd_checklist() -> str:
    """Return a short TDD checklist (RED-GREEN-refactor-commit)."""
    return _TDD_CHECKLIST_FALLBACK


def _previous_task_pointer(branch_dir: Path, task_id: str) -> str:
    """Return a markdown link to the prior task-context file, or 'none'."""
    match = re.match(r"^T(\d+)$", task_id)
    if not match:
        return "none"
    current_number = int(match.group(1))
    if current_number <= 1:
        return "none"
    previous_id = f"T{current_number - 1:03d}"
    task_context_dir = branch_dir / "task-context"
    if not task_context_dir.is_dir():
        return "none"
    candidates = sorted(task_context_dir.glob(f"{previous_id}-*.md"))
    if not candidates:
        return "none"
    previous = candidates[0]
    return f"[{previous_id}](./{previous.name})"


def _slugify(title: str) -> str:
    """Return a lowercase, hyphenated slug derived from ``title``."""
    cleaned = re.sub(r"[^A-Za-z0-9]+", "-", title.lower()).strip("-")
    return cleaned or "task"


def _branch_label(spec_text: str, branch_dir: Path) -> str:
    """Return the branch label declared in spec.md, or the dir name."""
    for line in spec_text.splitlines():
        if line.startswith("**Branch:**"):
            value = line.split("**Branch:**", 1)[1].strip()
            return value.strip("`")
    return branch_dir.name


def _resolve_template_path(workspace_path: Path) -> Path:
    """Locate the task-context template, preferring the workspace copy."""
    workspace_template = workspace_path / _TEMPLATE_RELATIVE
    if workspace_template.is_file():
        return workspace_template
    repo_root = Path(__file__).resolve().parents[2]
    return repo_root / _TEMPLATE_RELATIVE


def _workspace_root_from_task_context(task_context_path: Path) -> Path:
    """Return the workspace root above ``specs/<branch>/task-context/<file>``."""
    return task_context_path.resolve().parents[3]


def _referenced_files(text: str, workspace_root: Path) -> list[Path]:
    """Return absolute paths for every file mentioned in the Files section."""
    paths: list[Path] = []
    in_section = False
    for line in text.splitlines():
        if line.startswith("<!-- section: files -->"):
            in_section = True
            continue
        if in_section and line.startswith("<!-- section: "):
            break
        if not in_section:
            continue
        match = re.match(r"^\s*-\s*(create|modify|test):\s*`([^`]+)`", line)
        if match:
            paths.append(workspace_root / match.group(2))
    return paths
