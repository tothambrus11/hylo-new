#!/usr/bin/env python3
"""Prints a summary of a .jsonl file written by orders.py: usage: show.py FILE.jsonl [SUBSTRING]"""
import json, os, sys
for l in open(sys.argv[1]):
    r = json.loads(l)
    if len(sys.argv) > 2 and sys.argv[2] not in r["file"]: continue
    if not r.get("split"): print(os.path.basename(r["file"]), r["config"], "NOT SPLIT"); continue
    kinds = {}
    for o in r["outcomes"]: kinds[o["outcome"]] = kinds.get(o["outcome"], 0) + o["n"]
    print(f'{os.path.basename(r["file"]):50} {r["config"]:5} decls={r["decls"]} fixed={r.get("fixed", 0)} perms={r["perms"]} ' + " ".join(f"{k}={v}" for k, v in sorted(kinds.items())))
    if "-v" in sys.argv:
        for o in r["outcomes"]: print("      ", o["outcome"], o["n"], o["example"], o["errors"][:3])
