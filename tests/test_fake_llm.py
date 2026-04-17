"""T026 — fake LLM produces structurally-valid artifacts from ToolPayload."""
from __future__ import annotations

import pathlib


def test_fake_creates_file_at_target_path(
    framework_root: pathlib.Path, tmp_path: pathlib.Path
) -> None:
    from aiadev.tools import specify
    from tests._fakes.llm import execute_payload

    payload = specify(demand="test feature", workspace_path=str(tmp_path))
    target = execute_payload(payload)
    assert target.exists()
    assert target == pathlib.Path(payload["target_path"])


def test_fake_fills_template_placeholders(
    framework_root: pathlib.Path, tmp_path: pathlib.Path
) -> None:
    from aiadev.tools import specify
    from tests._fakes.llm import execute_payload

    payload = specify(demand="test feature", workspace_path=str(tmp_path))
    execute_payload(payload)
    content = pathlib.Path(payload["target_path"]).read_text()
    assert "{{FEATURE_NAME}}" not in content
    assert "{{BRANCH}}" not in content
    assert "{{DATE}}" not in content
