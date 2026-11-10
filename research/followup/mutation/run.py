"""Runs every mutant under every configuration. Restartable: appends to results.jsonl and skips
the (mutant, configuration) pairs already there. One tc-bench process at a time.

Standard-library mutants are applied to the private copy of the library in bin/, which is restored
after each mutant (and checked against the original when the runner starts).

Usage: python3 run.py [--limit N] [--only ID-prefix]
"""
import filecmp, json, os, random, shutil, signal, sys
import tc, mutate, sources

RESULTS = os.path.join(tc.HERE, "results.jsonl")
WORK = os.path.join(tc.HERE, "work")
TIMEOUT = 120

def restore_stdlib():
    """Makes the private copy of the standard library identical to the original."""
    n = 0
    for rel in sources.stdlib_files():
        a, b = os.path.join(tc.ORIG_STD, rel), os.path.join(tc.STD, rel)
        if not os.path.exists(b) or not filecmp.cmp(a, b, shallow=False):
            shutil.copyfile(a, b); n += 1
    return n

def source_path(m):
    if m["group"] == "stdlib":
        return os.path.join(tc.ORIG_STD, m["file"][len("stdlib:"):])
    return os.path.join(tc.ROOT, m["file"])

def materialize(m):
    """Applies the mutant; returns (program to check, part of the counters to read)."""
    text = open(source_path(m)).read()
    assert text[m["start"]:m["end"]][:120] == m["orig"], "source changed since the mutants were generated"
    mutated = mutate.apply(text, m)
    if m["group"] == "stdlib":
        with open(os.path.join(tc.STD, m["file"][len("stdlib:"):]), "w") as f: f.write(mutated)
        return tc.EMPTY, "stdlib"
    os.makedirs(WORK, exist_ok=True)
    p = os.path.join(WORK, "mutant.hylo")
    with open(p, "w") as f: f.write(mutated)
    return p, "user"

def load_mutants():
    return [json.loads(l) for l in open(os.path.join(tc.HERE, "mutants.jsonl"))]

def main():
    limit = None; only = None
    a = sys.argv[1:]
    while a:
        x = a.pop(0)
        if x == "--limit": limit = int(a.pop(0))
        elif x == "--only": only = a.pop(0)
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(1))
    if restore_stdlib(): print("restored the standard library copy", flush=True)
    mutants = load_mutants()
    random.Random(7).shuffle(mutants)       # so that a partial run is an unbiased sample
    if only: mutants = [m for m in mutants if m["id"].startswith(only)]
    done = set()
    if os.path.exists(RESULTS):
        for ln in open(RESULTS):
            r = json.loads(ln)
            if "all" in r: done.add((r["id"], r["config"]))     # early rows lack the full counters: redone
    n = 0
    with open(RESULTS, "a") as out:
        for m in mutants:
            todo = [c for c in tc.CONFIGS if (m["id"], c) not in done]
            if not todo: continue
            if limit is not None and n >= limit: break
            n += 1
            try:
                prog, part = materialize(m)
                for c in todo:
                    r = tc.run(prog, tc.CONFIGS[c], timeout=TIMEOUT)
                    row = {"id": m["id"], "config": c}
                    row.update(tc.summarize(r, part))
                    out.write(json.dumps(row) + "\n"); out.flush()
                    print(m["id"], c, row["status"], row["diags"], row["matches"], row["ms"], flush=True)
            finally:
                if m["group"] == "stdlib": restore_stdlib()

if __name__ == "__main__":
    main()
