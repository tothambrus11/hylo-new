"""Runs the attack programs under the configurations of the campaign.

usage: run.py [--all] [--configs A;B] FILE...
Results are appended to results.jsonl; a (program text, configuration) pair that is already
there is not run again. Exactly one tc-bench process runs at a time."""
import hashlib, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import tcrun
BIN = "eq22-554540c3a507"
NEW = tcrun.CONFIGS["NEW"]
def without(flag): return ",".join(x for x in NEW.split(",") if x != flag)
tcrun.CONFIGS["NEW-assocsubst"] = without("assocsubst")
tcrun.CONFIGS["NEW-abstractstrict"] = without("abstractstrict")
tcrun.CONFIGS["NEW-headsubst"] = without("headsubst")
tcrun.CONFIGS["NEW-premsubst"] = without("premsubst")
DEFAULT = ["base", "FULL", "NEW", "NEW+selfcheck", "NEW-assocsubst", "NEW-abstractstrict",
           "FULL+assocsubst", "FULL+abstractstrict"]
OUT = os.path.join(HERE, "results.jsonl")
def load():
    done = {}
    if os.path.exists(OUT):
        for l in open(OUT):
            r = json.loads(l); done[(r["sha"], r["config"])] = r
    return done
def main():
    a = sys.argv[1:]; configs = DEFAULT; quiet = False
    if "--configs" in a: i = a.index("--configs"); configs = a[i + 1].split(";"); del a[i:i + 2]
    if "--core" in a: a.remove("--core"); configs = ["base", "FULL", "NEW", "NEW+selfcheck"]
    done = load()
    for f in a:
        text = open(f).read(); sha = hashlib.sha1(text.encode()).hexdigest()[:12]
        for c in configs:
            r = done.get((sha, c))
            if r is None:
                x = tcrun.run(BIN, c, f)
                r = {"program": os.path.basename(f), "sha": sha, "config": c, "verdict": x["verdict"],
                     "errors": x["errors"], "violations": x["violations"]}
                open(OUT, "a").write(json.dumps(r) + "\n")
            msg = (r["violations"] or r["errors"] or [""])[0][:120]
            print(f"{os.path.basename(f)[:34]:34} {c[:20]:20} {r['verdict']:8} {('('+str(len(r['errors']))+') ') if r['errors'] else ''}{msg}")
main()
