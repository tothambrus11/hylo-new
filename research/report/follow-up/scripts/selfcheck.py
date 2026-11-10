"""Runs the type checker in self-checking mode over the corpus and the test programs.

usage: selfcheck.py BINID OUT.jsonl [jobs]
In this mode every pruning decision is verified by doing the work it avoided: a goal refuted by
the abstract model or by the equality procedure is searched for anyway, a candidate skipped by
the index is matched anyway, and so on. A violation is a pruning decision that was wrong."""
import json, os, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
RES = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RES, "exp"))
import tcx
FULL = ("occurs,fixsubst,eqsolve,extorder,arrowenv,eqmgu,givencheck,budget,symindex,coesrc,traitindex,"
        "memberskip,unify,index,absmodel,absquotient,typevec,reifymemo,selfcheck")
B = os.path.join(RES, "exp", "bin", sys.argv[1], "tc-bench")
out = sys.argv[2]; jobs = int(sys.argv[3]) if len(sys.argv) > 3 else 2
files = list(tcx.corpus("all")) + sorted(
    os.path.join(d, f) for d, _, fs in os.walk(os.path.join(RES, "report", "test-programs")) for f in fs if f.endswith(".hylo"))
done = set()
if os.path.exists(out): done = {json.loads(l)["file"] for l in open(out)}
def one(f):
    rel = os.path.relpath(f, RES)
    if rel in done: return None
    try:
        p = subprocess.run([B, "--count", f], env=dict(os.environ, HYLO_TC_EXPERIMENTS=FULL),
                           capture_output=True, text=True, timeout=300)
        m = re.search(r"counters.user:\s*(.*)", p.stdout)
        c = {k: int(v) for k, v in re.findall(r'"?([\w.]+)"?[=:]\s*(\d+)', m.group(1))} if m else {}
        v = sorted(set(re.findall(r"\[selfcheck\] VIOLATION: (.*)", p.stdout)))
        return {"file": rel, "rc": p.returncode, "violations": v,
                "selfcheck": {k: n for k, n in c.items() if k.startswith("selfcheck")}}
    except subprocess.TimeoutExpired:
        return {"file": rel, "rc": "timeout", "violations": [], "selfcheck": {}}
with open(out, "a") as o, ThreadPoolExecutor(jobs) as ex:
    for r in ex.map(one, files):
        if r: o.write(json.dumps(r) + "\n"); o.flush()
