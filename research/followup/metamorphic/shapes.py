#!/usr/bin/env python3
"""Declaration-order test of the hand-written programs in shapes/, one per shape of dependency
cycle. For each program: the original order and the first 23 permutations of relation 1, under
base, FIX and FULL. Writes shapes/results.jsonl (one row per program and configuration) and
prints a table. Restartable through the type-checker cache."""
import glob, json, os
from common import HERE, File, check
from metamorphic import variants_of

rows = []
for path in sorted(glob.glob(os.path.join(HERE, "shapes", "*.hylo"))):
    F, vs = variants_of(path, "r1")
    texts = [("original", F.render())] + [(v.vid, v.render(F)) for v in vs[:23]]
    for config in ("FULL", "FIX", "base"):
        out = {}
        for vid, t in texts:
            r = check(t, config)
            key = r["verdict"]
            out.setdefault(key, {"count": 0, "example": vid, "errors": r["errors"][:2]})["count"] += 1
        rows.append({"file": os.path.basename(path), "config": config, "orders": len(texts), "outcomes": out})
        print("%-32s %-5s %s" % (os.path.basename(path), config,
                                 ", ".join("%s: %d" % (k, v["count"]) for k, v in sorted(out.items()))), flush=True)
with open(os.path.join(HERE, "shapes", "results.jsonl"), "w") as o:
    for r in rows: o.write(json.dumps(r) + "\n")
