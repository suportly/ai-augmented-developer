"""Public Python API for invoking aiadev pipeline skills as tools."""
from __future__ import annotations

import pathlib
import time
from typing import Any

from aiadev._tooling import UnknownMarkerIdError
from aiadev._tooling.markers import enumerate_markers
from aiadev._tooling.payload import build
from aiadev._tooling.telemetry import log_invocation
from aiadev.paths import find_framework_root


def _call(
    skill: str,
    workspace_path: str,
    **kwargs: Any,
) -> dict[str, Any]:
    """Shared wrapper: resolve framework root, build payload, log telemetry."""
    root = find_framework_root()
    ws = str(pathlib.Path(workspace_path).resolve())
    start = time.monotonic()
    try:
        result = build(skill, root, workspace_path, **kwargs)
        elapsed = int((time.monotonic() - start) * 1000)
        log_invocation(tool=skill, workspace_path=ws, latency_ms=elapsed, status="ok")
        return result
    except Exception as exc:
        elapsed = int((time.monotonic() - start) * 1000)
        code = getattr(exc, "code", type(exc).__name__)
        log_invocation(
            tool=skill, workspace_path=ws, latency_ms=elapsed,
            status="error", error_code=code,
        )
        raise


def specify(
    *, demand: str, workspace_path: str, language: str = "en", **kwargs: Any
) -> dict[str, Any]:
    return _call("specify", workspace_path, demand=demand, language=language, **kwargs)


def clarify(
    *, spec_path: str, workspace_path: str,
    answers: list[dict[str, str]] | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    if answers:
        spec_text = pathlib.Path(spec_path).read_text(encoding="utf-8")
        existing = enumerate_markers(spec_text)
        existing_ids = {m["id"] for m in existing if m["id"] is not None}
        for a in answers:
            if a["id"] not in existing_ids:
                raise UnknownMarkerIdError(
                    f"Marker id {a['id']!r} not found in {spec_path}"
                )
    return _call("clarify", workspace_path, spec_path=spec_path, **kwargs)


def plan(
    *, spec_path: str, workspace_path: str, **kwargs: Any
) -> dict[str, Any]:
    return _call("plan", workspace_path, spec_path=spec_path, **kwargs)


def tasks(
    *, plan_path: str, workspace_path: str, **kwargs: Any
) -> dict[str, Any]:
    return _call("tasks", workspace_path, plan_path=plan_path, **kwargs)


def implement(*, workspace_path: str, **kwargs: Any) -> dict[str, Any]:
    return _call("implement", workspace_path, **kwargs)


def analyze(*, workspace_path: str, **kwargs: Any) -> dict[str, Any]:
    return _call("analyze", workspace_path, **kwargs)


def checklist(*, workspace_path: str, **kwargs: Any) -> dict[str, Any]:
    return _call("checklist", workspace_path, **kwargs)


def constitution(*, workspace_path: str, **kwargs: Any) -> dict[str, Any]:
    return _call("constitution", workspace_path, **kwargs)
