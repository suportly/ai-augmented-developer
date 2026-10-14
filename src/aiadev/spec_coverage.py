"""Scenario-to-task coverage: parser for a task's ``**Spec scenarios:**`` line.

``parse_scenario_refs`` is the single, pure parser shared by the coverage
check and ``task_context``. It reads the line's value (a leading
``**Spec scenarios:**`` label is tolerated) and returns a ``ScenarioRefs``.
``check`` compares a spec with a tasks file and returns ``CoverageIssue`` items.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

# A range wider than this keeps only its endpoints: a typo such as
# ``1-100000`` must not allocate. The limit errs toward "uncovered": the
# dropped middle scenarios surface as coverage errors, never as false cover.
MAX_RANGE_SPAN = 1000

_ITEM = r"\d+(?:\s*[–—-]\s*\d+)?"
_TOKEN_RE = re.compile(
    rf"""
    (?P<story>\bstory\s+(?P<story_n>\d+))
  | (?P<crit>\bsuccess\s+criteri(?:on|a)\s*(?P<crit_list>\#?\d+(?:\s*(?:,|and|&)\s*\#?\d+)*))
  | (?P<scen>\bscenarios?\s+(?P<scen_list>{_ITEM}(?:\s*(?:,|and|&)\s*{_ITEM})*))
  | (?P<legacy>\bsc(?P<legacy_n>\d+))
  | (?P<sep>;)
    """,
    re.IGNORECASE | re.VERBOSE,
)
_ITEM_RE = re.compile(r"(\d+)(?:\s*[–—-]\s*(\d+))?")
_LABEL_RE = re.compile(r"^[\s*_\-]*spec\s+scenarios[\s*_:]*", re.IGNORECASE)
# A value that opens with a dash or "n/a" names no scenario; only an explicit
# ``Success criterion #N`` counts, the rest is commentary.
_NONE_RE = re.compile(r"^(?:[–—-]|n/?a\b)", re.IGNORECASE)


@dataclass(frozen=True)
class ScenarioRefs:
    """What a task line cites.

    ``scenarios``: story -> cited scenario numbers. ``whole_stories``: stories
    cited alone (they cover every scenario). ``orphan_scenarios``: scenario
    numbers with no story before them; they cover nothing, so they do not make
    ``has_reference`` true (T018 decides the message). ``criteria``:
    ``Success criterion #N``.
    """

    scenarios: dict[int, frozenset[int]] = field(default_factory=dict)
    whole_stories: frozenset[int] = frozenset()
    orphan_scenarios: frozenset[int] = frozenset()
    criteria: frozenset[int] = frozenset()

    @property
    def has_reference(self) -> bool:
        return bool(self.scenarios or self.whole_stories or self.criteria)


def _numbers(text: str) -> set[int]:
    """Expand ``1, 3–5`` into numbers; zero is dropped (scenarios are 1-based)."""
    found: set[int] = set()
    for match in _ITEM_RE.finditer(text):
        low = int(match.group(1))
        high = int(match.group(2)) if match.group(2) else low
        low, high = min(low, high), max(low, high)
        if high - low > MAX_RANGE_SPAN:
            found.update((low, high))
        else:
            found.update(range(low, high + 1))
    found.discard(0)
    return found


def parse_scenario_refs(line: str) -> ScenarioRefs:
    """Parse the value of a ``**Spec scenarios:**`` line; never raises."""
    text = _LABEL_RE.sub("", line.strip(), count=1)
    scenarios: dict[int, set[int]] = {}
    mentioned: set[int] = set()
    orphans: set[int] = set()
    criteria: set[int] = set()
    story: int | None = None
    pending: int | None = None  # story cited so far without a scenario
    only_criteria = bool(_NONE_RE.match(text))

    def flush() -> None:
        nonlocal pending
        if pending is not None:
            mentioned.add(pending)
            pending = None

    def add(numbers: set[int]) -> None:
        if not numbers:
            return
        if story is None:
            orphans.update(numbers)
        else:
            scenarios.setdefault(story, set()).update(numbers)
            nonlocal pending
            pending = None

    for match in _TOKEN_RE.finditer(text):
        if match.group("crit"):
            criteria.update(_numbers(match.group("crit_list").replace("#", "")))
        elif only_criteria:
            continue
        elif match.group("story"):
            flush()
            story = int(match.group("story_n")) or None
            pending = story
        elif match.group("scen"):
            add(_numbers(match.group("scen_list")))
        elif match.group("legacy"):
            add({int(match.group("legacy_n"))} - {0})
        else:  # ";" closes the group: a following scenario no longer binds
            flush()
            story = None
    flush()

    return ScenarioRefs(
        scenarios={s: frozenset(n) for s, n in scenarios.items()},
        whole_stories=frozenset(mentioned),
        orphan_scenarios=frozenset(orphans),
        criteria=frozenset(criteria),
    )


_STORY_HEADING_RE = re.compile(r"^###\s+Story\s+(\d+)\b")
_SCENARIO_LINE_RE = re.compile(r"^\s*(\d+)\.\s+\S")
_TASK_HEADING_RE = re.compile(r"^###\s+(T\d+)\b")
_TASK_SCENARIOS_RE = re.compile(r"^\s*-\s*\*\*Spec scenarios:\*\*\s*(.*?)\s*$")


@dataclass(frozen=True)
class CoverageIssue:
    """One coverage problem.

    ``kind``: ``uncovered_scenario`` | ``orphan_task`` | ``unknown_reference``
    | ``unknown_criterion``. ``ref`` is the scenario, task id or citation at
    fault; ``task`` is the citing task, when there is one.
    """

    kind: str
    ref: str
    message: str
    task: str | None = None


def spec_scenarios(spec_text: str) -> dict[int, list[int]]:
    """Story number -> numbered acceptance scenarios under its ``### Story N``."""
    stories: dict[int, list[int]] = {}
    current: list[int] | None = None
    for line in spec_text.splitlines():
        heading = _STORY_HEADING_RE.match(line)
        if heading:
            current = stories.setdefault(int(heading.group(1)), [])
        elif line.startswith("## ") or line.startswith("### "):
            current = None
        elif current is not None:
            scenario = _SCENARIO_LINE_RE.match(line)
            if scenario:
                current.append(int(scenario.group(1)))
    return stories


def _criteria_count(spec_text: str) -> int:
    """Top-level bullets under ``## Success criteria`` (N = bullet order)."""
    in_section = False
    count = 0
    for line in spec_text.splitlines():
        if line.startswith("## "):
            in_section = line[3:].strip().lower() == "success criteria"
        elif in_section and re.match(r"^[-*]\s+\S", line):
            count += 1
    return count


def _task_lines(tasks_text: str) -> list[tuple[str, str | None]]:
    """``(task_id, spec scenarios value or None)`` for every ``### T0NN`` block."""
    tasks: list[tuple[str, str | None]] = []
    for line in tasks_text.splitlines():
        heading = _TASK_HEADING_RE.match(line)
        if heading:
            tasks.append((heading.group(1), None))
            continue
        match = _TASK_SCENARIOS_RE.match(line)
        if match and tasks and tasks[-1][1] is None:
            tasks[-1] = (tasks[-1][0], match.group(1))
    return tasks


def check(spec_path: Path, tasks_path: Path) -> list[CoverageIssue]:
    """Check scenario-to-task coverage; raises ``FileNotFoundError`` for a missing file."""
    texts: list[str] = []
    for path in (Path(spec_path), Path(tasks_path)):
        if not path.is_file():
            raise FileNotFoundError(f"{path.name} not found: {path}")
        texts.append(path.read_text(encoding="utf-8"))
    spec_text, tasks_text = texts
    stories = spec_scenarios(spec_text)
    criteria = _criteria_count(spec_text)

    issues: list[CoverageIssue] = []
    covered: set[tuple[int, int]] = set()
    for task_id, value in _task_lines(tasks_text):
        refs = parse_scenario_refs(value or "")
        if not refs.has_reference:
            issues.append(CoverageIssue(
                "orphan_task", task_id,
                f"{task_id} cites no scenario, story or Success criterion #N",
                task_id,
            ))
        for story in sorted(refs.whole_stories):
            if story in stories:
                covered.update((story, n) for n in stories[story])
            else:
                issues.append(_unknown(task_id, f"Story {story}"))
        for story, numbers in sorted(refs.scenarios.items()):
            for number in sorted(numbers):
                if number in stories.get(story, ()):
                    covered.add((story, number))
                else:
                    issues.append(_unknown(task_id, f"Story {story} scenario {number}"))
        for number in sorted(refs.criteria):
            if not 1 <= number <= criteria:
                issues.append(CoverageIssue(
                    "unknown_criterion", f"Success criterion #{number}",
                    f"{task_id} cites Success criterion #{number}, "
                    f"but the spec has {criteria}",
                    task_id,
                ))
    for story, numbers in sorted(stories.items()):
        for number in numbers:
            if (story, number) not in covered:
                ref = f"Story {story} scenario {number}"
                issues.append(CoverageIssue(
                    "uncovered_scenario", ref, f"{ref} is cited by no task",
                ))
    return issues


def _unknown(task_id: str, ref: str) -> CoverageIssue:
    return CoverageIssue(
        "unknown_reference", ref, f"{task_id} cites {ref}, which is not in the spec", task_id
    )


def load_exceptions(path: Path) -> dict[str, str]:
    """Read ``coverage-exceptions.yaml`` (feature -> reason); missing file -> ``{}``.

    The file belongs to this repository (``docs/``); a consumer project has
    none, so the coverage gate applies to all of its features.

    Raises ``ValueError`` when the file is not a mapping or a reason is not a
    non-empty string.
    """
    path = Path(path)
    if not path.is_file():
        return {}
    import yaml  # local import keeps the module import-cheap

    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ValueError(f"{path.name}: invalid YAML ({exc})") from exc
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError(f"{path.name}: expected a mapping of feature -> reason")
    for feature, reason in data.items():
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError(f"{path.name}: {feature!r} needs a non-empty reason")
    return {str(k): v for k, v in data.items()}
