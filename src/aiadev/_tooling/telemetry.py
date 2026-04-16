"""JSON-lines telemetry emitted to stderr (MCP convention)."""
from __future__ import annotations

import json
import logging
import sys
import time
from typing import Any

_ALLOWED = frozenset({"ts", "tool", "workspace_path", "latency_ms", "status", "error_code"})

_logger = logging.getLogger("aiadev.telemetry")
if not _logger.handlers:
    _handler = logging.StreamHandler(sys.stderr)
    _handler.setFormatter(logging.Formatter("%(message)s"))
    _logger.addHandler(_handler)
    _logger.setLevel(logging.INFO)

_last: str = ""


def log_invocation(**kwargs: Any) -> None:
    """Emit one JSON-line with only the allowed fields. Extra kwargs are silently dropped."""
    global _last
    record: dict[str, Any] = {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    for key in _ALLOWED:
        if key != "ts" and key in kwargs:
            record[key] = kwargs[key]
    line = json.dumps(record, ensure_ascii=False)
    _last = line
    _logger.info(line)


def _last_record() -> str:
    """Return the last logged JSON line (for testing only)."""
    return _last
