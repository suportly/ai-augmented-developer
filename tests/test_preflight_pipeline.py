"""End-to-end pre-flight pipeline tests.

Spec: ``specs/0010-pipeline-preflight-checks/spec.md`` Success criterion #5
("deleting any prior-stage artifact causes the immediately following
pipeline skill to fail with the actionable message").
"""
from __future__ import annotations

import pathlib
import shutil
import time

import pytest
from click.testing import CliRunner

REFERENCE_FIXTURE = (
    pathlib.Path(__file__).resolve().parent / "fixtures" / "preflight" / "reference"
)


def _build_repo(tmp_path: pathlib.Path) -> tuple[pathlib.Path, pathlib.Path]:
    """Lay out tmp/specs/<slug>/ from the reference fixture and return paths."""
    repo = tmp_path / "repo"
    repo.mkdir()
    feature_slug = "0001-reference"
    feature_dir = repo / "specs" / feature_slug
    shutil.copytree(REFERENCE_FIXTURE, feature_dir)
    review = repo / ".aiadev" / "review.yaml"
    review.parent.mkdir(parents=True, exist_ok=True)
    review.write_text(
        "status: approved\ntimestamp: 2026-04-21T00:00:00Z\n",
        encoding="utf-8",
    )
    return repo, feature_dir


def _run_cli(args: list[str], cwd: pathlib.Path):
    from aiadev.cli import main

    runner = CliRunner()
    return runner.invoke(main, args, catch_exceptions=False)


# -- T023: Success criterion #5, Story 1 scenario 1 --------------------------


def test_deleting_tasks_md_causes_implement_preflight_failure(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, feature_dir = _build_repo(tmp_path)
    (feature_dir / "tasks.md").unlink()

    monkeypatch.chdir(repo)
    monkeypatch.setattr(
        "aiadev.preflight._git_current_branch", lambda: "feature/reference"
    )

    result = _run_cli(
        ["preflight", "implement", "--feature", feature_dir.name],
        cwd=repo,
    )

    assert result.exit_code != 0
    assert "pre-flight: tasks.md missing — run /aia:tasks first" in result.output


# -- T024: Success criterion #5 (parametrised) ------------------------------


@pytest.mark.parametrize(
    ("skill", "deleted", "needle"),
    [
        ("plan", "spec.md", "spec.md missing"),
        ("tasks", "spec.md", "spec.md missing"),
        ("tasks", "plan.md", "plan.md missing"),
        ("implement", "spec.md", "spec.md missing"),
        ("implement", "plan.md", "plan.md missing"),
        ("implement", "tasks.md", "tasks.md missing"),
        ("analyze", "tasks.md", "tasks.md missing"),
        ("finishing-a-branch", ".aiadev/review.yaml", "review approval missing"),
    ],
)
def test_deleting_each_prior_artifact_fails_the_next_skill(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    skill: str,
    deleted: str,
    needle: str,
) -> None:
    repo, feature_dir = _build_repo(tmp_path)
    monkeypatch.chdir(repo)
    monkeypatch.setattr(
        "aiadev.preflight._git_current_branch", lambda: "feature/reference"
    )

    target = repo / deleted if deleted.startswith(".aiadev") else feature_dir / deleted
    if target.exists():
        target.unlink()

    result = _run_cli(
        ["preflight", skill, "--feature", feature_dir.name],
        cwd=repo,
    )

    assert result.exit_code != 0, f"{skill}/{deleted}: expected failure, got 0"
    assert needle in result.output, (
        f"{skill}/{deleted}: expected {needle!r} in {result.output!r}"
    )


# -- T025: Success criterion #3 ----------------------------------------------


def test_reference_dir_completes_under_500ms(tmp_path: pathlib.Path) -> None:
    from aiadev.preflight import check

    repo, feature_dir = _build_repo(tmp_path)

    start = time.perf_counter()
    check(
        "analyze",
        feature_dir,
        env={},
        current_branch=lambda: "feature/reference",
        repo_root=repo,
    )
    elapsed = time.perf_counter() - start

    assert elapsed < 0.5, f"pre-flight took {elapsed:.3f}s — exceeds 500ms budget"


# -- T026: Story 1 scenario 4 (positive) -------------------------------------


def test_review_yaml_approved_lets_finishing_branch_pass(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, feature_dir = _build_repo(tmp_path)
    monkeypatch.chdir(repo)
    monkeypatch.setattr(
        "aiadev.preflight._git_current_branch", lambda: "feature/reference"
    )

    result = _run_cli(
        ["preflight", "finishing-a-branch", "--feature", feature_dir.name],
        cwd=repo,
    )

    assert result.exit_code == 0, result.output
    assert result.output == ""


# -- T024 (spec 0030): --format json with feature context ---------------------


def _run_json(args: list[str]):
    import inspect

    from aiadev.cli import main

    kwargs = {}
    if "mix_stderr" in inspect.signature(CliRunner.__init__).parameters:
        kwargs["mix_stderr"] = False
    return CliRunner(**kwargs).invoke(main, args, catch_exceptions=False)


def _json_env(tmp_path, monkeypatch):
    repo, feature_dir = _build_repo(tmp_path)
    monkeypatch.chdir(repo)
    monkeypatch.setattr(
        "aiadev.preflight._git_current_branch", lambda: "feature/reference"
    )
    return repo, feature_dir


def test_json_format_happy_path_payload(tmp_path, monkeypatch) -> None:
    import json

    repo, feature_dir = _json_env(tmp_path, monkeypatch)
    (repo / "templates").mkdir()
    (repo / "templates" / "tasks-template.md").write_text("t", encoding="utf-8")
    cl = feature_dir / "checklists"
    cl.mkdir()
    (cl / "security.md").write_text("x", encoding="utf-8")

    result = _run_json(
        ["preflight", "tasks", "--feature", feature_dir.name, "--format", "json"]
    )

    assert result.exit_code == 0
    assert result.stderr == ""
    payload = json.loads(result.stdout)  # stdout is ONLY the JSON object
    assert payload["skill"] == "tasks"
    assert payload["feature"] == "0001-reference"
    assert payload["feature_dir"] == "specs/0001-reference"
    assert payload["ok"] is True
    assert payload["issues"] == []
    assert payload["docs"] == {
        "spec": "specs/0001-reference/spec.md",
        "plan": "specs/0001-reference/plan.md",
        "tasks": "specs/0001-reference/tasks.md",
        "checklists": ["specs/0001-reference/checklists/security.md"],
    }
    assert payload["template"] == "templates/tasks-template.md"


def test_json_format_failure_goes_to_stdout_with_exit_1(tmp_path, monkeypatch) -> None:
    import json

    _, feature_dir = _json_env(tmp_path, monkeypatch)
    (feature_dir / "tasks.md").unlink()

    result = _run_json(
        ["preflight", "implement", "--feature", feature_dir.name, "--format", "json"]
    )

    assert result.exit_code == 1
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert payload["docs"]["tasks"] is None
    assert payload["docs"]["checklists"] == []
    assert payload["template"] is None
    assert {
        "message": "pre-flight: tasks.md missing — run /aia:tasks first",
        "would_abort": True,
    } in payload["issues"]


def test_json_format_warn_mode_is_ok_true(tmp_path, monkeypatch) -> None:
    import json

    _, feature_dir = _json_env(tmp_path, monkeypatch)
    (feature_dir / "tasks.md").unlink()
    monkeypatch.setenv("AIADEV_PREFLIGHT", "warn")

    result = _run_json(
        ["preflight", "implement", "--feature", feature_dir.name, "--format", "json"]
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is True  # ok == no issue would abort
    assert payload["issues"] and payload["issues"][0]["would_abort"] is False


def test_json_format_valid_when_feature_dir_missing(tmp_path, monkeypatch) -> None:
    import json

    repo, _ = _json_env(tmp_path, monkeypatch)

    result = _run_json(
        ["preflight", "plan", "--feature", "9999-nope", "--format", "json"]
    )

    assert result.exit_code == 1
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert payload["docs"] == {
        "spec": None, "plan": None, "tasks": None, "checklists": []
    }
    assert payload["ok"] is False


def test_json_format_task_context_keeps_stdout_pure(tmp_path, monkeypatch) -> None:
    import json

    _, feature_dir = _json_env(tmp_path, monkeypatch)

    result = _run_json(
        [
            "preflight", "implement", "--feature", feature_dir.name,
            "--task-context", "--format", "json",
        ]
    )

    assert result.stderr == ""
    payload = json.loads(result.stdout)  # no task-context banner line
    assert payload["skill"] == "implement"


def test_json_format_all_returns_list_per_feature(tmp_path, monkeypatch) -> None:
    import json

    repo, feature_dir = _json_env(tmp_path, monkeypatch)
    other = repo / "specs" / "0002-other"
    other.mkdir()

    result = _run_json(["preflight", "--all", "--format", "json"])

    payload = json.loads(result.stdout)
    assert result.stderr == ""
    assert isinstance(payload, list)
    assert [p["feature"] for p in payload] == [feature_dir.name, "0002-other"]


def test_json_format_all_without_specs_dir_is_empty_list(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    result = _run_json(["preflight", "--all", "--format", "json"])

    assert result.exit_code == 0
    assert result.stderr == ""
    assert result.stdout.strip() == "[]"


# -- T025: test_command no payload (D3) ---------------------------------------


def _payload_for(tmp_path, monkeypatch, files: dict[str, str]) -> dict:
    import json

    repo, feature_dir = _json_env(tmp_path, monkeypatch)
    for name, body in files.items():
        (repo / name).write_text(body, encoding="utf-8")
    result = _run_json(
        ["preflight", "tasks", "--feature", feature_dir.name, "--format", "json"]
    )
    return json.loads(result.stdout)


def test_test_command_from_node_test_script(tmp_path, monkeypatch) -> None:
    payload = _payload_for(
        tmp_path,
        monkeypatch,
        {"package.json": '{"scripts": {"test": "vitest run", "build": "tsc"}}'},
    )
    assert payload["test_command"] == "npm run test"


def test_test_command_null_without_detectable_command(tmp_path, monkeypatch) -> None:
    payload = _payload_for(tmp_path, monkeypatch, {})
    assert "test_command" in payload and payload["test_command"] is None
    # pure Python (pyproject only): no test command is detected today
    (tmp_path / "py").mkdir()
    payload = _payload_for(
        tmp_path / "py", monkeypatch, {"pyproject.toml": "[project]\nname='x'\n"}
    )
    assert payload["test_command"] is None


def test_test_command_never_raises_on_detection_failure(
    tmp_path, monkeypatch
) -> None:
    def boom(_root):
        raise OSError("manifest unreadable")

    monkeypatch.setattr("aiadev.project_introspect.introspect", boom)
    payload = _payload_for(
        tmp_path, monkeypatch, {"package.json": '{"scripts": {"test": "x"}}'}
    )
    assert payload["test_command"] is None
