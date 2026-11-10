"""Compares two configurations program by program: verdict, messages, self-check violations.

usage: compare2.py BINID OUT.jsonl REF NEW DIR... [--jobs N]
REF and NEW are configurations of tcrun.py. NEW is also run with +selfcheck. Restartable."""
import json, os, sys
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import tcrun
a = sys.argv[1:]; jobs = 2
if "--jobs" in a: i = a.index("--jobs"); jobs = int(a[i + 1]); del a[i:i + 2]
binid, out, ref, new, dirs = a[0], a[1], a[2], a[3], a[4:]
files = []
for d in dirs:
    if d.endswith(".hylo"): files.append(d)
    else: files += sorted(os.path.join(r, f) for r, _, fs in os.walk(d) for f in fs if f.endswith(".hylo"))
done = {json.loads(l)["file"] for l in open(out)} if os.path.exists(out) else set()
def one(f):
    if f in done: return None
    x, y, z = tcrun.run(binid, ref, f), tcrun.run(binid, new, f), tcrun.run(binid, new + "+selfcheck", f, 120)
    keep = lambda r: {"verdict": r["verdict"], "errors": r["errors"][:3]}
    return {"file": f, "ref": keep(x), "new": keep(y), "violations": z["violations"][:3], "selfcheck": z["verdict"],
            "counters": {k: v for k, v in y["counters"].items() if k.split(".")[0] in ("sigrounds", "premsubst", "headsubst", "assocsubst", "eqeager")}}
with open(out, "a") as o, ThreadPoolExecutor(jobs) as ex:
    for r in ex.map(one, files):
        if r: o.write(json.dumps(r) + "\n"); o.flush()
rows = [json.loads(l) for l in open(out)]
ch = [r for r in rows if r["ref"]["verdict"] != r["new"]["verdict"]]
print(len(rows), "programs; verdict changes:", len(ch), "; violations:", sum(1 for r in rows if r["violations"]),
      "; selfcheck verdict differs:", sum(1 for r in rows if r["selfcheck"] != r["new"]["verdict"]))
for r in ch: print(f"  {r['ref']['verdict']:>7} -> {r['new']['verdict']:7} {os.path.relpath(r['file'])[:70]:70} {(r['new']['errors'] or r['ref']['errors'] or [''])[0][:80]}")
for r in rows:
    if r["violations"]: print("  VIOLATION", os.path.relpath(r["file"]), r["violations"][0][:140])
