"""T019 — aiadev sync discovers rules and skills; every artifact path resolves."""

from pathlib import Path

from aiadev.framework_artifacts import iter_framework_artifacts

ROOT = Path(__file__).resolve().parents[1]


def test_discovered_artifact_paths_resolve():
    artifacts = list(iter_framework_artifacts(ROOT))
    for role, name, path in artifacts:
        assert path.exists(), f"{role} '{name}' resolves to missing path {path}"
