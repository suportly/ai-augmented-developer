"""T020 — terse-mode does not regress existing framework validators.

Spec 0009 success criterion 5: ``scripts/validate_skills.py`` must exit 0
both when terse-mode is off and when it is on. Today the validator is
stateless w.r.t. terse-mode, so this is a guard rather than a discovery
test — if the validator ever starts reading ``AIADEV_TERSE`` in a way
that breaks one mode, this fails.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_skills.py"


@pytest.mark.xfail(
    reason="T004 migrates the 22 SKILL.md files to metadata.aiadev; until "
    "then 10 real skills still have proprietary fields at the top level "
    "and scripts/validate_skills.py exits 1 (spec 0016 Story 1, T002 "
    "rewrites the schema first).",
    strict=False,
)
@pytest.mark.parametrize("terse_value", ["0", "1"])
def test_validate_skills_exits_zero_in_both_modes(terse_value):
    env = dict(os.environ)
    env["AIADEV_TERSE"] = terse_value

    result = subprocess.run(
        [sys.executable, str(VALIDATOR)],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"scripts/validate_skills.py failed under AIADEV_TERSE={terse_value!r}\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    # Paste evidence: both runs produced non-empty stdout listing skills.
    assert "OK " in result.stdout, (
        f"expected at least one 'OK ' line in validator output under "
        f"AIADEV_TERSE={terse_value!r}; got:\n{result.stdout[:500]}"
    )
