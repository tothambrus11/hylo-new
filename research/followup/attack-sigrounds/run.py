#!/usr/bin/env python3
"""Runs attack programs under several configurations, one tc-bench process at a time.

usage: run.py [--configs "A;B;..."] [--force] FILE...

Appends one JSON line per (program, configuration) to results.jsonl and prints one line per run:
verdict, the sigrounds counters and the first message. A (program, configuration) pair whose
program text is unchanged since its last run is not run again unless --force is given.

Configurations (see ../tcrun.py): base, FULL, NEW, optionally followed by +flag+flag.
NOSIG is NEW without sigrounds; FULL+sigrounds is FULL with the single flag added; NEW-flag is NEW
without that flag."""
import hashlib, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import tcrun
BIN = "eq22-554540c3a507"
tcrun.CONFIGS["NOSIG"] = tcrun.CONFIGS["NEW"].replace(",sigrounds", "")
# NEW-flag is NEW without one flag (used to attribute a difference to an interaction).
for _f in ("memberskip", "index", "absmodel", "extorder", "givencheck", "premsubst", "headsubst", "assocsubst"):
    tcrun.CONFIGS["NEW-" + _f] = ",".join(x for x in tcrun.CONFIGS["NEW"].split(",") if x != _f)
DEFAULT = "base;FULL;FULL+sigrounds;NOSIG;NEW;NEW+selfcheck"
OUT = os.path.join(HERE, "results.jsonl")

def load():
    done = {}
    if os.path.exists(OUT):
        for l in open(OUT):
            r = json.loads(l); done[(r["program"], r["config"])] = r
    return done

def main():
    a = sys.argv[1:]; configs = DEFAULT; force = False; timeout = 60
    if "--configs" in a: i = a.index("--configs"); configs = a[i + 1]; del a[i:i + 2]
    if "--timeout" in a: i = a.index("--timeout"); timeout = int(a[i + 1]); del a[i:i + 2]
    if "--force" in a: a.remove("--force"); force = True
    done = load()
    for f in a:
        name = os.path.relpath(os.path.abspath(f), HERE)
        h = hashlib.sha1(open(f, "rb").read()).hexdigest()[:12]
        for c in configs.split(";"):
            r = done.get((name, c))
            if force or not r or r["sha"] != h:
                x = tcrun.run(BIN, c, f, timeout)
                r = {"program": name, "config": c, "sha": h, "verdict": x["verdict"], "errors": x["errors"],
                     "violations": x["violations"],
                     "counters": {k: v for k, v in x["counters"].items() if k.startswith(("sigrounds", "summon.calls", "names.appliesCalls"))}}
                open(OUT, "a").write(json.dumps(r) + "\n")
            cs = " ".join(f"{k.split('.')[1]}={v}" for k, v in r["counters"].items() if k.startswith("sigrounds"))
            msg = (["VIOLATION " + v for v in r["violations"]] + r["errors"] + [""])[0][:90]
            msg = f"[{len(r['errors'])}] " + msg if r["errors"] else msg
            print(f"{os.path.basename(name)[:40]:40} {c[:16]:16} {r['verdict']:8} {cs:40} {msg}")

if __name__ == "__main__":
    main()
