"""Permutes the top-level declarations of programs and compares the verdicts under NEW.

usage: permute.py N FILE...
For each program, writes up to N permutations (the reverse, the rotations, then random ones with a
fixed seed) in perm/ and runs each under NEW. Results go to permute.jsonl (restartable). Prints one
line per program: the number of permutations run and the set of verdicts."""
import hashlib, json, os, random, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import run, tcrun
OUT = os.path.join(HERE, "permute.jsonl")
def split(text):
    decls, cur = [], []
    for l in text.splitlines():
        if l.startswith("//") or not l.strip(): continue
        if not l[0].isspace() and l[0] != "}" and cur: decls.append(cur); cur = []
        cur.append(l)
    if cur: decls.append(cur)
    return ["\n".join(d) for d in decls]
def main():
    n = int(sys.argv[1]); done = {}
    if os.path.exists(OUT):
        for l in open(OUT): r = json.loads(l); done[r["sha"]] = r
    os.makedirs(os.path.join(HERE, "perm"), exist_ok=True)
    tcrun.CONFIGS["_"] = run.flags("NEW")
    for f in sys.argv[2:]:
        ds = split(open(f).read()); rng = random.Random(1); perms = [ds, ds[::-1]]
        for k in range(1, len(ds)): perms.append(ds[k:] + ds[:k])
        while len(perms) < n + len(ds):
            p = ds[:]; rng.shuffle(p); perms.append(p)
        seen, verdicts = set(), {}
        for p in perms:
            text = "\n".join(p) + "\n"
            sha = hashlib.sha1(text.encode()).hexdigest()[:12]
            if sha in seen or len(seen) >= n: continue
            seen.add(sha)
            if sha not in done:
                path = os.path.join(HERE, "perm", os.path.basename(f)[:-5] + "-" + sha + ".hylo")
                open(path, "w").write(text)
                x = tcrun.run(run.BIN, "_", path, 60)
                done[sha] = {"program": os.path.basename(f), "sha": sha, "file": os.path.relpath(path, HERE), "verdict": x["verdict"],
                             "errors": len(x["errors"]), "first": (x["errors"] or [""])[0], "stuck": x["counters"].get("premsubst.stuck", 0)}
                with open(OUT, "a") as o: o.write(json.dumps(done[sha]) + "\n")
            r = done[sha]
            verdicts.setdefault((r["verdict"], r["errors"]), []).append(r["file"])
        print(f"{os.path.basename(f)[:46]:46} {len(seen):3} permutations  " + "  ".join(f"{v}/{e} errors: {len(fs)}" for (v, e), fs in verdicts.items())
              + ("   <-- ORDER" if len({v for v, _ in verdicts}) > 1 else ""))
if __name__ == "__main__":
    main()
