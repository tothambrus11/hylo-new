"""Census of implicit resolutions.

usage: census.py BINID OUT.json
Runs the checker with the `census` flag (one record per resolution: kind of goal, visible givens,
layers explored, candidates matched, results) on the standard library and on the compiler's
positive tests, under the existing checker and under all techniques, and aggregates."""
import glob, json, os, re, statistics, subprocess, sys
RES = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = os.path.join(RES, "exp", "bin", sys.argv[1], "tc-bench")
FIX = "occurs,fixsubst,eqsolve,extorder,arrowenv,eqmgu,givencheck,budget"
CONFIGS = {"base": "", "FULL": FIX + ",symindex,coesrc,traitindex,memberskip,unify,index,absmodel,absquotient,typevec,reifymemo"}
def records(path, flags):
    p = subprocess.run([B, path], env=dict(os.environ, HYLO_TC_EXPERIMENTS=(flags + ",census").strip(",")),
                       capture_output=True, text=True, timeout=300)
    return [json.loads(l[9:]) for l in p.stdout.split("\n") if l.startswith("[census] ")]
def q(xs, p):
    xs = sorted(xs); return xs[min(len(xs) - 1, int(p * len(xs)))] if xs else None
def summary(rs):
    out = {}
    for kind in ("conformance", "equality", "other"):
        k = [r for r in rs if r["kind"] == kind]
        if not k: out[kind] = {"n": 0}; continue
        fail = [r for r in k if r["done"] == 0]
        out[kind] = {"n": len(k), "failing": len(fail), "ambiguous": sum(r["minimal"] > 1 for r in k),
                     "with_assumptions": sum(r["assumed"] > 0 for r in k), "open": sum(r["open"] for r in k),
                     "givens_median": q([r["givens"] for r in k], .5), "givens_p95": q([r["givens"] for r in k], .95),
                     "layers_median": q([r["layers"] for r in k], .5), "layers_p95": q([r["layers"] for r in k], .95), "layers_max": max(r["layers"] for r in k),
                     "matches_total": sum(r["matches"] for r in k), "matches_in_failing": sum(r["matches"] for r in fail),
                     "matches_median": q([r["matches"] for r in k], .5), "matches_p95": q([r["matches"] for r in k], .95), "matches_max": max(r["matches"] for r in k)}
    return out
result = {}
tests = sorted(glob.glob(os.path.join(RES, "..", "Tests", "CompilerTests", "positive", "*.hylo")))
for c, flags in CONFIGS.items():
    std = records(os.path.join(RES, "workloads", "empty.hylo"), flags)
    user = []
    for t in tests:
        try: user += records(t, flags)[len(std):]
        except Exception: pass
    result[c] = {"stdlib": summary(std), "positive_tests": summary(user)}
json.dump(result, open(sys.argv[2], "w"), indent=1)
for c in result:
    for part in result[c]:
        print(f"== {c} / {part}")
        for kind, s in result[c][part].items(): print("  ", kind, s)
