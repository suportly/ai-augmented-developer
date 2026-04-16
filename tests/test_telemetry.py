"""T013 — telemetry emits JSON-lines to stderr with PII allowlist."""
from __future__ import annotations

import json


class TestLogInvocation:
    ALLOWED_FIELDS = {"ts", "tool", "workspace_path", "latency_ms", "status", "error_code"}

    def test_emits_json_with_allowed_fields(self) -> None:
        from aiadev._tooling.telemetry import _last_record, log_invocation

        log_invocation(
            tool="specify",
            workspace_path="/tmp/test",
            latency_ms=42,
            status="ok",
        )
        record = json.loads(_last_record())
        assert set(record.keys()) <= self.ALLOWED_FIELDS
        assert record["tool"] == "specify"
        assert record["status"] == "ok"

    def test_demand_is_never_logged(self) -> None:
        from aiadev._tooling.telemetry import log_invocation, _last_record

        log_invocation(
            tool="specify",
            workspace_path="/tmp/test",
            latency_ms=1,
            status="ok",
            demand="secret user input",
        )
        record_str = _last_record()
        assert "secret" not in record_str
        assert "demand" not in record_str

    def test_error_code_included_on_failure(self) -> None:
        from aiadev._tooling.telemetry import log_invocation, _last_record

        log_invocation(
            tool="plan",
            workspace_path="/tmp/test",
            latency_ms=5,
            status="error",
            error_code="spec_not_found",
        )
        record = json.loads(_last_record())
        assert record["error_code"] == "spec_not_found"
