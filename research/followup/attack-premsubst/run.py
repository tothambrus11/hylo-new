"""Runs the attack programs of p/ under several configurations; restartable.

usage: run.py [--configs "base;FULL;NEW;..."] [FILE...]      (default: every p/*.hylo)
Raw results are appended to results.jsonl, one line per (program, content hash, configuration);
a run that is already there is not repeated. One tc-bench process at a time, under a timeout.
Configurations: those of ../tcrun.py, plus NEW-flag (NEW without one flag), +flag as in tcrun."""
import hashlib, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import tcrun
BIN = "eq22-554540c3a507"
DEFAULT = "FULL;NEW;NEW+selfcheck;NEW-premsubst;FULL+premsubst"
OUT = os.path.join(HERE, "results.jsonl")

def flags(config):
    """Like tcrun.flags, with `NEW-flag` meaning NEW without that flag."""
    parts = config.split("+")
    head = parts[0].split("-")
    fs = tcrun.CONFIGS.get(head[0], head[0]).split(",")
    fs = [f for f in fs if f and f not in head[1:]]
    return ",".join(fs + parts[1:])

def load():
    done = {}
    if os.path.exists(OUT):
        for l in open(OUT):
            r = json.loads(l)
            done[(r["program"], r["sha"], r["config"])] = r
    return done

def main():
    a = sys.argv[1:]
    configs = DEFAULT
    if "--configs" in a:
        i = a.index("--configs"); configs = a[i + 1]; del a[i:i + 2]
    files = a or sorted(os.path.join(HERE, "p", f) for f in os.listdir(os.path.join(HERE, "p")) if f.endswith(".hylo"))
    done = load()
    for f in files:
        sha = hashlib.sha1(open(f, "rb").read()).hexdigest()[:12]
        name = os.path.relpath(os.path.abspath(f), HERE)
        for c in configs.split(";"):
            r = done.get((name, sha, c))
            if r is None:
                tcrun.CONFIGS["_"] = flags(c)
                x = tcrun.run(BIN, "_", f, 60)
                keep = ("premsubst", "summon.subgoals", "summon.matches", "summon.depthExhausted", "eqsolve.premises",
                        "eqsolve.proved", "absmodel.refuted", "selfcheck", "headsubst", "eqeager", "summon.budget")
                r = {"program": name, "sha": sha, "config": c, "verdict": x["verdict"], "errors": x["errors"],
                     "violations": x["violations"],
                     "counters": {k: v for k, v in x["counters"].items() if any(k.startswith(p) for p in keep)}}
                with open(OUT, "a") as o: o.write(json.dumps(r) + "\n")
            cs = " ".join(f"{k.replace('premsubst.', 'ps.')}={v}" for k, v in r["counters"].items()
                          if k.startswith("premsubst") or k in ("eqsolve.premises", "summon.depthExhausted", "absmodel.refuted"))
            print(f"{os.path.basename(f)[:40]:40} {c[:18]:18} {r['verdict']:8} {cs} | {(r['violations'] or r['errors'] or [''])[0][:120]}")

if __name__ == "__main__":
    main()
