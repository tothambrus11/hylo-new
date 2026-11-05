"""Measures every corpus test and round-3 workload at several implicit-resolution depth caps.

usage: depthscan.py BINID OUT.jsonl [DEPTH ...]   (restartable: skips rows already in OUT)"""
import json, os, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
B = os.path.join(HERE, "..", "exp", "bin", sys.argv[1], "tc-bench")
OUT = sys.argv[2]
DEPTHS = [int(d) for d in sys.argv[3:]] or [10, 12, 15, 20]
T = os.path.join(REPO, "Tests", "CompilerTests")
files = sorted(os.path.join(T, d, f) for d in ("positive", "negative")
               for f in os.listdir(os.path.join(T, d)) if f.endswith(".hylo"))
R3 = os.path.join(REPO, "research", "workloads", "round3")
files += sorted(os.path.join(R3, f) for f in os.listdir(R3) if f.endswith(".hylo"))
done = set()
if os.path.exists(OUT):
    for l in open(OUT):
        r = json.loads(l); done.add((r["file"], r["depth"]))

def run(job):
    f, d = job
    env = dict(os.environ, HYLO_TC_MAXDEPTH=str(d))
    try:
        p = subprocess.run([B, "--count", f], env=env, capture_output=True, text=True, timeout=180)
        o = p.stdout + p.stderr
        t = re.search(r"type\.user\s+([\d.]+)", o)
        g = re.search(r"diagnostics: (\d+)", o)
        m = re.search(r"counters\.user:.*?summon\.matches=(\d+)", o)
        x = re.search(r"counters\.user:.*?summon\.depthExhausted=(\d+)", o)
        st = "ok" if p.returncode == 0 or t else f"rc{p.returncode}"
        return {"file": os.path.relpath(f, REPO), "depth": d, "status": st,
                "ms": float(t.group(1)) if t else None, "diags": int(g.group(1)) if g else None,
                "matches": int(m.group(1)) if m else 0, "exhausted": int(x.group(1)) if x else 0}
    except subprocess.TimeoutExpired:
        return {"file": os.path.relpath(f, REPO), "depth": d, "status": "timeout", "ms": None,
                "diags": None, "matches": None, "exhausted": None}

jobs = [(f, d) for d in DEPTHS for f in files if (os.path.relpath(f, REPO), d) not in done]
with ThreadPoolExecutor(3) as ex, open(OUT, "a") as out:
    for r in ex.map(run, jobs):
        out.write(json.dumps(r) + "\n"); out.flush()
