#!/usr/bin/env python3
"""Reduces one violating variant for each (program text, relation, kind of variant, pair of
verdicts) found under FULL, and writes violations/index.jsonl. Restartable: a violation whose
directory already holds info.json is not reduced again.

usage: reduce_all.py [REL...]"""
import hashlib, json, os, re, sys
from common import HERE, ROOT
from reduce import reduce

rels = sys.argv[1:]
seen, index = set(), []
for l in open(os.path.join(HERE, "data", "rows-FULL.jsonl")):
    r = json.loads(l)
    if not r.get("violation") or r.get("invalid") or (rels and r["rel"] not in rels): continue
    path = os.path.join(ROOT, r["file"])
    key = (hashlib.sha1(open(path, "rb").read()).hexdigest(), r["rel"], r["kind"], r["base_verdict"], r["verdict"])
    if key in seen: continue
    seen.add(key)
    name = os.path.basename(path)[:-5] + "--" + re.sub(r"[^A-Za-z0-9]+", "-", r["vid"]).strip("-")
    out = os.path.join(HERE, "violations", r["rel"], name)
    if not os.path.exists(os.path.join(out, "info.json")):
        try:
            reduce(path, r["rel"], r["vid"], "FULL", out)
        except SystemExit as e:
            print("skipped", r["file"], r["vid"], e); continue
    info = json.load(open(os.path.join(out, "info.json")))
    info["dir"] = os.path.relpath(out, HERE)
    index.append(info)
    print(info["dir"], {c: "%s/%s" % (v["a"], v["b"]) for c, v in info["reduced"].items()}, flush=True)
existing = []
p = os.path.join(HERE, "violations", "index.jsonl")
if rels and os.path.exists(p):
    existing = [x for x in map(json.loads, open(p)) if x["rel"] not in rels]
with open(p, "w") as o:
    for x in existing + index: o.write(json.dumps(x) + "\n")
