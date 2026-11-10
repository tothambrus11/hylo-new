"""Runs every mutant and every unmutated source under FULL without absmodel,absquotient, so that the
effect of the abstract model can be read with the equality fixes in place (FULL versus FULL minus the
model), not only on top of MIN5. Appends to fullnoabs.jsonl; restartable; one tc-bench process at a time.

Rows: {"kind": "source", "file": ...} for an unmutated source, {"kind": "mutant", "id": ...} for a mutant.
"""
import json, os, sys
import tc, run

OUT = os.path.join(tc.HERE, "fullnoabs.jsonl")
FLAGS = ",".join(f for f in tc.FULL.split(",") if f not in ("absmodel", "absquotient"))

def main():
    done = set()
    if os.path.exists(OUT):
        for ln in open(OUT):
            r = json.loads(ln); done.add((r["kind"], r.get("id") or r.get("file")))
    mutants = run.load_mutants()
    os.environ.pop("TCX_MEM_LIMIT_KB", None)
    run.restore_stdlib()
    with open(OUT, "a") as out:
        files = ["<stdlib>"] + sorted({m["file"] for m in mutants if m["group"] != "stdlib"})
        for f in files:
            if ("source", f) in done: continue
            r = tc.run(tc.EMPTY if f == "<stdlib>" else os.path.join(tc.ROOT, f), FLAGS, timeout=60)
            row = {"kind": "source", "file": f, "config": "full-abs"}
            row.update(tc.summarize(r, "stdlib" if f == "<stdlib>" else "user"))
            out.write(json.dumps(row) + "\n"); out.flush()
        for m in mutants:
            if ("mutant", m["id"]) in done: continue
            try:
                prog, part = run.materialize(m)
                r = tc.run(prog, FLAGS, timeout=60)
                row = {"kind": "mutant", "id": m["id"], "config": "full-abs"}
                row.update(tc.summarize(r, part))
                out.write(json.dumps(row) + "\n"); out.flush()
                print(m["id"], row["status"], row["diags"], row["matches"], row["ms"], flush=True)
            finally:
                if m["group"] == "stdlib": run.restore_stdlib()

if __name__ == "__main__":
    main()
