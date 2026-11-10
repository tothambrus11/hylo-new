"""Runs the compiler tests and the mechanism's own tests under FULL, NEW and NEW without
headsubst, and prints the programs whose verdict or number of errors differs between two of
them. Results go to screen.jsonl (restartable). usage: screen.py FILE..."""
import hashlib, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import tcrun
BIN = "eq34-6718f1de213f"; OUT = os.path.join(HERE, "screen.jsonl")
NEW = tcrun.CONFIGS["NEW"]
CONFIGS = {"FULL": tcrun.CONFIGS["FULL"], "NEW": NEW,
           "NEW-headsubst": ",".join(f for f in NEW.split(",") if f != "headsubst")}
done = {}
if os.path.exists(OUT):
    for l in open(OUT): r = json.loads(l); done[(r["file"], r["config"], r["sha"])] = r
for f in sys.argv[1:]:
    sha = hashlib.sha1(open(f, "rb").read()).hexdigest()[:12]; row = {}
    for c, flags in CONFIGS.items():
        r = done.get((f, c, sha))
        if r is None:
            x = tcrun.run(BIN, flags, f)
            r = {"file": f, "config": c, "sha": sha, "verdict": x["verdict"], "errors": x["errors"]}
            with open(OUT, "a") as o: o.write(json.dumps(r) + "\n")
        row[c] = (r["verdict"], len(r["errors"]))
    if len(set(row.values())) > 1:
        print(os.path.basename(f), " ".join(f"{c}={v[0]}/{v[1]}" for c, v in row.items()))
