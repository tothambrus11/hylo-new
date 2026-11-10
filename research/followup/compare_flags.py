"""Compares two configurations program by program (verdict and error messages), with the second
one also run in self-checking mode.

usage: compare_flags.py BINID OUT.jsonl EXTRA_FLAGS DIR_OR_CORPUS... [--jobs N]
The reference is FULL; the candidate is FULL + EXTRA_FLAGS. "corpus" stands for the compiler
tests and workloads."""
import json, os, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
RES = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RES, "exp")); import tcx
FULL = ("occurs,fixsubst,eqsolve,extorder,arrowenv,eqmgu,givencheck,budget,symindex,coesrc,traitindex,"
        "memberskip,unify,index,absmodel,absquotient,typevec,reifymemo")
args = sys.argv[1:]; jobs = 2
if "--jobs" in args: i = args.index("--jobs"); jobs = int(args[i + 1]); del args[i:i + 2]
B = os.path.join(RES, "exp", "bin", args[0], "tc-bench"); out, extra, where = args[1], args[2], args[3:]
files = []
for w in where:
    if w == "corpus": files += list(tcx.corpus("all"))
    else: files += sorted(os.path.join(d, f) for d, _, fs in os.walk(w) for f in fs if f.endswith(".hylo"))
def run(f, flags):
    try:
        p = subprocess.run([B, "--count", f], env=dict(os.environ, HYLO_TC_EXPERIMENTS=flags), capture_output=True, text=True, timeout=300)
        m = re.search(r"diagnostics: (\d+)", p.stdout)
        errs = sorted(re.sub(r"^.*?: error: ", "", l.strip()) for l in p.stdout.splitlines() if ": error: " in l)
        return {"rc": p.returncode, "d": int(m.group(1)) if m else None, "errors": errs,
                "violations": sorted(set(re.findall(r"\[selfcheck\] VIOLATION: (.*)", p.stdout)))}
    except subprocess.TimeoutExpired:
        return {"rc": "timeout", "d": None, "errors": [], "violations": []}
done = set()
if os.path.exists(out): done = {json.loads(l)["file"] for l in open(out)}
def one(f):
    rel = os.path.relpath(f, RES)
    if rel in done: return None
    a, b, c = run(f, FULL), run(f, FULL + "," + extra), run(f, FULL + "," + extra + ",selfcheck")
    return {"file": rel, "ref": a, "new": b, "violations": c["violations"], "selfcheck_rc": c["rc"]}
with open(out, "a") as o, ThreadPoolExecutor(jobs) as ex:
    for r in ex.map(one, files):
        if r: o.write(json.dumps(r) + "\n"); o.flush()
rows = [json.loads(l) for l in open(out)]
diff = [r for r in rows if (r["ref"]["rc"], r["ref"]["d"] == 0) != (r["new"]["rc"], r["new"]["d"] == 0)]
msg = [r for r in rows if r not in diff and r["ref"]["errors"] != r["new"]["errors"]]
viol = [r for r in rows if r["violations"]]
print(len(rows), "programs; verdict differs:", len(diff), "; only messages differ:", len(msg), "; self-check violations:", len(viol))
for r in diff: print("  VERDICT", r["file"], "ref d=", r["ref"]["d"], r["ref"]["rc"], "new d=", r["new"]["d"], r["new"]["rc"], (r["new"]["errors"] or r["ref"]["errors"] or [""])[0][:90])
for r in viol[:20]: print("  VIOLATION", r["file"], r["violations"][0][:160])
