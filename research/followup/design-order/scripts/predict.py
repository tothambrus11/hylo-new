#!/usr/bin/env python3
"""For the declaration-order test programs that model.py can parse, compares the verdict of the
round semantics of the model with the verdicts recorded by the review's fuzzer for the FULL
configuration (research/followup/permute-full.jsonl).

usage: predict.py > results/predicted-verdicts.txt
"""
import glob, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import model

full = {}
for l in open("/home/user/hylo-new/research/followup/permute-full.jsonl"):
    r = json.loads(l)
    full[os.path.basename(r["file"])] = sorted({o["outcome"][0] for o in r["outcomes"]}) or ["?"]
rows, skipped = [], 0
for f in sorted(glob.glob("/home/user/hylo-new/research/report/test-programs/declaration-order/*.hylo")):
    text = "\n".join(l for l in open(f).read().split("\n") if not l.startswith("//!"))
    try:
        v, errs, k = model.rounds(model.parse(text))
    except Exception:
        skipped += 1; continue
    rows.append((os.path.basename(f), "/".join(full.get(os.path.basename(f), ["?"])), v, k))
same = sum(1 for r in rows if r[1] == r[2])
print(f"{len(rows)} programs modelled, {skipped} outside the subset of the model")
print(f"{same} have the same verdict under FULL (in every order tried) and under rounds")
print("the others:")
for r in rows:
    if r[1] != r[2]: print(f"  {r[0]:58} FULL: {r[1]:14} rounds: {r[2]} ({r[3]} rounds)")
