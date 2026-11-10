"""Re-runs, with the default 2.5 GB memory cap and a 120 s timeout, the mutants that aborted under the
1 GB cap used for most of the main run. Appends to recheck.jsonl (restartable).

Usage: python3 recheck.py [--only MUTANT-ID] [config ...]     (default: min5)
"""
import json, os, sys
import tc, run

OUT = os.path.join(tc.HERE, "recheck.jsonl")

def main():
    a = sys.argv[1:]
    only = None
    if a and a[0] == "--only": only = a[1]; a = a[2:]
    cfgs = a or ["min5"]
    os.environ.pop("TCX_MEM_LIMIT_KB", None)
    last = {}
    for ln in open(run.RESULTS):
        r = json.loads(ln); last[(r["id"], r["config"])] = r
    ids = sorted({i for (i, c), r in last.items() if r["status"] != "ok"})
    done = set()
    if os.path.exists(OUT):
        for ln in open(OUT):
            r = json.loads(ln); done.add((r["id"], r["config"]))
    mutants = {m["id"]: m for m in run.load_mutants()}
    with open(OUT, "a") as out:
        for mid in ids:
            if only and mid != only: continue
            m = mutants[mid]
            try:
                prog, part = run.materialize(m)
                for c in cfgs:
                    if (mid, c) in done or last[(mid, c)]["status"] == "ok": continue
                    r = tc.run(prog, tc.CONFIGS[c], timeout=120)
                    row = {"id": mid, "config": c, "memcap_kb": 2500000}
                    row.update(tc.summarize(r, part))
                    out.write(json.dumps(row) + "\n"); out.flush()
                    print(mid, c, row["status"], row["exit"], row["wall"], flush=True)
            finally:
                if m["group"] == "stdlib": run.restore_stdlib()

if __name__ == "__main__":
    main()
