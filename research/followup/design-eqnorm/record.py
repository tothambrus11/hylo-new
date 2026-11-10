#!/usr/bin/env python3
"""Records the current verdict of every program in tests/ under base and FULL.

For each tests/*.hylo, runs the frozen binary (one process at a time), appends the raw result to
tests/current.jsonl (pairs already there are not run again), and rewrites the line that starts with
"// currently:" in the program. Run it again after a compiler change with another binary by
editing `run.B`; delete tests/current.jsonl first.
"""
import glob, json, os, sys
import run

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "tests", "current.jsonl")
CONFIGS = ["base", "FULL"]
SHOWN = ["summon.subgoals", "summon.matches", "summon.depthExhausted", "eqsolve.proved",
         "eqsolve.refuted", "eqmgu.solved", "index.fallback", "absmodel.refuted"]


def main():
    done = {}
    if os.path.exists(OUT):
        for l in open(OUT):
            j = json.loads(l)
            done[(j["program"], j["config"])] = j
    for f in sorted(glob.glob(os.path.join(HERE, "tests", "*.hylo"))):
        rel = os.path.relpath(f, HERE)
        parts = []
        for c in CONFIGS:
            if (rel, c) not in done:
                r = run.run(f, c, timeout=40)
                done[(rel, c)] = r
                with open(OUT, "a") as o:
                    o.write(json.dumps(r) + "\n")
            r = done[(rel, c)]
            cs = " ".join("%s=%d" % (k, r["counters"][k]) for k in SHOWN if k in r.get("counters", {}))
            v = r["verdict"]
            if v == "crash(-6)":
                v = "out of memory"
            parts.append("%s %s (%s)" % (c, v, cs) if cs else "%s %s" % (c, v))
        e = done[(rel, "FULL")].get("first_error", "")
        line = "// currently: " + "; ".join(parts) + (". FULL says: " + e[:150] if e else ".")
        src = open(f).read().split("\n")
        src = [line if l.startswith("// currently:") else l for l in src]
        open(f, "w").write("\n".join(src))
        print(os.path.basename(f), "|", line[14:200])
        sys.stdout.flush()


if __name__ == "__main__":
    main()
