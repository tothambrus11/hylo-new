#!/usr/bin/env python3
"""Prints a compact table of results.jsonl: one row per program, one column per (binary, configuration).
usage: show.py [PREFIX...]   (program name prefixes; all programs if none)
A = accept, R = reject, C = crash, T = timeout; '!' marks a self-check violation; the number is the count of diagnostics."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
COLS = [("eq22", "base"), ("eq22", "FULL"), ("eq22", "FULL+sigrounds"), ("eq22", "NOSIG22"), ("eq22", "NEW22"), ("eq22", "NEW22+selfcheck"),
        ("eq38", "FULL"), ("eq38", "NOSIG"), ("eq38", "NEW"), ("eq38", "NEW+selfcheck")]
rows, order = {}, []
for l in open(os.path.join(HERE, "results.jsonl")):
    r = json.loads(l)
    if r["program"] not in rows: rows[r["program"]] = {}; order.append(r["program"])
    v = r["verdict"]; s = {"accept": "A", "reject": "R", "timeout": "T"}.get(v, "C")
    if r["errors"]: s += str(len(r["errors"]))
    if r["violations"]: s += "!"
    rows[r["program"]][(r["bin"][:4], r["config"])] = s
pre = tuple(sys.argv[1:])
print(f"{'program':46} " + " ".join(f"{(b[2:] + ':' + c.replace('+selfcheck', '+sc').replace('+sigrounds', '+sig'))[:10]:10}" for b, c in COLS))
for p in order:
    if pre and not p.startswith(pre): continue
    print(f"{p[:46]:46} " + " ".join(f"{rows[p].get(k, '-'):10}" for k in COLS))
