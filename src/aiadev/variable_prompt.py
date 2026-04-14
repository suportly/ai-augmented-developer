"""Variable collection for ``aiadev install``.

The CLI resolves a preset's variable values from three sources, in
descending priority:

1. **CLI flags** — ``--vars KEY=VAL,KEY2=VAL2``. Always wins when set.
2. **Previous install** — the manifest's ``variables`` dict for the same
   preset. Lets re-installs skip prompts for values the user already
   provided.
3. **Preset defaults** — the ``default:`` field declared on each
   variable in ``preset.yaml``.

If, after merging those three, a variable still has no value **and** the
caller is running in interactive mode, ``click.prompt`` asks the user.
In non-interactive mode a missing required variable is a hard error
that names the missing key.
"""
from __future__ import annotations

from typing import Mapping

import click


class VariableError(RuntimeError):
    """Raised when variable collection fails (missing required, duplicate key, …)."""


def parse_cli_vars(raw: str | None) -> dict[str, str]:
    """Parse ``--vars KEY=VAL,KEY2=VAL2`` into a dict.

    Limitations (documented for users):

    * Values may not contain literal commas. If you need to pass one,
      repeat ``--vars`` (the CLI wrapper joins multiple invocations).
    * Whitespace around ``,`` and around ``=`` is stripped.
    * Duplicate keys raise :class:`VariableError`.
    * Empty string or ``None`` returns an empty dict.
    """
    if not raw:
        return {}
    result: dict[str, str] = {}
    for entry in raw.split(","):
        entry = entry.strip()
        if not entry:
            continue
        if "=" not in entry:
            raise VariableError(f"invalid --vars entry (expected KEY=VALUE): {entry!r}")
        key, _, value = entry.partition("=")
        key = key.strip()
        if not key:
            raise VariableError(f"empty key in --vars entry: {entry!r}")
        if key in result:
            raise VariableError(f"duplicate key in --vars: {key}")
        result[key] = value.strip()
    return result


def merge_vars_strings(raws: list[str]) -> dict[str, str]:
    """Parse multiple ``--vars`` invocations and merge them left-to-right.

    Later invocations override earlier ones for the same key, allowing
    the pattern ``--vars A=1 --vars A=2`` to end up with ``A=2``.
    Duplicate keys inside a single invocation still raise.
    """
    merged: dict[str, str] = {}
    for raw in raws:
        merged.update(parse_cli_vars(raw))
    return merged


def collect(
    preset_vars: list[Mapping[str, object]],
    *,
    previous: Mapping[str, str] | None = None,
    cli_vars: Mapping[str, str] | None = None,
    non_interactive: bool = False,
    prompt_func=click.prompt,  # Injectable for tests.
) -> dict[str, str]:
    """Resolve every variable declared by the preset.

    ``preset_vars`` is the list that appears under ``variables:`` in
    ``preset.yaml``. Each entry is expected to be a mapping with at
    least ``name``; optional keys ``prompt``, ``default``, ``required``.
    """
    previous = dict(previous or {})
    cli_vars = dict(cli_vars or {})
    resolved: dict[str, str] = {}

    for entry in preset_vars:
        name = entry.get("name")
        if not name or not isinstance(name, str):
            raise VariableError(f"preset variable without a name: {entry!r}")
        required = bool(entry.get("required", False))
        preset_default = entry.get("default")
        prompt_text = entry.get("prompt", name)

        if name in cli_vars:
            resolved[name] = cli_vars[name]
            continue
        if name in previous:
            default_for_prompt = previous[name]
        elif preset_default is not None:
            default_for_prompt = str(preset_default)
        else:
            default_for_prompt = None

        if non_interactive:
            if default_for_prompt is None:
                if required:
                    raise VariableError(
                        f"--non-interactive: required variable {name!r} has no "
                        "value (not in --vars, not in manifest, no default)"
                    )
                resolved[name] = ""
            else:
                resolved[name] = default_for_prompt
            continue

        # Interactive branch.
        answer = prompt_func(
            prompt_text,
            default=default_for_prompt if default_for_prompt is not None else "",
            show_default=default_for_prompt is not None,
        )
        if required and not answer and default_for_prompt in (None, ""):
            raise VariableError(f"required variable {name!r} cannot be empty")
        resolved[name] = answer

    return resolved
