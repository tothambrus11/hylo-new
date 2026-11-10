#!/usr/bin/env python3
"""Judge's runner: type-checks programs under the configurations used to judge the attack on sigrounds.

usage: run.py [--bin BINID] [--configs "A;B"] [--full] FILE...
Results are appended to results.jsonl; a (binary, program text, configuration) triple already there
is not run again. Exactly one tc-bench process runs at a time, under the timeout of tcrun (60 s).

NEW22 is the NEW of BRIEF2.md (the configuration that was attacked, binary eq22); NEW is tcrun's
current NEW (binary eq38, the sources now in /home/user/hylo-impl). NOSIG and NOSIG22 are these
without sigrounds; FULL+sigrounds is FULL with the single flag. --full prints every diagnostic."""
import hashlib, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
import tcrun
FULL = tcrun.CONFIGS["FULL"]
tcrun.CONFIGS["NEW22"] = FULL + ",sigrounds,assocsubst,eqindex,eqeager,premsubst,headsubst,abstractstrict"
tcrun.CONFIGS["NOSIG22"] = tcrun.CONFIGS["NEW22"].replace(",sigrounds", "")
tcrun.CONFIGS["NOSIG"] = tcrun.CONFIGS["NEW"].replace(",sigrounds", "")
for base in ("NEW", "NEW22"):
    for flag in ("hidecache", "extorder", "givencheck", "memberskip", "index", "absmodel"):
        tcrun.CONFIGS[base + "-" + flag] = ",".join(x for x in tcrun.CONFIGS[base].split(",") if x != flag)
OUT = os.path.join(HERE, "results.jsonl")
DEFAULT = {"eq22-554540c3a507": "base;FULL;FULL+sigrounds;NOSIG22;NEW22;NEW22+selfcheck",
           "eq38-893592cba1a5": "FULL;NOSIG;NEW;NEW+selfcheck"}
def load():
    done = {}
    if os.path.exists(OUT):
        for l in open(OUT):
            r = json.loads(l); done[(r["bin"], r["sha"], r["config"])] = r
    return done
def main():
    a = sys.argv[1:]; bins = list(DEFAULT); configs = None; full = False
    if "--bin" in a: i = a.index("--bin"); bins = [b for b in DEFAULT if b.startswith(a[i + 1])] or [a[i + 1]]; del a[i:i + 2]
    if "--configs" in a: i = a.index("--configs"); configs = a[i + 1]; del a[i:i + 2]
    if "--full" in a: a.remove("--full"); full = True
    done = load()
    for f in a:
        text = open(f).read(); sha = hashlib.sha1(text.encode()).hexdigest()[:12]
        for binid in bins:
            for c in (configs or DEFAULT[binid]).split(";"):
                r = done.get((binid, sha, c))
                if r is None:
                    x = tcrun.run(binid, c, f)
                    r = {"bin": binid, "program": os.path.basename(f), "sha": sha, "config": c, "verdict": x["verdict"],
                         "errors": x["errors"], "violations": x["violations"],
                         "counters": {k: v for k, v in x["counters"].items() if k.startswith(("sigrounds", "summon.calls", "summon.matches", "summon.cacheHits", "names.appliesCalls"))}}
                    open(OUT, "a").write(json.dumps(r) + "\n"); done[(binid, sha, c)] = r
                cs = " ".join(f"{k.split('.')[1]}={v}" for k, v in r["counters"].items() if k.startswith("sigrounds"))
                msgs = ["VIOLATION " + v for v in r["violations"]] + r["errors"]
                n = ("[%d] " % len(r["errors"])) if r["errors"] else ""
                print(f"{os.path.basename(f)[:34]:34} {binid[:4]} {c[:17]:17} {r['verdict']:9} {cs:30} {n}{(msgs + [''])[0][:100]}")
                if full:
                    for m in msgs[1:]: print(" " * 70 + m[:140])
if __name__ == "__main__":
    main()
