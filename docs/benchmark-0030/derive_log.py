#!/usr/bin/env python3
"""Derive a review-log from the real subagent transcripts of one run."""
import glob, json, os, re, sys
run = sys.argv[1]
meta = json.load(open(f"{run}/meta.json"))
sid = meta["session_id"]
base = os.path.dirname(meta["transcript"])
rows = []
for mp in sorted(glob.glob(f"{base}/{sid}/subagents/**/agent-*.meta.json", recursive=True)):
    m = json.load(open(mp))
    if m.get("agentType") != "code-reviewer":
        continue
    jp = mp.replace(".meta.json", ".jsonl")
    last = ""
    ts = ""
    for line in open(jp):
        try:
            d = json.loads(line)
        except ValueError:
            continue
        msg = d.get("message") or {}
        if msg.get("role") == "assistant":
            c = msg.get("content")
            if isinstance(c, list):
                t = "".join(b.get("text", "") for b in c if b.get("type") == "text")
                if t.strip():
                    last = t
                    ts = d.get("timestamp", ts)
    head = last.strip().upper()
    if "CHANGES_REQUESTED" in head[:200] or "ISSUES_FOUND" in head[:200] or re.match(r"^\W*ISSUES", head):
        verdict = "CHANGES_REQUESTED"
    elif "APPROVED" in head[:200]:
        verdict = "APPROVED"
    else:
        verdict = "UNKNOWN"
    tid = re.search(r"\b(T\d+)\b", m.get("description", ""))
    rows.append({"timestamp": ts, "reviewer": "code-reviewer", "verdict": verdict,
                 "has_why_no_issues_block": "WHY NO ISSUES" in last.upper(),
                 "task_id": tid.group(1) if tid else "branch-review", "description": m.get("description")})
rows.sort(key=lambda r: r["timestamp"])
with open(f"{run}/derived-review-log.jsonl", "w") as f:
    for r in rows:
        f.write(json.dumps(r) + "\n")
print(run, len(rows), {v: sum(1 for r in rows if r["verdict"] == v) for v in ("APPROVED", "CHANGES_REQUESTED", "UNKNOWN")})
