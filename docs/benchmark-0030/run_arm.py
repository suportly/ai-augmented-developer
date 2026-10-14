#!/usr/bin/env python3
"""Run one arm of one pair: fresh project, real `claude -p`, collect evidence."""
import json, os, subprocess, sys, time, uuid, shutil, glob
from pathlib import Path

B = Path(__file__).resolve().parent
arm, pair = sys.argv[1], sys.argv[2]
run = B / "runs" / f"par-{pair}-{arm}"
proj = run / "proj"
run.mkdir(parents=True, exist_ok=True)
subprocess.run([str(B / "mkproj.sh"), arm, str(proj)], check=True)
sid = str(uuid.uuid4())
env = dict(os.environ)
env["PATH"] = f"{B}/bin-{arm}:{env['PATH']}"
cmd = ["claude", "-p", (B / os.environ.get("BENCH_PROMPT", "prompt.txt")).read_text(), "--model", "sonnet",
       "--setting-sources", "project,local", "--strict-mcp-config",
       "--permission-mode", "acceptEdits", "--allowedTools", "Bash",
       "--disallowedTools", "WebFetch", "WebSearch",
       "--max-budget-usd", "8", "--session-id", sid, "--output-format", "json"]
t0 = time.time()
try:
    p = subprocess.run(cmd, cwd=proj, env=env, capture_output=True, text=True, timeout=3600)
    rc, out, err = p.returncode, p.stdout, p.stderr
except subprocess.TimeoutExpired as e:
    rc, out, err = -9, (e.stdout or b"").decode() if isinstance(e.stdout, bytes) else (e.stdout or ""), "TIMEOUT"
dur = time.time() - t0
(run / "result.json").write_text(out)
(run / "stderr.txt").write_text(err or "")
meta = {"arm": arm, "pair": int(pair), "session_id": sid, "rc": rc, "seconds": round(dur, 1)}
try:
    r = json.loads(out)
    meta.update({k: r.get(k) for k in ("total_cost_usd", "num_turns", "is_error", "subtype", "terminal_reason", "stop_reason")})
    meta["subagent_stats"] = r.get("subagent_stats")
except Exception as exc:  # noqa
    meta["parse_error"] = repr(exc)
logs = glob.glob(str(proj / "specs" / "*" / ".review-log.jsonl"))
if logs:
    shutil.copy(logs[0], run / "review-log.jsonl")
meta["review_log"] = bool(logs)
transcripts = glob.glob(os.path.expanduser(f"~/.claude/projects/*/{sid}.jsonl"))
meta["transcript"] = transcripts[0] if transcripts else None
git = lambda *a: subprocess.run(["git", *a], cwd=proj, capture_output=True, text=True).stdout.strip()
meta["commits"] = git("log", "--oneline", "main..HEAD").splitlines() if git("rev-parse", "--verify", "main") else []
meta["branch"] = git("rev-parse", "--abbrev-ref", "HEAD")
meta["status_dirty"] = bool(git("status", "--short"))
(run / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False))
print(json.dumps(meta, ensure_ascii=False))
