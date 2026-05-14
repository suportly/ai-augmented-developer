"""RED tests for ``aiadev.customization``.

Covers Story 2 acceptance criteria sc2..sc5 from
``specs/0014-bmad-inspired-evolutions/spec.md``:

  - sc2: arrays of tables matched by ``code``/``id`` replace-or-append
    in correct order.
  - sc3: scalar precedence is user > team > base.
  - sc4: parse error in any layer aborts with a ``file:line`` reference.
  - sc5: overrides apply to extension-sourced skills.

(sc1 — install creates ``_aiadev/team.toml`` and the ``.gitignore`` line —
is covered separately by T014.)

Plan ADR-2 pins the public API for T013 GREEN:

    merge_layers(base: dict, team: dict, user: dict) -> dict
    load_layer(path: Path) -> dict
    resolve(base_path: Path,
            team_path: Path | None,
            user_path: Path | None) -> dict

The module ``aiadev.customization`` does not exist yet — every test in
this file MUST fail at import time with ``ModuleNotFoundError`` until
T013 lands. See ``.claude/rules/testing.md``: write the test first.
"""
from __future__ import annotations

import copy
import json
import re
import time
import tomllib
from pathlib import Path

import pytest

from aiadev.customization import (  # noqa: E402  RED: module does not exist yet
    load_layer,
    merge_layers,
    resolve,
)

FIXTURES = Path(__file__).parent / "fixtures" / "customization"


def _load_fixture(name: str) -> tuple[dict, dict, dict, dict]:
    """Read ``base.toml`` + ``team.toml`` + ``user.toml`` + ``expected.json``."""
    fixture_dir = FIXTURES / name
    base = tomllib.loads((fixture_dir / "base.toml").read_text(encoding="utf-8"))
    team = tomllib.loads((fixture_dir / "team.toml").read_text(encoding="utf-8"))
    user = tomllib.loads((fixture_dir / "user.toml").read_text(encoding="utf-8"))
    expected = json.loads((fixture_dir / "expected.json").read_text(encoding="utf-8"))
    return base, team, user, expected


# ---------------------------------------------------------------------------
# sc2 + sc3 + sc5: success-path detector parametrize over fixture scenarios.
# Each row pins one layered-merge invariant from the spec. The `passthrough`
# fixture also covers the empty team/user no-op edge inside the loop.
# ---------------------------------------------------------------------------

MERGE_FIXTURE_CASES = [
    # sc3: scalar precedence user > team > base.
    pytest.param("scalar_override", id="scalar_override"),
    # sc3 (table form): nested tables deep-merge per-leaf.
    pytest.param("table_deep_merge", id="table_deep_merge"),
    # sc2: arrays of tables match by code/id then replace-or-append in order.
    pytest.param("array_replace_or_append", id="array_replace_or_append"),
    # sc3 (no-op): empty team + empty user passes base through unchanged.
    pytest.param("passthrough", id="passthrough"),
    # sc5: extension-sourced base still respects team overrides.
    pytest.param("extension_override", id="extension_override"),
]


@pytest.mark.parametrize("fixture_name", MERGE_FIXTURE_CASES)
def test_merge_layers_matches_expected_for_fixture(fixture_name: str) -> None:
    base, team, user, expected = _load_fixture(fixture_name)

    result = merge_layers(base, team, user)

    assert result == expected, (
        f"fixture {fixture_name!r}: merged result {result!r} "
        f"does not match expected {expected!r}"
    )


# ---------------------------------------------------------------------------
# sc4: parse error in any layer aborts with a ``file:line`` reference.
# The ``parse_error`` fixture has a malformed ``team.toml``; the loader must
# surface the file name AND the offending line number.
# ---------------------------------------------------------------------------


def test_load_layer_raises_with_file_and_line_on_parse_error() -> None:
    fixture_dir = FIXTURES / "parse_error"
    expected = json.loads((fixture_dir / "expected.json").read_text(encoding="utf-8"))
    bad_path = fixture_dir / expected["error_file"]

    # Pin the exception type to (TOMLDecodeError, ValueError) so a
    # regression that raises e.g. FileNotFoundError isn't masked.
    # `match=` enforces the file-name presence on the message; the
    # substring + line-window assertions below give specific failure
    # messages when one fact is missing.
    with pytest.raises(
        (tomllib.TOMLDecodeError, ValueError),
        match=re.escape(expected["error_file"]),
    ) as excinfo:
        load_layer(bad_path)

    message = str(excinfo.value)

    assert expected["error_file"] in message, (
        f"parse error message must reference the file name "
        f"{expected['error_file']!r}, got {message!r}"
    )
    assert expected["error_substring"] in message.lower(), (
        f"parse error message must mention the issue "
        f"{expected['error_substring']!r}, got {message!r}"
    )

    # The message must include some line number within the expected window.
    line_min = int(expected["error_line_min"])
    line_max = int(expected["error_line_max"])
    found_line = False
    for candidate in range(line_min, line_max + 1):
        if f":{candidate}" in message or f"line {candidate}" in message:
            found_line = True
            break
    assert found_line, (
        f"parse error message must include a line number in "
        f"[{line_min}, {line_max}] (as ':<n>' or 'line <n>'), got {message!r}"
    )


# ---------------------------------------------------------------------------
# Resolver convenience: ``resolve(base_path, team_path, user_path)`` must
# load + merge in one call and return the same result as direct merge_layers.
# ---------------------------------------------------------------------------


def test_resolve_high_level_helper_matches_direct_merge_for_scalar_override() -> None:
    fixture_dir = FIXTURES / "scalar_override"
    base, team, user, _expected = _load_fixture("scalar_override")
    direct = merge_layers(base, team, user)

    via_resolve = resolve(
        fixture_dir / "base.toml",
        fixture_dir / "team.toml",
        fixture_dir / "user.toml",
    )

    assert via_resolve == direct, (
        f"resolve() must agree with merge_layers(): "
        f"resolve={via_resolve!r}, direct={direct!r}"
    )


def test_resolve_treats_missing_team_and_user_paths_as_empty_layers() -> None:
    fixture_dir = FIXTURES / "passthrough"
    base, _team, _user, expected = _load_fixture("passthrough")

    via_resolve = resolve(fixture_dir / "base.toml", None, None)

    assert via_resolve == expected, (
        f"resolve() with no team/user must equal base alone: "
        f"resolve={via_resolve!r}, expected={expected!r}"
    )
    assert via_resolve == base, (
        f"resolve() with no team/user must equal raw base: "
        f"resolve={via_resolve!r}, base={base!r}"
    )


# ---------------------------------------------------------------------------
# Edge cases on merge_layers: empty layers and mutation safety.
# ---------------------------------------------------------------------------


def test_merge_layers_returns_empty_dict_when_all_layers_are_empty() -> None:
    result = merge_layers({}, {}, {})

    assert result == {}, f"merge of three empty layers must be empty, got {result!r}"


def test_merge_layers_returns_deep_copy_of_base_when_team_and_user_are_empty() -> None:
    base = {"default_model": "sonnet", "skill": {"config": {"timeout": 30}}}

    result = merge_layers(base, {}, {})

    assert result == base, f"empty overlays must yield base verbatim, got {result!r}"
    assert result is not base, "result must be a fresh dict, not a base alias"
    assert result["skill"] is not base["skill"], (
        "nested tables must be deep-copied (not aliased) to keep merge_layers pure"
    )


def test_merge_layers_does_not_mutate_any_input_layer() -> None:
    base, team, user, _expected = _load_fixture("array_replace_or_append")
    base_snapshot = copy.deepcopy(base)
    team_snapshot = copy.deepcopy(team)
    user_snapshot = copy.deepcopy(user)

    merge_layers(base, team, user)

    assert base == base_snapshot, (
        f"merge_layers mutated `base`: before={base_snapshot!r}, after={base!r}"
    )
    assert team == team_snapshot, (
        f"merge_layers mutated `team`: before={team_snapshot!r}, after={team!r}"
    )
    assert user == user_snapshot, (
        f"merge_layers mutated `user`: before={user_snapshot!r}, after={user!r}"
    )


# ---------------------------------------------------------------------------
# Performance: ≤ 50 ms for ~200 keys across 3 layers (plan ADR-2 budget).
# ---------------------------------------------------------------------------


def _build_synthetic_layer(prefix: str, key_count: int) -> dict:
    """Build a flat-ish dict with `key_count` total scalar leaves."""
    layer: dict = {}
    # Half the keys are plain scalars; the other half nest one table deep
    # to exercise the recursive merge path.
    half = key_count // 2
    for i in range(half):
        layer[f"{prefix}_scalar_{i}"] = f"{prefix}-value-{i}"
    nested: dict = {}
    for i in range(key_count - half):
        nested[f"{prefix}_nested_{i}"] = i
    layer["section"] = nested
    return layer


@pytest.mark.perf
def test_merge_layers_meets_50ms_budget_on_200_keys() -> None:
    base = _build_synthetic_layer("base", 200)
    team = _build_synthetic_layer("team", 200)
    user = _build_synthetic_layer("user", 200)

    start = time.perf_counter()
    result = merge_layers(base, team, user)
    duration = time.perf_counter() - start

    assert isinstance(result, dict), f"expected dict, got {type(result).__name__}"
    assert duration < 0.050, (
        f"merge_layers took {duration * 1000:.1f} ms; budget is 50 ms"
    )
