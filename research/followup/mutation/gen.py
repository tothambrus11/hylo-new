"""Samples the mutants (fixed seed) and writes mutants.jsonl.

Strata: source group (tests, workloads, stdlib, corpus) x operator. Within a stratum the files are
visited round-robin in a shuffled order and one random unused site is taken from each file per pass,
until the quota is reached or the sites are exhausted. So no single large file dominates.
"""
import json, os, random, sys, collections, zlib
import tc, mutate, sources

SEED = 20261110
QUOTA = {"tests": 50, "workloads": 50, "stdlib": 50, "corpus": 40}
SLOW_MS = 8000        # sources whose unmutated typing time under base exceeds this are left out
STD_TYPES = ["Void", "Int", "Bool", "Int8", "UInt", "Float64"]

def load_baseline():
    by = collections.defaultdict(dict)
    for name in ("baseline.jsonl", "baseline-corpus.jsonl"):
        p = os.path.join(tc.HERE, name)
        if not os.path.exists(p): continue
        for ln in open(p):
            r = json.loads(ln); by[r["file"]][r["config"]] = r
    return by

def classify(d):
    """'valid' if every configuration accepts the program; otherwise None."""
    ok = {c: (x["status"] == "ok" and x["diags"] == 0) for c, x in d.items()}
    if len(ok) < 4: return None
    return "valid" if all(ok.values()) else None

def main():
    base = load_baseline()
    files = []          # (group, key, path)
    skipped = []
    for src, f in sources.sources() + sources.corpus():
        rel = os.path.relpath(f, tc.ROOT)
        if rel not in base: continue                    # no baseline yet (corpus not measured)
        cls = classify(base.get(rel, {}))
        if cls is None:
            skipped.append((rel, "not accepted by every configuration")); continue
        if (base[rel]["base"]["ms"] or 0) > SLOW_MS:
            skipped.append((rel, "slow")); continue
        group = {"tests": "tests", "corpus": "corpus"}.get(src, "workloads")
        files.append((group, rel, f))
    for rel in sources.stdlib_files():
        files.append(("stdlib", "stdlib:" + rel, os.path.join(tc.ORIG_STD, rel)))

    cells = collections.defaultdict(lambda: collections.defaultdict(list))   # (group, op) -> file -> sites
    for group, key, path in files:
        text = open(path).read()
        rng = random.Random(SEED ^ zlib.crc32(key.encode()))
        extra = STD_TYPES if group == "stdlib" else mutate.BUILTIN_TYPES
        for s in mutate.all_sites(text, rng, extra):
            cells[(group, s["op"])][key].append(s)

    mutants = []
    for (group, op) in sorted(cells):
        rng = random.Random(SEED ^ zlib.crc32((group + "/" + op).encode()))
        per_file = {k: list(v) for k, v in cells[(group, op)].items()}
        for v in per_file.values(): rng.shuffle(v)
        order = sorted(per_file); rng.shuffle(order)
        chosen = []
        while len(chosen) < QUOTA[group] and any(per_file.values()):
            for k in order:
                if per_file[k] and len(chosen) < QUOTA[group]:
                    chosen.append((k, per_file[k].pop()))
        for i, (k, s) in enumerate(chosen):
            m = {"id": f"{group}/{op}/{i:03d}", "group": group, "file": k}
            m.update(s)
            mutants.append(m)
    with open(os.path.join(tc.HERE, "mutants.jsonl"), "w") as out:
        for m in mutants: out.write(json.dumps(m) + "\n")
    with open(os.path.join(tc.HERE, "sources-skipped.json"), "w") as out:
        json.dump(skipped, out, indent=1)
    cnt = collections.Counter((m["group"], m["op"]) for m in mutants)
    avail = {k: sum(len(v) for v in d.values()) for k, d in cells.items()}
    nfiles = {k: len(d) for k, d in cells.items()}
    print(f'{"group":10} {"operator":16} {"chosen":>6} {"sites":>6} {"files":>6}')
    for k in sorted(avail): print(f"{k[0]:10} {k[1]:16} {cnt[k]:6} {avail[k]:6} {nfiles[k]:6}")
    print("total", len(mutants), "skipped sources:", skipped)

if __name__ == "__main__":
    main()
