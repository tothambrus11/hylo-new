"""Prints every diagnostic recorded in results.jsonl for the given programs (latest run of each
configuration). usage: show.py [--configs "A;B"] FILE..."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
a = sys.argv[1:]; configs = None
if "--configs" in a: i = a.index("--configs"); configs = a[i + 1].split(";"); del a[i:i + 2]
last = {}
for l in open(os.path.join(HERE, "results.jsonl")):
    r = json.loads(l); last[(r["program"], r["config"])] = r
for f in a:
    rel = os.path.relpath(os.path.abspath(f), HERE)
    for (p, c), r in last.items():
        if p != rel or (configs and c not in configs): continue
        print(f"== {p} [{c}] {r['bin'][:4]} {r['verdict']} {r['counters']}")
        for e in r["errors"] + r["violations"]: print("   ", e)
