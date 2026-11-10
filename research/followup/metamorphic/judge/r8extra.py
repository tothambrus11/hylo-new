#!/usr/bin/env python3
"""Judge's extra coverage for relation 8: the kinds the campaign generated but never ran
(`gconf`: an unrelated generic conformance; `ext`: an unrelated struct with an extension;
`conf-top`: an unrelated ground conformance placed first). FULL only, for programs whose
original is accepted or rejected under FULL (taken from data/baseline-FULL.jsonl).
usage: r8extra.py [SUBSTR ...]   -> appends to judge/r8-extra.jsonl (restartable)."""
import json, os, random, sys, zlib
HERE = os.path.dirname(os.path.abspath(__file__)); UP = os.path.dirname(HERE)
sys.path.insert(0, UP); sys.path.insert(0, HERE)
from hylosyn import File
from relations import r8_unrelated
import j
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(UP)))
OUT = os.path.join(HERE, "r8-extra.jsonl")
done = set()
if os.path.exists(OUT):
    for l in open(OUT): r = json.loads(l); done.add((r["file"], r["vid"]))
bl = [json.loads(l) for l in open(os.path.join(UP, "data", "baseline-FULL.jsonl"))]
subs = sys.argv[1:]
tmp = os.path.join(HERE, "tmp"); os.makedirs(tmp, exist_ok=True)
with open(OUT, "a") as o:
    for b in bl:
        if b.get("skip") or b.get("verdict") not in ("accept", "reject"): continue
        if subs and not any(s in b["file"] for s in subs): continue
        src = open(os.path.join(ROOT, b["file"])).read()
        F = File(src)
        rng = random.Random(zlib.crc32((src + "r8").encode()))
        for v in r8_unrelated.variants(F, rng):
            if v.kind not in ("gconf", "ext", "conf-top") or (b["file"], v.vid) in done: continue
            p = os.path.join(tmp, "v.hylo"); open(p, "w").write(v.render(F))
            r, _ = j.run(p, "FULL")
            errs = sorted(e.split(": ", 2)[2] for e in r["errors"] if e.startswith("error"))
            orig = sorted(e[len("error: "):] for e in b["errors"] if e.startswith("error"))
            row = {"file": b["file"], "vid": v.vid, "kind": v.kind, "orig": b["verdict"], "variant": r["verdict"],
                   "violation": r["verdict"] != b["verdict"], "messages_differ": errs != orig}
            if row["violation"] or row["messages_differ"]: row["errors"] = errs; row["orig_errors"] = orig
            o.write(json.dumps(row) + "\n"); o.flush()
