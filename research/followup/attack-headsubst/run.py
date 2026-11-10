"""Runs programs under several configurations, one tc-bench process at a time, and appends
one JSON line per (binary, program, configuration) to results.jsonl. Restartable: a triple
already in results.jsonl whose program has not changed is not run again.

usage: run.py [--bin BINID] [--configs "A;B;C"] [--force] [--counters] FILE..."""
import hashlib, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import tcrun
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results.jsonl")
BIN = "eq34-6718f1de213f"
CONFIGS = "base;FULL;NEW;NEW+selfcheck;NEW-headsubst;FULL+headsubst"

_flags = tcrun.flags
def flags(config):
    """Like tcrun.flags, with NAME-flag to remove a flag."""
    minus = config.split("-")
    fs = _flags(minus[0]).split(",")
    return ",".join(f for f in fs if f and f not in minus[1:])

def run(binid, config, path):
    saved = tcrun.flags
    tcrun.flags = flags
    try: return tcrun.run(binid, config, path, 60)
    finally: tcrun.flags = saved

def main():
    a = sys.argv[1:]; binid, configs, force, counters = BIN, CONFIGS, False, False
    if "--bin" in a: i = a.index("--bin"); binid = a[i + 1]; del a[i:i + 2]
    if "--configs" in a: i = a.index("--configs"); configs = a[i + 1]; del a[i:i + 2]
    if "--force" in a: a.remove("--force"); force = True
    if "--counters" in a: a.remove("--counters"); counters = True
    done = {}
    if os.path.exists(OUT):
        for l in open(OUT):
            r = json.loads(l); done[(r["bin"], r["program"], r["config"], r["sha"])] = r
    for f in a:
        rel = os.path.relpath(os.path.abspath(f), HERE)
        sha = hashlib.sha1(open(f, "rb").read()).hexdigest()[:12]
        for c in configs.split(";"):
            r = None if force else done.get((binid, rel, c, sha))
            if r is None:
                x = run(binid, c, f)
                r = {"bin": binid, "program": rel, "config": c, "sha": sha, "verdict": x["verdict"],
                     "errors": x["errors"], "violations": x["violations"],
                     "counters": {k: v for k, v in x["counters"].items() if k.startswith(("headsubst", "selfcheck", "premsubst", "summon.depth", "summon.budget"))}}
                with open(OUT, "a") as o: o.write(json.dumps(r) + "\n"); o.flush(); os.fsync(o.fileno())
            cs = " ".join(f"{k.replace('headsubst.', 'h.')}={v}" for k, v in r["counters"].items() if k.startswith("headsubst")) if counters else ""
            msg = (r["violations"] or r["errors"] or [""])[0][:100]
            print(f"{os.path.basename(f)[:40]:40} {c[:16]:16} {r['verdict']:8} {len(r['errors'])} {cs} {msg}")
main()
