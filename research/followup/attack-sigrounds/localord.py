#!/usr/bin/env python3
"""Type-checks permutations of the declarations written in function bodies, one process at a time.

usage: localord.py [--max N] [--configs A;B] FILE...

The permuted lines are those that start with two spaces followed by `given`, `extension` or `type`
(one-line declarations of a function body). Lines are only exchanged inside a block of consecutive
such lines, so a declaration never moves to another function. All combinations if there are at
most N (default 24), otherwise the source order, its reverse and N-2 random ones (fixed seed). Appends one JSON line per (file, config) to localorders.jsonl and
prints the distinct outcomes (verdict and sorted messages without positions) with their counts."""
import hashlib, itertools, json, math, os, random, re, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import tcrun
BIN = "eq22-554540c3a507"
def main():
    a = sys.argv[1:]; nmax = 24; configs = "NEW;FULL"
    if "--max" in a: i = a.index("--max"); nmax = int(a[i + 1]); del a[i:i + 2]
    if "--configs" in a: i = a.index("--configs"); configs = a[i + 1]; del a[i:i + 2]
    out = open(os.path.join(HERE, "localorders.jsonl"), "a")
    for f in a:
        lines = open(f).read().split("\n")
        idx = [i for i, l in enumerate(lines) if re.match(r"  (given|extension|type) ", l)]
        k = len(idx)
        blocks = []
        for i in idx:
            if blocks and blocks[-1][-1] == i - 1: blocks[-1].append(i)
            else: blocks.append([i])
        def combine(ps): return tuple(idx.index(b[j]) for b, p in zip(blocks, ps) for j in p)
        total = math.prod(math.factorial(len(b)) for b in blocks)
        if total <= nmax:
            perms = [combine(ps) for ps in itertools.product(*[itertools.permutations(range(len(b))) for b in blocks])]
        else:
            rng = random.Random(int(hashlib.sha1(os.path.basename(f).encode()).hexdigest()[:8], 16))
            perms = [tuple(range(k)), combine([tuple(reversed(range(len(b)))) for b in blocks])]
            while len(perms) < nmax:
                ps = []
                for b in blocks: p = list(range(len(b))); rng.shuffle(p); ps.append(p)
                perms.append(combine(ps))
        for c in configs.split(";"):
            seen = {}
            for p in perms:
                ls = list(lines)
                for pos, src in zip(idx, p): ls[pos] = lines[idx[src]]
                with tempfile.NamedTemporaryFile("w", suffix=".hylo", delete=False, dir=os.path.join(HERE, "scratch")) as t:
                    t.write("\n".join(ls)); path = t.name
                r = tcrun.run(BIN, c, path); os.unlink(path)
                key = json.dumps([r["verdict"], sorted(r["errors"]), r["violations"]])
                e = seen.setdefault(key, {"verdict": r["verdict"], "errors": sorted(r["errors"]), "violations": r["violations"], "n": 0, "example": list(p)})
                e["n"] += 1
            out.write(json.dumps({"file": os.path.relpath(f, HERE), "config": c, "decls": k, "perms": len(perms), "outcomes": list(seen.values())}) + "\n"); out.flush()
            print(f"{os.path.basename(f)} {c}: {k} local declarations, {len(perms)} orders, {len(seen)} outcome(s)")
            for e in seen.values():
                print(f"    {e['n']:4} x {e['verdict']:7} example {e['example']}  {'; '.join(x[:80] for x in (e['violations'] + e['errors'])[:2])}")
if __name__ == "__main__":
    main()
