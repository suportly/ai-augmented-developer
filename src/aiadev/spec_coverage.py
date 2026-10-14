"""Scenario-to-task coverage: parser for a task's ``**Spec scenarios:**`` line.

``parse_scenario_refs`` is the single, pure parser shared by the coverage
check and ``task_context``. It reads the line's value (a leading
``**Spec scenarios:**`` label is tolerated) and returns a ``ScenarioRefs``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

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
