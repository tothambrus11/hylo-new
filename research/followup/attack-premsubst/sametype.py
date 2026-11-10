"""Runs the programs of same-type/ under NEW: one clause each, called as f<A, A>() (y4: f<A, A2>()).
Every program is well typed. Results go to sametype.jsonl (restartable); prints clause and verdict."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import run, tcrun
OUT = os.path.join(HERE, "sametype.jsonl")
done = {r["file"]: r for r in map(json.loads, open(OUT))} if os.path.exists(OUT) else {}
tcrun.CONFIGS["_"] = run.flags("NEW")
for f in sorted(os.listdir(os.path.join(HERE, "same-type"))):
    path = os.path.join(HERE, "same-type", f)
    if f not in done:
        x = tcrun.run(run.BIN, "_", path, 60)
        done[f] = {"file": f, "verdict": x["verdict"], "first": (x["errors"] or [""])[0]}
        with open(OUT, "a") as o: o.write(json.dumps(done[f]) + "\n")
    src = open(path).read()
    clause = src.split("fun f<T, U where ")[1].split(">() {}")[0]
    call = src.split("main() { ")[1].split(" }")[0]
    print(f"{f[:-5]:4} {done[f]['verdict']:7} {call:12} {clause}")
