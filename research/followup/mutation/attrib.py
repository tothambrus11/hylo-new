"""Which technique removes a blow-up? Runs selected mutants under MIN5 plus individual fixes.

Usage: python3 attrib.py [--configs "name;name;..."] MUTANT-ID ...   (appends to attrib.jsonl; restartable)
The memory cap is lowered to 600 MB and the timeout to 60 s so that a blow-up is detected quickly.
"""
import json, os, sys
import tc, run

OUT = os.path.join(tc.HERE, "attrib.jsonl")
M = tc.MIN5
FULL_FLAGS = tc.FULL.split(",")
def without(*xs): return ",".join(f for f in FULL_FLAGS if f not in xs)
FIX_FLAGS = tc.FIX.split(",")
def fix_without(*xs): return ",".join(f for f in FIX_FLAGS if f not in xs)
CONFIGS = {
    "min5+budget": M + ",budget",
    "min5+eqsolve": M + ",eqsolve",
    "min5+occurs,fixsubst,eqsolve": M + ",occurs,fixsubst,eqsolve",
    "min5+occurs": M + ",occurs",
    "min5+eqmgu": M + ",eqmgu",
    "min5+givencheck": M + ",givencheck",
    "min5+arrowenv": M + ",arrowenv",
    "min5+extorder": M + ",extorder",
    "fix": tc.FIX,
    "fix-budget": fix_without("budget"),
    "fix-eqsolve": fix_without("eqsolve"),
    "fix-eqmgu": fix_without("eqmgu"),
    "fix-givencheck": fix_without("givencheck"),
    "fix-arrowenv": fix_without("arrowenv"),
    "fix-occurs": fix_without("occurs"),
    "fix-extorder": fix_without("extorder"),
    "full-absmodel,absquotient": without("absmodel", "absquotient"),
    "full-budget": without("budget"),
    "full-eqsolve": without("eqsolve"),
}

def main():
    ids = sys.argv[1:]
    names = list(CONFIGS)
    if ids and ids[0] == "--configs":
        names = ids[1].split(";"); ids = ids[2:]
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
                for c in names:
                    flags = CONFIGS[c]
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
