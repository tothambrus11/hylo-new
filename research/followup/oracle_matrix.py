"""Output equivalence of every technique alone and of every leave-one-out configuration.

usage: oracle_matrix.py BINID OUT.jsonl [jobs]
For each corpus file and each configuration, compares the typing dump (types, bindings, witness
tables, diagnostics, and elaborated witnesses with equality proofs erased) with the baseline's.
Restartable. A technique can be adopted independently only if it is identical alone."""
import json, os, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor
RES = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RES, "exp"))
import tcx
FIX = ["occurs", "fixsubst", "eqsolve", "extorder", "arrowenv", "eqmgu", "givencheck", "budget"]
PERF = ["symindex", "coesrc", "traitindex", "memberskip", "unify", "index", "absmodel", "absquotient", "typevec", "reifymemo"]
FULL = FIX + PERF
CONFIGS = {"+" + f: [f] for f in FULL} | {"-" + f: [x for x in FULL if x != f] for f in FULL}
CONFIGS["MIN5"] = ["index", "memberskip", "typevec", "symindex", "traitindex"]
CONFIGS["FULL"] = FULL
B = os.path.join(RES, "exp", "bin", sys.argv[1], "tc-bench")

def dump(path, flags):
    with tempfile.NamedTemporaryFile(suffix=".dump", delete=False) as f: out = f.name
    try:
        p = subprocess.run([B, "--dump", out, path], env=dict(os.environ, HYLO_TC_EXPERIMENTS=",".join(flags)),
                           capture_output=True, text=True, timeout=300)
        if p.returncode != 0: return None
        return {l for l in tcx.NORMALIZE.sub("(erased: _)", open(out).read()).split("\n") if " syn.raw " not in l}
    except subprocess.TimeoutExpired:
        return None
    finally:
        if os.path.exists(out): os.unlink(out)

def one(path):
    rel = os.path.relpath(path, RES)
    if rel in done: return None
    base = dump(path, [])
    r = {"file": rel, "base": base is not None, "diff": {}}
    if base is None: return r
    for name, flags in CONFIGS.items():
        d = dump(path, flags)
        if d is None: r["diff"][name] = "crash"
        elif d != base: r["diff"][name] = sorted(d ^ base)[:4]
    return r

out = sys.argv[2]; jobs = int(sys.argv[3]) if len(sys.argv) > 3 else 1
done = set()
if os.path.exists(out): done = {json.loads(l)["file"] for l in open(out)}
with open(out, "a") as o, ThreadPoolExecutor(jobs) as ex:
    for r in ex.map(one, tcx.corpus("all")):
        if r: o.write(json.dumps(r) + "\n"); o.flush()
