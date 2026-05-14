"""Layered TOML customization for skill defaults.

Implements Story 2 of ``specs/0014-bmad-inspired-evolutions/spec.md``:
three TOML layers — ``base.toml`` (skill-shipped) < ``team.toml``
(committed under ``_aiadev/``) < ``user.toml`` (gitignored under
``_aiadev/``) — are merged so user overrides team overrides base.

Public API (pinned by plan ADR-2):

    load_layer(path)                       -> dict
    merge_layers(base, team, user)         -> dict
    resolve(base_path, team_path, user_path) -> dict

Merge semantics:

* Tables (``dict``) deep-merge per-leaf.
* Arrays of tables identified by ``code`` or ``id`` use a
  position-preserving replace-or-append strategy.
* Other lists (scalar arrays, mismatched shapes) are wholesale
  replaced by the override.
* Scalars and unknown shapes follow last-writer-wins (user > team
  > base).

The merge is pure: inputs are never mutated; ``copy.deepcopy`` is used
for any value the result borrows from a layer.
"""
from __future__ import annotations

import copy
import re
import tomllib
from pathlib import Path
from typing import Any

_KEY_NAMES: tuple[str, ...] = ("code", "id")
_LINE_PATTERN = re.compile(r"line\s+(\d+)", re.IGNORECASE)


def load_layer(path: Path) -> dict[str, Any]:
    """Read a TOML file and return its parsed mapping.

    Wraps :class:`tomllib.TOMLDecodeError` as :class:`ValueError`
    annotated with ``<filename>:<line> — <original message>`` so the
    offending file and line number stay visible to the caller. The
    original tomllib message is preserved verbatim so downstream
    substring assertions (e.g. "table") keep working.

    Existence checks are the caller's responsibility; this function
    always reads from ``path``.
    """
    raw = path.read_text(encoding="utf-8")
    try:
        return tomllib.loads(raw)
    except tomllib.TOMLDecodeError as exc:
        original = str(exc)
        match = _LINE_PATTERN.search(original)
        line = match.group(1) if match else "?"
        raise ValueError(f"{path.name}:{line} — {original}") from exc


def merge_layers(
    base: dict[str, Any],
    team: dict[str, Any],
    user: dict[str, Any],
) -> dict[str, Any]:
    """Merge three layers in precedence order: user > team > base.

    Returns a fresh dict; never mutates any input. See module docstring
    for the per-shape semantics (deep-merge dicts, replace-or-append
    arrays of tables, replace other lists, override scalars).
    """
    result: dict[str, Any] = copy.deepcopy(base)
    result = _merge_dicts(result, team)
    result = _merge_dicts(result, user)
    return result


def resolve(
    base_path: Path,
    team_path: Path | None,
    user_path: Path | None,
) -> dict[str, Any]:
    """Load three layers from disk and return the merged result.

    Missing or ``None`` ``team_path`` / ``user_path`` arguments are
    treated as empty layers. Parse errors from :func:`load_layer`
    propagate verbatim so the ``file:line`` annotation reaches the
    caller.
    """
    base = load_layer(base_path)
    team = _load_optional(team_path)
    user = _load_optional(user_path)
    return merge_layers(base, team, user)


def _load_optional(path: Path | None) -> dict[str, Any]:
    """Return the parsed layer, or ``{}`` if the path is missing."""
    if path is None or not path.exists():
        return {}
    return load_layer(path)


def _merge_dicts(
    left: dict[str, Any],
    right: dict[str, Any],
) -> dict[str, Any]:
    """Return a new dict where ``right`` overrides ``left`` per-key.

    Recurses into nested dicts and dispatches to
    :func:`_merge_array_of_tables` when both sides hold a list whose
    elements are all dicts and at least one item carries a known match
    key (``code`` or ``id``). Other shapes follow override-wins.
    """
    merged: dict[str, Any] = copy.deepcopy(left)
    for key, right_value in right.items():
        if key not in merged:
            merged[key] = copy.deepcopy(right_value)
            continue
        left_value = merged[key]
        if isinstance(left_value, dict) and isinstance(right_value, dict):
            merged[key] = _merge_dicts(left_value, right_value)
        elif _is_array_of_tables(left_value) and _is_array_of_tables(right_value):
            merged[key] = _merge_array_of_tables(left_value, right_value)
        else:
            merged[key] = copy.deepcopy(right_value)
    return merged


def _is_array_of_tables(value: Any) -> bool:
    """Return ``True`` when ``value`` is a non-empty list of dicts."""
    return (
        isinstance(value, list)
        and len(value) > 0
        and all(isinstance(item, dict) for item in value)
    )


def _merge_array_of_tables(
    left: list[dict[str, Any]],
    right: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Replace-or-append merge keyed by ``code``/``id``.

    Walks ``left`` in order: each item is replaced (deep-merged) by the
    matching ``right`` entry when one exists, otherwise kept as-is.
    Items in ``right`` whose key did not match anything in ``left``
    are appended in their original order. Falls back to replacing the
    whole list when no shared match key is detected on either side.
    """
    match_key = _detect_match_key(left, right)
    if match_key is None:
        return copy.deepcopy(right)

    right_by_key: dict[Any, dict[str, Any]] = {}
    right_order: list[Any] = []
    for item in right:
        if match_key in item:
            key_value = item[match_key]
            if key_value not in right_by_key:
                right_order.append(key_value)
            right_by_key[key_value] = item

    merged: list[dict[str, Any]] = []
    consumed: set[Any] = set()
    for item in left:
        key_value = item.get(match_key)
        if key_value is not None and key_value in right_by_key:
            merged.append(_merge_dicts(item, right_by_key[key_value]))
            consumed.add(key_value)
        else:
            merged.append(copy.deepcopy(item))

    for key_value in right_order:
        if key_value in consumed:
            continue
        merged.append(copy.deepcopy(right_by_key[key_value]))
    return merged


def _detect_match_key(
    left: list[dict[str, Any]],
    right: list[dict[str, Any]],
) -> str | None:
    """Pick the first key in ``_KEY_NAMES`` that appears on both sides."""
    for candidate in _KEY_NAMES:
        if any(candidate in item for item in left) and any(
            candidate in item for item in right
        ):
            return candidate
    return None
