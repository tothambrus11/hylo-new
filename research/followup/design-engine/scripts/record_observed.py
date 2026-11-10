#!/usr/bin/env python3
"""Records, in the header of each test that has a line "// observed:", what a binary that implements
`premsubst` as first designed does with it.

Usage: record_observed.py [--bin eq25-c7cbd846a05c] [FILE.hylo...]   (default: tests/*.hylo)

Runs each program under FULL+premsubst, FULL+premsubst+selfcheck, FULL+premsubst+assocsubst and NEW
(one tc-bench process at a time), writes the raw results to tests/observed.jsonl, and replaces the
line starting with "// observed:" by a summary. Restartable: results already in the file are reused.
"""
import glob, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run as R
import review_run as V

CONFIGS = ["FULL+premsubst", "FULL+premsubst+selfcheck", "FULL+premsubst+assocsubst", "NEW"]
a = sys.argv[1:]
binid = "eq25-c7cbd846a05c"
if a[:1] == ["--bin"]:
    binid, a = a[1], a[2:]
files = a or sorted(glob.glob(os.path.join(R.HERE, "tests", "*.hylo")))
out = os.path.join(R.HERE, "tests", "observed.jsonl")
old = {}
if os.path.exists(out):
    for l in open(out):
        j = json.loads(l)
        old[(j["program"], j["bin"], j["config"])] = j


def brief(r):
    cs = r["counters"]
    c = " ".join("%s=%s" % (k.split(".")[1], cs[k]) for k in
                 ("premsubst.bound", "premsubst.released", "premsubst.normalized", "premsubst.stuck",
                  "summon.depthExhausted") if cs.get(k))
    s = r["verdict"] + (" (" + c + ")" if c else "")
    if r["violations"]:
        s += " VIOLATION: " + r["violations"][0][:80]
    return s


for f in files:
    f = os.path.abspath(f)
    src = open(f).read().split("\n")
    at = [i for i, l in enumerate(src) if l.startswith("// observed:")]
    if not at:
        continue
    rs = {}
    for c in CONFIGS:
        k = (os.path.relpath(f, R.HERE), binid, c)
        if k not in old:
            old[k] = V.run(binid, f, c)
            with open(out, "a") as o:
                o.write(json.dumps(old[k]) + "\n")
        rs[c] = old[k]
    sc = rs["FULL+premsubst+selfcheck"]
    line = "// observed: (%s, premsubst as first designed) FULL+premsubst %s; +selfcheck %s; +assocsubst %s; NEW %s" % (
        binid.split("-")[0], brief(rs["FULL+premsubst"]),
        "same" if (sc["verdict"] == rs["FULL+premsubst"]["verdict"] and not sc["violations"]) else brief(sc),
        rs["FULL+premsubst+assocsubst"]["verdict"], rs["NEW"]["verdict"])
    src[at[0]] = line
    open(f, "w").write("\n".join(src))
    print(os.path.basename(f), "|", line[13:])
