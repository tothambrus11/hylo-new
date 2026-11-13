"""For each equality proved by the decision procedure, does search complete in the layer that the
procedure reports? Sums the self-check counters over programs.
usage: size_parity.py BINID OUT.jsonl DIR..."""
import json, os, sys
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); import tcrun
binid, out, dirs = sys.argv[1], sys.argv[2], sys.argv[3:]
files = []
for d in dirs:
    if d.endswith(".hylo"): files.append(d)
    else: files += sorted(os.path.join(r, f) for r, _, fs in os.walk(d) for f in fs if f.endswith(".hylo"))
def one(f):
    r = tcrun.run(binid, "RECZ+selfcheck", f, 120)
    return {"file": f, "verdict": r["verdict"], "violations": r["violations"][:2],
            **{k.split(".")[2]: v for k, v in r["counters"].items() if k.startswith("selfcheck.equality.")}}
with open(out, "w") as o, ThreadPoolExecutor(2) as ex:
    for r in ex.map(one, files): o.write(json.dumps(r) + "\n"); o.flush()
