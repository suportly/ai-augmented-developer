"""T011 — pre-commit config runs the pipeline-reference generator."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / ".pre-commit-config.yaml"
WORKFLOW = ROOT / ".github" / "workflows" / "pipeline-reference-drift.yml"


def test_precommit_config_exists():
    assert CONFIG.exists(), ".pre-commit-config.yaml must exist"


def test_precommit_hook_runs_generator():
    payload = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    hook_ids = {hook["id"] for repo in payload["repos"] for hook in repo.get("hooks", [])}
    assert "pipeline-reference" in hook_ids, (
        "pre-commit must carry a 'pipeline-reference' hook"
    )

    local_repo = next(r for r in payload["repos"] if r["repo"] == "local")
    hook = next(h for h in local_repo["hooks"] if h["id"] == "pipeline-reference")
    assert "generate_pipeline_reference.py" in hook["entry"], (
        "hook entry must invoke the generator script"
    )
    assert hook.get("pass_filenames") is False, (
        "hook must not receive filenames (generator takes --output only)"
    )


def test_drift_workflow_exists_and_fails_on_diff():
    assert WORKFLOW.exists(), "CI drift workflow must be committed"
    body = WORKFLOW.read_text(encoding="utf-8")
    assert "generate_pipeline_reference.py" in body
    assert "git diff --exit-code" in body, (
        "workflow must fail when the generator produces a non-empty diff"
    )
