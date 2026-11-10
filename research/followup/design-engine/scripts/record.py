#!/usr/bin/env python3
"""Records the current verdict of every program of tests/ in its header.

Usage: record.py [FILE.hylo...]      (default: tests/*.hylo)

Runs each program under base and FULL (one tc-bench process at a time), writes the raw results to
tests/current.jsonl, and replaces the line starting with "// currently:" by a summary: verdict,
first diagnostic and the main counters of the user module under each configuration.
"""
import glob, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run as R

KEYS = ["summon.subgoals", "summon.matches", "summon.depthExhausted", "summon.budgetExhausted",
        "eqsolve.proved", "eqsolve.premises", "absmodel.refuted"]


def brief(r):
    v = r["verdict"]
    cs = r.get("counters", {})
    c = " ".join("%s=%s" % (k.split(".")[1], cs[k]) for k in KEYS if cs.get(k))
    s = v + (" (" + c + ")" if c else "")
    if v == "rejected":
        s += ": " + r.get("first_error", "")[:110]
    return s


files = sys.argv[1:] or sorted(glob.glob(os.path.join(R.HERE, "tests", "*.hylo")))
out = os.path.join(R.HERE, "tests", "current.jsonl")
old = {}
if os.path.exists(out):
    for l in open(out):
        j = json.loads(l)
        old[(j["program"], j["config"])] = j
for f in files:
    f = os.path.abspath(f)
    rs = {}
    for c in ("base", "FULL"):
        r = R.run(f, c, timeout=60)
        rs[c] = r
        old[(r["program"], c)] = r
    line = "// currently: base " + brief(rs["base"]) + "; FULL " + brief(rs["FULL"])
    src = open(f).read().split("\n")
    for i, l in enumerate(src):
        if l.startswith("// currently:"):
            src[i] = line
            break
    else:
        sys.exit("no '// currently:' line in " + f)
    open(f, "w").write("\n".join(src))
    print(os.path.basename(f), "|", line[14:200])
    with open(out, "w") as o:
        for k in sorted(old):
            o.write(json.dumps(old[k]) + "\n")
