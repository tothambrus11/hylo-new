#!/usr/bin/env python3
"""Type-checks permutations of the top-level declarations of programs with ../sigrounds/orders.py
(binary eq22) and prints, per (program, configuration), the distinct outcomes with their counts.

usage: ord.py [--max N] [--fix K] [--configs A,B] FILE...
Raw results are appended to orders.jsonl (restartable; a program whose text changed is run again
under a key that includes a hash of its text). Configurations: FULL, NEW, optionally +flag."""
import hashlib, json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
NEW = "FULL+sigrounds+assocsubst+eqindex+eqeager+premsubst+headsubst+abstractstrict"
def main():
    a = sys.argv[1:]; extra = []; configs = "NEW"
    for opt in ("--max", "--fix"):
        if opt in a: i = a.index(opt); extra += a[i:i + 2]; del a[i:i + 2]
    if "--configs" in a: i = a.index("--configs"); configs = a[i + 1]; del a[i:i + 2]
    out = os.path.join(HERE, "orders.jsonl")
    cs = ",".join(c.replace("NEW", NEW) for c in configs.split(","))
    env = dict(os.environ, TCB="/home/user/hylo-new/research/exp/bin/eq22-554540c3a507/tc-bench")
    # orders.py keys its restart on the path, so run on a copy named after the content hash.
    os.makedirs(os.path.join(HERE, "scratch", "ord"), exist_ok=True)
    for f in a:
        h = hashlib.sha1(open(f, "rb").read() + " ".join(extra).encode()).hexdigest()[:8]
        copy = os.path.join(HERE, "scratch", "ord", os.path.basename(f)[:-5] + "." + h + ".hylo")
        open(copy, "w").write(open(f).read())
        subprocess.run([sys.executable, os.path.join(HERE, "..", "sigrounds", "orders.py"), out, cs] + extra + [copy], env=env, check=True)
        for l in open(out):
            r = json.loads(l)
            if r["file"] != copy: continue
            c = r["config"].replace(NEW, "NEW")
            if not r.get("split"): print(f"{os.path.basename(f)} {c}: not split"); continue
            print(f"{os.path.basename(f)} {c}: {r['decls']} declarations ({r['fixed']} fixed), {r['perms']} orders, {len(r['outcomes'])} outcome(s)")
            for o in r["outcomes"]:
                print(f"    {o['n']:4} x {o['outcome']:7} example order {o['example']}  {'; '.join(e[:90] for e in o['errors'][:3])}")
if __name__ == "__main__":
    main()
