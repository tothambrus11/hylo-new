"""Which technique removes a blow-up? Runs selected mutants under MIN5 plus individual fixes.

Usage: python3 attrib.py MUTANT-ID ...   (appends to attrib.jsonl; restartable)
The memory cap is lowered to 600 MB and the timeout to 60 s so that a blow-up is detected quickly.
"""
import json, os, sys
import tc, run

OUT = os.path.join(tc.HERE, "attrib.jsonl")
M = tc.MIN5
FULL_FLAGS = tc.FULL.split(",")
def without(*xs): return ",".join(f for f in FULL_FLAGS if f not in xs)
CONFIGS = {
    "min5+budget": M + ",budget",
    "min5+eqsolve": M + ",eqsolve",
    "min5+occurs,fixsubst,eqsolve": M + ",occurs,fixsubst,eqsolve",
    "fix": tc.FIX,
    "fix-budget": ",".join(f for f in tc.FIX.split(",") if f != "budget"),
    "fix-eqsolve": ",".join(f for f in tc.FIX.split(",") if f != "eqsolve"),
    "full-absmodel,absquotient": without("absmodel", "absquotient"),
    "full-budget": without("budget"),
    "full-eqsolve": without("eqsolve"),
}

def main():
    ids = sys.argv[1:]
    done = set()
    if os.path.exists(OUT):
        for ln in open(OUT):
            r = json.loads(ln); done.add((r["id"], r["config"]))
    mutants = {m["id"]: m for m in run.load_mutants()}
    os.environ["TCX_MEM_LIMIT_KB"] = "600000"
    with open(OUT, "a") as out:
        for mid in ids:
            m = mutants[mid]
            try:
                prog, part = run.materialize(m)
                for c, flags in CONFIGS.items():
                    if (mid, c) in done: continue
                    r = tc.run(prog, flags, timeout=60)
                    row = {"id": mid, "config": c}
                    row.update(tc.summarize(r, part))
                    out.write(json.dumps(row) + "\n"); out.flush()
                    print(mid, c, row["status"], row["diags"], row["matches"], row["ms"], flush=True)
            finally:
                if m["group"] == "stdlib": run.restore_stdlib()

if __name__ == "__main__":
    main()
