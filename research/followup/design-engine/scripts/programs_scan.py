#!/usr/bin/env python3
"""Runs the research test programs (research/report/test-programs/*/*.hylo) under one configuration.

Usage: programs_scan.py [--config FULL] [--depth N]   (appends to experiments/programs-scan.jsonl)

Records the verdict and the counters of each program. It is used to find (a) the programs in which
the equality procedure resolves a pending premise ahead of time (`eqsolve.premises` > 0), which are
the programs that substituting discharged premises affects, and (b) the programs in which a
resolution reaches the bound (`summon.depthExhausted` > 0), which are the programs that a
different bound affects. Restartable.
"""
import argparse, glob, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run as R

ap = argparse.ArgumentParser()
ap.add_argument("--config", default="FULL")
ap.add_argument("--depth", type=int, default=None)
ap.add_argument("--dirs", default="*", help="comma-separated subdirectories of test-programs")
ap.add_argument("--out", default=os.path.join(R.HERE, "experiments", "programs-scan.jsonl"))
a = ap.parse_args()
root = os.path.join(R.HERE, "..", "..", "report", "test-programs")
files = sorted(f for d in a.dirs.split(",") for f in glob.glob(os.path.join(root, d, "*.hylo")))
done = set()
if os.path.exists(a.out):
    for l in open(a.out):
        j = json.loads(l)
        done.add((j["program"], j["config"], j["depth"]))
for f in files:
    rel = os.path.relpath(os.path.abspath(f), R.HERE)
    if (rel, a.config, a.depth or 10) in done:
        continue
    r = R.run(os.path.abspath(f), a.config, a.depth, timeout=30)
    with open(a.out, "a") as o:
        o.write(json.dumps(r) + "\n")
print("done", len(files), "programs")
