"""Placeholder substitution helpers shared by the install engine.

The framework's templates and preset files use ``{{UPPER_SNAKE}}``
placeholders. This module exposes two pure functions so that the
engine can render a file and, separately, verify that no placeholder
survived.

Design notes recorded in ``specs/feature-install-interactive/plan.md``:

* Single-pass substitution with :func:`re.sub`. The regex matches the
  placeholder grammar (``{{`` + uppercase key + ``}}``); ``re.sub``
  walks the original text left to right, so a replacement that *looks*
  like a placeholder is not re-scanned. Users can therefore provide a
  value that contains ``{{SOMETHING}}`` without accidentally
  triggering a second substitution.
* No templating engine. The scope here is "literal key replacement";
  escalating to Jinja2 would violate Article III of the constitution
  without a concrete need.
"""
from __future__ import annotations

import re
from typing import Mapping

# ``{{KEY}}`` where KEY starts with an uppercase letter and may contain
# uppercase letters, digits, and underscores. Matching the preset
# variable grammar keeps prose like ``{{foo}}`` or ``{{2FOO}}`` from
# being mistaken for a template token.
_PLACEHOLDER = re.compile(r"\{\{([A-Z][A-Z0-9_]*)\}\}")


def substitute(text: str, values: Mapping[str, str]) -> str:
    """Replace every known placeholder in ``text`` with its value.

    Unknown placeholders are left untouched. :func:`find_unresolved` can
    then report them to the caller.
    """

    def _replace(match: re.Match[str]) -> str:
        key = match.group(1)
        return values[key] if key in values else match.group(0)

    return _PLACEHOLDER.sub(_replace, text)


def find_unresolved(text: str) -> list[str]:
    """Return the sorted, de-duplicated list of placeholder keys in ``text``."""
    return sorted(set(_PLACEHOLDER.findall(text)))
