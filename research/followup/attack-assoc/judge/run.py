"""Judge's runner: type-checks programs under the configurations used to judge the attack on assoc.

usage: run.py [--bin BINID] [--configs A;B] FILE...
Results are appended to results.jsonl; a (binary, program text, configuration) triple already there
is not run again. Exactly one tc-bench process runs at a time, under the timeout of tcrun (60 s).

NEW22 is the NEW of BRIEF2.md (the configuration that was attacked); NEW is tcrun's current NEW."""
import hashlib, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
import tcrun
FULL = tcrun.CONFIGS["FULL"]
tcrun.CONFIGS["NEW22"] = FULL + ",sigrounds,assocsubst,eqindex,eqeager,premsubst,headsubst,abstractstrict"
for base in ("NEW", "NEW22"):
    for flag in ("assocsubst", "abstractstrict", "headsubst", "premsubst"):
        tcrun.CONFIGS[base + "-" + flag] = ",".join(x for x in tcrun.CONFIGS[base].split(",") if x != flag)
OUT = os.path.join(HERE, "results.jsonl")
def load():
    done = {}
    if os.path.exists(OUT):
        for l in open(OUT):
            r = json.loads(l); done[(r["bin"], r["sha"], r["config"])] = r
    return done
def main():
    a = sys.argv[1:]; binid = "eq22-554540c3a507"
    configs = ["base", "FULL", "NEW22", "NEW22+selfcheck"]
    if "--bin" in a: i = a.index("--bin"); binid = a[i + 1]; del a[i:i + 2]
    if "--configs" in a: i = a.index("--configs"); configs = a[i + 1].split(";"); del a[i:i + 2]
    done = load()
    for f in a:
        text = open(f).read(); sha = hashlib.sha1(text.encode()).hexdigest()[:12]
        for c in configs:
            r = done.get((binid, sha, c))
            if r is None:
                x = tcrun.run(binid, c, f)
                r = {"bin": binid, "program": os.path.basename(f), "sha": sha, "config": c, "verdict": x["verdict"],
                     "errors": x["errors"], "violations": x["violations"]}
                open(OUT, "a").write(json.dumps(r) + "\n")
            msg = (r["violations"] or r["errors"] or [""])[0][:120]
            n = ("(%d) " % len(r["errors"])) if r["errors"] else ""
            print(f"{binid[:4]} {os.path.basename(f)[:36]:36} {c[:22]:22} {r['verdict']:8} {n}{msg}")
main()
