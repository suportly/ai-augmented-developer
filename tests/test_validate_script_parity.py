"""T006 — scripts/validate_skills.py mirrors aiadev.validate's dual validation.

Spec 0016, Story 1, sc3: ``python3 scripts/validate_skills.py`` (the
zero-install fallback) must reproduce ``aiadev validate``'s verdict on the
same inputs — a conformant SKILL.md passes, a pre-0016 old-format SKILL.md
(proprietary field at top level) fails with the same didactic message
naming the field and ``metadata.aiadev.<field>``.

The script is invoked via subprocess (mirrors the pattern in
tests/test_existing_validators_regress.py) so this test exercises the real
CLI entry point, not just importable internals — and stays honest that the
script does not import the ``aiadev`` package.
"""
from __future__ import annotations

import pathlib
import subprocess
import sys

from aiadev.validate import validate_paths

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_skills.py"

CONFORMANT_SKILL = (
    "---\n"
    "name: conformant-skill\n"
    "description: A minimal skill conformant with both schemas.\n"
    "metadata:\n"
    "  aiadev:\n"
    "    version: 0.1.0\n"
    "---\n\n"
    "# Conformant Skill\n"
)

OLD_FORMAT_SKILL = (
    "---\n"
    "name: old-format-skill\n"
    "description: A skill still using the old top-level pipeline fields.\n"
    "requires:\n"
    "  - some-other-skill\n"
    "---\n\n"
    "# Old Format Skill\n"
)


def _write_skill(root: pathlib.Path, name: str, body: str) -> pathlib.Path:
    skill_dir = root / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_path = skill_dir / "SKILL.md"
    skill_path.write_text(body, encoding="utf-8")
    return skill_path


def _run_script(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )


def test_conformant_skill_exits_zero(tmp_path: pathlib.Path) -> None:
    skill_path = _write_skill(tmp_path, "conformant-skill", CONFORMANT_SKILL)
    result = _run_script(str(skill_path))
    assert result.returncode == 0, (
        f"expected exit 0 for a conformant skill\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )


def test_old_format_skill_exits_one_with_didactic_message(tmp_path: pathlib.Path) -> None:
    skill_path = _write_skill(tmp_path, "old-format-skill", OLD_FORMAT_SKILL)
    result = _run_script(str(skill_path))
    assert result.returncode == 1, (
        f"expected exit 1 for a pre-0016 old-format skill\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    combined = result.stdout + result.stderr
    assert "requires" in combined, combined
    assert "metadata.aiadev.requires" in combined, combined


def test_parity_with_aiadev_validate_on_same_fixtures(tmp_path: pathlib.Path) -> None:
    """The script's verdict (exit code) must match aiadev.validate.validate_paths
    for the same inputs, for both a conformant and an old-format skill."""
    conformant_path = _write_skill(tmp_path, "conformant-skill", CONFORMANT_SKILL)
    old_format_path = _write_skill(tmp_path, "old-format-skill", OLD_FORMAT_SKILL)

    for skill_path in (conformant_path, old_format_path):
        script_result = _run_script(str(skill_path))
        script_ok = script_result.returncode == 0

        report = validate_paths([skill_path], root=ROOT)
        assert script_ok == report.ok, (
            f"parity mismatch for {skill_path}: "
            f"script exit={script_result.returncode} (ok={script_ok}) "
            f"vs aiadev.validate ok={report.ok}\n"
            f"script stdout:\n{script_result.stdout}\nstderr:\n{script_result.stderr}"
        )


def test_real_repo_tree_passes_with_no_args() -> None:
    """Sanity: the whole repo (post T004 migration) still passes the
    zero-install fallback under the new dual-schema validation."""
    result = _run_script()
    assert result.returncode == 0, (
        f"scripts/validate_skills.py failed against the real repo tree\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    assert "OK " in result.stdout, (
        f"expected at least one 'OK ' line; got:\n{result.stdout[:500]}"
    )
