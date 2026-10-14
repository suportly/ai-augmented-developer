#!/usr/bin/env python3
"""Real behavioural verification of one run (no mocks): pytest + CLI + artifacts."""
import json, re, subprocess, sys
from pathlib import Path
run = Path(sys.argv[1]); proj = run / "proj"
env = {"PATH": "/opt/homebrew/bin:/usr/bin:/bin:/usr/local/bin", "PYTHONPATH": str(proj / "src"), "HOME": str(Path.home())}
def sh(*a, **k):
    return subprocess.run(a, cwd=proj, env=env, capture_output=True, text=True, **k)
out = {}
t = sh("python3", "-m", "pytest", "-q", "-p", "no:cacheprovider")
out["pytest_rc"] = t.returncode
out["pytest_tail"] = (t.stdout.strip().splitlines() or [""])[-1]
g = sh("python3", "-m", "hello_cli.cli", "greet", "World")
out["greet_ok"] = g.returncode == 0 and g.stdout.strip() == "Hello, World!"
s = sh("python3", "-m", "hello_cli.cli", "greet", "World", "--shout")
out["shout_ok"] = s.returncode == 0 and s.stdout.strip() == "HELLO, WORLD!"
n = sh("python3", "-m", "hello_cli.cli", "greet")
out["usage_ok"] = n.returncode == 2 and "Usage" in (n.stderr + n.stdout)
readme = (proj / "README.md").read_text()
out["readme_mentions_greet"] = "greet" in readme
specs = sorted((proj / "specs").glob("*/")) if (proj / "specs").exists() else []
out["spec_dirs"] = [p.name for p in specs]
if specs:
    d = specs[0]
    out["has_spec_plan_tasks"] = all((d / f).exists() for f in ("spec.md", "plan.md", "tasks.md"))
    tasks = (d / "tasks.md").read_text() if (d / "tasks.md").exists() else ""
    st = re.findall(r"\*\*Status:\*\*\s*(\w+)", tasks)
    out["tasks_total"] = len(st); out["tasks_done"] = st.count("done")
    spec = (d / "spec.md").read_text() if (d / "spec.md").exists() else ""
    out["open_markers"] = spec.count("[NEEDS CLARIFICATION")
rv = proj / ".aiadev" / "review.yaml"
out["review_yaml"] = rv.read_text().strip().replace("\n", " | ") if rv.exists() else None
out["branch_clean"] = sh("git", "status", "--short").stdout.strip() == ""
(run / "verify.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))
print(json.dumps(out, ensure_ascii=False))
