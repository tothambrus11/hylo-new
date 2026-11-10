"""Permutes the top-level declarations of programs and compares the verdicts under NEW.

usage: permute.py N FILE...
For each program, writes up to N permutations (reverse, rotations, random with a fixed seed) in
perm/ and runs each under NEW. Results go to permute.jsonl (restartable). Prints the programs with
more than one verdict (number of errors included)."""
import hashlib, json, os, random, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import tcrun
BIN = "eq22-554540c3a507"; OUT = os.path.join(HERE, "permute.jsonl")
def split(text):
    decls, cur = [], []
    for l in text.splitlines():
        if l.startswith("//"): continue
        if l and not l[0].isspace() and l[0] != "}" and cur: decls.append(cur); cur = []
        cur.append(l)
    if cur: decls.append(cur)
    return ["\n".join(d) for d in decls]
def main():
    n = int(sys.argv[1]); done = {}
    if os.path.exists(OUT):
        for l in open(OUT): r = json.loads(l); done[r["sha"]] = r
    os.makedirs(os.path.join(HERE, "perm"), exist_ok=True)
    for f in sys.argv[2:]:
        ds = split(open(f).read()); rng = random.Random(1); perms = [ds, ds[::-1]]
        for k in range(1, len(ds)): perms.append(ds[k:] + ds[:k])
        while len(perms) < n + len(ds):
            p = ds[:]; rng.shuffle(p); perms.append(p)
        seen, verdicts = set(), {}
        for p in perms:
            text = "\n".join(p) + "\n"; sha = hashlib.sha1(text.encode()).hexdigest()[:12]
            if sha in seen or len(seen) >= n: continue
            seen.add(sha)
            r = done.get(sha)
            if r is None:
                path = os.path.join(HERE, "perm", os.path.basename(f)[:-5] + "." + sha + ".hylo")
                open(path, "w").write(text)
                x = tcrun.run(BIN, "NEW", path)
                r = {"program": os.path.basename(f), "sha": sha, "file": os.path.basename(path),
                     "verdict": x["verdict"], "errors": x["errors"]}
                open(OUT, "a").write(json.dumps(r) + "\n")
            verdicts.setdefault((r["verdict"], len(r["errors"])), []).append(r["file"])
        s = "; ".join(f"{v} ({e} errors) x{len(fs)}" for (v, e), fs in verdicts.items())
        print(f"{os.path.basename(f):40} {len(seen):3} permutations: {s}" + ("   <== DIFFERENT" if len(verdicts) > 1 else ""))
        if len(verdicts) > 1:
            for k, fs in verdicts.items(): print("     ", k, fs[0])
main()
