"""T020 — the framework skill validator keeps exiting zero on this repository."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_skills.py"


def test_validate_skills_exits_zero():
    result = subprocess.run(
        [sys.executable, str(VALIDATOR)], cwd=ROOT, capture_output=True, text=True
    )
    assert result.returncode == 0, (
        f"scripts/validate_skills.py failed\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    assert "OK " in result.stdout, f"expected an 'OK ' line; got:\n{result.stdout[:500]}"
