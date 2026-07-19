"""A fake knowledge-graph provider conforming to the spec-0017 contract.

Article V requires that tests exercise a *fake provider*, not a mocked
vendor SDK. This fixture returns deterministic, canned responses for the
three contract queries (impact / drift / provenance) so the `analyze`
integration and the contract itself can be tested without graphify (or any
network) present.

Each returned fact carries an aiadev-canonical ``confidence`` label
(explicit / inferred / ambiguous), mirroring the mapping documented in
``rules/graph-facts.md``.
"""
from __future__ import annotations

from typing import Any


def impact(paths: list[str]) -> dict[str, Any]:
    """Which subsystems the given changed paths touch (blast-radius)."""
    return {
        "subsystems": [
            {
                "name": "cli",
                "edges": [
                    {
                        "symbol": f"{path}:main",
                        "subsystem": "cli",
                        "confidence": "explicit",
                        "provider_label": "EXTRACTED",
                    }
                    for path in paths
                ],
            }
        ]
    }


def drift(tasks: list[str], diff_paths: list[str]) -> dict[str, Any]:
    """Facts for the 'task without code' and 'code without task' gaps.

    - ``missing``: symbols a done task claimed but the diff lacks.
    - ``extra``: changed files no task requested.
    """
    return {
        "missing": [
            {
                "symbol": "src/aiadev/pending.py:do_work",
                "subsystem": "core",
                "confidence": "explicit",
                "provider_label": "EXTRACTED",
            }
        ],
        "extra": [
            {
                "symbol": f"{path}:unknown",
                "subsystem": "core",
                "confidence": "inferred",
                "provider_label": "INFERRED",
            }
            for path in diff_paths
        ],
    }


def provenance(symbol: str) -> dict[str, Any]:
    """The confidence and provider-native label behind a single fact."""
    return {
        "symbol": symbol,
        "subsystem": "cli",
        "confidence": "explicit",
        "provider_label": "EXTRACTED",
    }
