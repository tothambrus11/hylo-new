#!/usr/bin/env python3
"""Pivot tc-bench --count outputs: table.py DIR WORKLOAD [phase=stdlib|user] [counter-regex]"""
import sys, os, re, glob
d, wl = sys.argv[1], sys.argv[2]
phase = sys.argv[3] if len(sys.argv) > 3 else "user"
rx = re.compile(sys.argv[4]) if len(sys.argv) > 4 else re.compile(".")
FL = "names unify index absmodel solver loopcheck".split()
rows = {}
for f in glob.glob(f"{d}/{wl}__*.txt"):
    cfg = os.path.basename(f)[len(wl) + 2:-4]
    txt = open(f).read()
    m = re.search(rf"counters\.{phase}:\s*(.*)", txt)
    kv = dict(x.split("=") for x in (m.group(1).split() if m else []))
    kv = {k: int(v) for k, v in kv.items()}
    kv["diags"] = int(re.search(r"diagnostics: (\d+)", txt).group(1)) if "diagnostics:" in txt else -1
    if "TIMEOUT" in txt: kv["TIMEOUT"] = 1
    rows[cfg] = kv
def label(c):
    if c == "base": return "base"
    s = set(c.split(","))
    if s == set(FL): return "ALL"
    if len(s) == 5: return "ALL-" + (set(FL) - s).pop()
    return c
order = sorted(rows, key=lambda c: (0 if c == "base" else 1 if label(c) == "ALL" else 2 if label(c).startswith("ALL-") else 3, label(c)))
keys = sorted({k for r in rows.values() for k in r if rx.search(k)})
keys = [k for k in keys if not k.endswith("micros") or rx.pattern != "."]
print(f"## {wl} ({phase})")
print("| counter | " + " | ".join(label(c) for c in order) + " |")
print("|---|" + "---:|" * len(order))
for k in keys:
    print(f"| {k} | " + " | ".join(str(rows[c].get(k, "")) for c in order) + " |")
