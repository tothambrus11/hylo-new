"""Careful timing of selected mutants: MIN5 and MIN5+absmodel alternately, N runs each, minimum kept.

Usage: python3 timing.py [-n N] MUTANT-ID ...   (appends one row per mutant to timing.jsonl)
Wall-clock times on this shared machine are noisy; the minimum of several runs is the least bad estimate.
"""
import json, os, sys
import tc, run

OUT = os.path.join(tc.HERE, "timing.jsonl")

def main():
    a = sys.argv[1:]
    n = 5
    if a and a[0] == "-n": n = int(a[1]); a = a[2:]
    done = set()
    if os.path.exists(OUT):
        for ln in open(OUT): done.add(json.loads(ln)["id"])
    mutants = {m["id"]: m for m in run.load_mutants()}
    with open(OUT, "a") as out:
        for mid in a:
            if mid in done: continue
            m = mutants[mid]
            try:
                prog, part = run.materialize(m)
                ts = {"min5": [], "min5abs": []}
                micros = []
                for _ in range(n):
                    for c in ts:
                        r = tc.run(prog, tc.CONFIGS[c], timeout=120)
                        s = tc.summarize(r, part)
                        if s["status"] == "ok": ts[c].append(s["ms"])
                        if c == "min5abs": micros.append(s["all"].get("absmodel.micros", 0))
                row = {"id": mid, "n": n, "min5_ms": ts["min5"], "min5abs_ms": ts["min5abs"], "absmodel_micros": micros}
                out.write(json.dumps(row) + "\n"); out.flush()
                print(mid, "min5", min(ts["min5"] or [None]), "min5abs", min(ts["min5abs"] or [None]), flush=True)
            finally:
                if m["group"] == "stdlib": run.restore_stdlib()

if __name__ == "__main__":
    main()
