"""Runs every review program under baseline / FIX / FULL; writes regress-final.jsonl (restartable).

usage: regress.py BINID [jobs]"""
import json, os, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__))
FIX = "occurs,fixsubst,eqsolve,extorder,arrowenv,eqmgu,givencheck,budget"
FULL = FIX + ",symindex,coesrc,traitindex,memberskip,unify,index,absmodel,absquotient,typevec,reifymemo"
CONFIGS = {"base": "", "FIX": FIX, "FULL": FULL}
binid = sys.argv[1]; jobs = int(sys.argv[2]) if len(sys.argv) > 2 else 3
B = os.path.join(HERE, "..", "..", "exp", "bin", binid, "tc-bench")
out = os.path.join(HERE, "regress-final.jsonl")
files = sorted(os.path.relpath(os.path.join(d, f), HERE) for r in ("review", "review2")
               for d, _, fs in os.walk(os.path.join(HERE, r)) if "recheck" not in d
               for f in fs if f.endswith(".hylo"))
done = set()
if os.path.exists(out):
    done = {(r["file"], r["config"]) for r in map(json.loads, open(out))}
todo = [(f, c) for f in files for c in CONFIGS if (f, c) not in done]
def one(fc):
    f, c = fc
    env = dict(os.environ, HYLO_TC_EXPERIMENTS=CONFIGS[c])
    try:
        p = subprocess.run([B, os.path.join(HERE, f)], env=env, capture_output=True, text=True, timeout=30)
        m = re.search(r"diagnostics: (\d+)", p.stdout); d = int(m.group(1)) if m else None
        m = re.search(r"type\.user\s+([\d.]+)", p.stdout); ms = float(m.group(1)) if m else None
        errs = [l.strip().split("error: ", 1)[1] for l in p.stdout.splitlines() if "error: " in l][:3]
        return {"file": f, "config": c, "rc": p.returncode, "d": d, "ms": ms, "errors": errs}
    except subprocess.TimeoutExpired:
        return {"file": f, "config": c, "rc": "timeout", "d": None, "ms": None, "errors": []}
with open(out, "a") as o, ThreadPoolExecutor(jobs) as ex:
    for r in ex.map(one, todo):
        o.write(json.dumps(r) + "\n"); o.flush()
