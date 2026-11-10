"""Runs existing programs that have a requirement on a projection under FULL, NEW and NEW without
premsubst, to find verdicts that the flag changes. Restartable; raw results in corpus.jsonl.

Programs: the 76 research test programs listed in ../design-engine/experiments/dependent-programs.jsonl,
../design-engine/tests/s1-*.hylo, ../headsubst/tests/*.hylo and the compiler tests whose where clause
mentions a projection. `corpus.py --report` prints the programs whose verdicts differ."""
import glob, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import run, tcrun
OUT = os.path.join(HERE, "corpus.jsonl")
CONFIGS = ["FULL", "NEW", "NEW-premsubst"]
def programs():
    F = os.path.dirname(HERE)
    ps = {os.path.join(os.path.dirname(F), "report", json.loads(l)["program"].split("/report/")[1])
          for l in open(os.path.join(F, "design-engine", "experiments", "dependent-programs.jsonl"))}
    ps |= set(glob.glob(os.path.join(F, "design-engine", "tests", "s1-*.hylo")))
    ps |= set(glob.glob(os.path.join(F, "headsubst", "tests", "*.hylo")))
    for f in glob.glob("/home/user/hylo-new/Tests/CompilerTests/*/*.hylo"):
        if re.search(r"where[^{]*\.[A-Z]", open(f).read()): ps.add(f)
    return sorted(ps)
def load():
    return {(r["program"], r["config"]): r for r in map(json.loads, open(OUT))} if os.path.exists(OUT) else {}
if __name__ == "__main__":
    done = load()
    if "--report" in sys.argv:
        for p in programs():
            rs = [done.get((p, c)) for c in CONFIGS]
            if None in rs: continue
            vs = [r["verdict"] + ("!VIOL" if r["violations"] else "") + ("!STUCK" if r["counters"].get("premsubst.stuck") else "") for r in rs]
            if len(set(vs)) > 1 or "!" in "".join(vs):
                print(f"{os.path.relpath(p, os.path.dirname(HERE))[:70]:70} " + " ".join(f"{v:8}" for v in vs) + " | " + (rs[1]["errors"] or [""])[0][:60])
        sys.exit(0)
    for p in programs():
        for c in CONFIGS:
            if (p, c) in done: continue
            tcrun.CONFIGS["_"] = run.flags(c)
            x = tcrun.run(run.BIN, "_", p, 60)
            r = {"program": p, "config": c, "verdict": x["verdict"], "errors": x["errors"][:3], "violations": x["violations"],
                 "counters": {k: v for k, v in x["counters"].items() if k.startswith(("premsubst", "eqsolve.premises", "summon.depthExhausted", "selfcheck"))}}
            with open(OUT, "a") as o: o.write(json.dumps(r) + "\n")
    print("done")
