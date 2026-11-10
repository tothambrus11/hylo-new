#!/usr/bin/env python3
"""Runs the compiler's tests at several values of the search bound.

Usage: corpus_scan.py [--configs base,FULL] [--depths 10,40]

For each test of Tests/CompilerTests/{positive,negative} and each (configuration, bound), records
the verdict, the diagnostics and the user-module counters in experiments/corpus-scan.jsonl.
Restartable: pairs already recorded are skipped. The question it answers: does any test reach the
bound today (summon.depthExhausted), and does any verdict or any amount of work change when the
bound on the size of a derivation is raised (which over-approximates replacing it by a bound on
the height)?
"""
import argparse, glob, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run as R

ap = argparse.ArgumentParser()
ap.add_argument("--configs", default="base,FULL")
ap.add_argument("--depths", default="10,40")
ap.add_argument("--out", default=os.path.join(R.HERE, "experiments", "corpus-scan.jsonl"))
a = ap.parse_args()
root = os.path.join(R.HERE, "..", "..", "..", "Tests", "CompilerTests")
files = sorted(glob.glob(os.path.join(root, "positive", "*.hylo")) +
               glob.glob(os.path.join(root, "negative", "*.hylo")))
done = set()
if os.path.exists(a.out):
    for l in open(a.out):
        j = json.loads(l)
        done.add((j["program"], j["config"], j["depth"]))
for f in files:
    rel = os.path.relpath(os.path.abspath(f), R.HERE)
    for c in a.configs.split(","):
        for d in [int(x) for x in a.depths.split(",")]:
            if (rel, c, d) in done:
                continue
            r = R.run(os.path.abspath(f), c, d, timeout=120)
            with open(a.out, "a") as o:
                o.write(json.dumps(r) + "\n")
print("done", len(files), "files")
