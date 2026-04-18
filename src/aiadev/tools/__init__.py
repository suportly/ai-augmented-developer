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
    *, demand: str, workspace_path: str, language: str = "en",
    slug: str | None = None, **kwargs: Any,
) -> dict[str, Any]:
    return _call(
        "specify", workspace_path,
        demand=demand, language=language, slug=slug, **kwargs,
    )


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
    result = _call(
        "clarify", workspace_path,
        spec_path=spec_path, answers=answers, **kwargs,
    )
    return result


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


def locate_latest_artifact(
    workspace_path: str,
    *,
    artifact: str = "spec.md",
) -> pathlib.Path | None:
    """Return the most recently modified ``specs/*/<artifact>`` or ``None``.

    Safety net for callers whose predicted ``target_path`` diverged from the
    slug the LLM chose when writing the file (see issue #19). Prefer pinning
    on ``target_path`` — this helper exists only as a fallback.
    """
    specs_dir = pathlib.Path(workspace_path).resolve() / "specs"
    if not specs_dir.is_dir():
        return None
    matches = sorted(
        specs_dir.glob(f"*/{artifact}"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return matches[0] if matches else None
