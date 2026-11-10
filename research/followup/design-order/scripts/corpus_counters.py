#!/usr/bin/env python3
"""Records the work counters of the type checker (FULL configuration) for every program of the
compiler's test suite, one process at a time.

usage: corpus_counters.py OUT.jsonl
Restartable. Each line has the file, the verdict, and the counters of the user module and of the
standard library as dictionaries.
"""
import glob, json, os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import orders

def counters(line):
    return {k: int(v) for k, v in (x.split("=") for x in line.split())}

out = sys.argv[1]
done = {json.loads(l)["file"] for l in open(out)} if os.path.exists(out) else set()
files = sorted(glob.glob("/home/user/hylo-new/Tests/CompilerTests/*/*.hylo"))
with open(out, "a") as o:
    for f in files:
        if f in done: continue
        try:
            p = subprocess.run([orders.B, "--count", f], env=dict(os.environ, HYLO_TC_EXPERIMENTS=orders.CONFIGS["FULL"]),
                               capture_output=True, text=True, timeout=60)
        except subprocess.TimeoutExpired:
            o.write(json.dumps({"file": f, "verdict": "timeout"}) + "\n"); o.flush(); continue
        u = re.search(r"counters.user:(.*)", p.stdout); s = re.search(r"counters.stdlib:(.*)", p.stdout)
        m = re.search(r"diagnostics: (\d+)", p.stdout)
        o.write(json.dumps({"file": f, "exit": p.returncode,
                            "verdict": "accept" if m and m.group(1) == "0" else "reject",
                            "user": counters(u.group(1)) if u else {}, "stdlib": counters(s.group(1)) if s else {}}) + "\n")
        o.flush()
