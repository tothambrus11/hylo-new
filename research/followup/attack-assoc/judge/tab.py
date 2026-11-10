"""Prints one row per program and one column per configuration from results.jsonl.
usage: tab.py BINPREFIX CONFIG;CONFIG... [name-prefix...]"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
binp, configs, pre = sys.argv[1], sys.argv[2].split(";"), sys.argv[3:]
rows, order = {}, []
for l in open(os.path.join(HERE, "results.jsonl")):
    r = json.loads(l)
    if not r["bin"].startswith(binp): continue
    if r["program"] not in rows: rows[r["program"]] = {}; order.append(r["program"])
    v = r["verdict"]
    rows[r["program"]][r["config"]] = ("VIOL" if r["violations"] else "acc" if v == "accept" else "rej%d" % len(r["errors"]) if v == "reject" else v)
print(f"{'program':40}" + "".join(f"{c[-12:]:>13}" for c in configs))
for p in order:
    if pre and not any(p.startswith(x) for x in pre): continue
    print(f"{p[:40]:40}" + "".join(f"{rows[p].get(c, '-'):>13}" for c in configs))
