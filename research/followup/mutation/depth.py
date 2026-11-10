"""Cost of selected mutants as a function of the search depth bound HYLO_TC_MAXDEPTH.

Usage: python3 depth.py [--depths 6,8] MUTANT-ID ...     (appends to depth.jsonl; pairs already there are skipped)
For each mutant: configurations base, min5, min5abs at depths 10, 12, 14 (or --depths a,b,c), for the
mutant and for the unmutated source. Memory cap 1 GB, timeout 120 s.
"""
import json, os, sys
import tc, run

OUT = os.path.join(tc.HERE, "depth.jsonl")
DEPTHS = [10, 12, 14]
CFGS = ["base", "min5", "min5abs"]

def main():
    global DEPTHS
    ids = sys.argv[1:]
    if ids and ids[0] == "--depths":
        DEPTHS = [int(x) for x in ids[1].split(",")]; ids = ids[2:]
    os.environ.setdefault("TCX_MEM_LIMIT_KB", "1000000")   # blow-ups are detected at 1 GB
    done = set()
    if os.path.exists(OUT):
        for ln in open(OUT):
            r = json.loads(ln); done.add((r["id"], r["what"], r["config"], r["depth"]))
    mutants = {m["id"]: m for m in run.load_mutants()}
    with open(OUT, "a") as out:
        for mid in ids:
            m = mutants[mid]
            for what in ("mutant", "original"):
                try:
                    if what == "mutant":
                        prog, part = run.materialize(m)
                    elif m["group"] == "stdlib":
                        run.restore_stdlib(); prog, part = tc.EMPTY, "stdlib"
                    else:
                        prog, part = run.source_path(m), "user"
                    for c in CFGS:
                        for d in DEPTHS:
                            if (mid, what, c, d) in done: continue
                            r = tc.run(prog, tc.CONFIGS[c], timeout=120, env_extra={"HYLO_TC_MAXDEPTH": str(d)})
                            row = {"id": mid, "what": what, "config": c, "depth": d}
                            row.update(tc.summarize(r, part))
                            out.write(json.dumps(row) + "\n"); out.flush()
                            print(mid, what, c, d, row["status"], row["diags"], row["matches"], row["ms"], flush=True)
                finally:
                    if m["group"] == "stdlib": run.restore_stdlib()

if __name__ == "__main__":
    main()
