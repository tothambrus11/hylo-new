"""Counts, per program and configuration, the name-resolution ties decided by the size of a witness.
usage: witness_size.py BINID OUT.jsonl DIR..."""
import json, os, sys
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); import tcrun
binid, out, dirs = sys.argv[1], sys.argv[2], sys.argv[3:]
files = []
for d in dirs:
    if d.endswith(".hylo"): files.append(d)
    else: files += sorted(os.path.join(r, f) for r, _, fs in os.walk(d) for f in fs if f.endswith(".hylo"))
done = {json.loads(l)["file"] for l in open(out)} if os.path.exists(out) else set()
def one(f):
    if f in done: return None
    row = {"file": f}
    for c in ("base", "REC"):
        r = tcrun.run(binid, c, f, 60)
        row[c] = {"verdict": r["verdict"], **{k.split(".")[1]: v for k, v in r["counters"].items() if k.startswith("names.")}}
    return row
with open(out, "a") as o, ThreadPoolExecutor(2) as ex:
    for r in ex.map(one, files):
        if r: o.write(json.dumps(r) + "\n"); o.flush()
