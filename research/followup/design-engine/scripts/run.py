#!/usr/bin/env python3
"""Runs tc-bench on Hylo programs under named configurations, one process at a time.

Usage:
  run.py [--trace] [--configs base,FULL] [--depth N] [--out results.jsonl] FILE.hylo...

For each (program, configuration, depth) triple, appends one JSON line to the output file with the
verdict, the first diagnostic and the user-module counters, and prints a one-line summary. Triples
already in the output file are skipped unless --force is given, so the script is restartable.
With --trace nothing is recorded; the trace lines of the user module are printed instead.
"""
import argparse, json, os, re, subprocess, sys

B = "/home/user/hylo-new/research/exp/bin/eq9-723cc0e6b0f8/tc-bench"
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCK = os.path.join(HERE, "experiments", ".lock")
FIX = "occurs,fixsubst,eqsolve,extorder,arrowenv,eqmgu,givencheck,budget"
OPT = "symindex,coesrc,traitindex,memberskip,unify,index,absmodel,absquotient,typevec,reifymemo"
CONFIGS = {
    "base": "",
    "FIX": FIX,
    "FULL": FIX + "," + OPT,
    "MIN5": "index,memberskip,typevec,symindex,traitindex",
    # FULL without the equality procedure: premises are proved by search only.
    "FULL-eqsolve": FIX.replace("eqsolve,", "") + "," + OPT,
    # FULL without the abstract model: failing goals are searched to the bound.
    "FULL-absmodel": FIX + "," + OPT.replace("absmodel,absquotient,", ""),
}
KEYS = [
    "summon.calls", "summon.cacheHits", "summon.subgoals", "summon.matches", "summon.matchOK",
    "summon.layers", "summon.depthExhausted", "summon.budgetExhausted", "coerced.slowPath",
    "eqsolve.proved", "eqsolve.refuted", "eqsolve.untrusted", "eqsolve.premises", "eqmgu.solved",
    "absmodel.refuted", "index.skipped", "index.fallback",
]


def run(path, config, depth=None, trace=False, timeout=60):
    flags = CONFIGS[config]
    if trace:
        flags = (flags + ",trace") if flags else "trace"
    env = dict(os.environ, HYLO_TC_EXPERIMENTS=flags)
    if depth is not None:
        env["HYLO_TC_MAXDEPTH"] = str(depth)
    # The lock serializes every tc-bench process started by the scripts of this directory.
    p = subprocess.run(
        ["flock", LOCK, "timeout", str(timeout), B, "--count", path], env=env,
        capture_output=True, text=True, errors="replace")
    out = p.stdout + p.stderr
    r = {"program": os.path.relpath(path, HERE), "config": config, "depth": depth or 10,
         "exit": p.returncode}
    if p.returncode == 124:
        r["verdict"] = "timeout"
    elif p.returncode != 0 and "diagnostics:" not in out:
        r["verdict"] = "crash(%d)" % p.returncode
    else:
        m = re.search(r"diagnostics: (\d+)", out)
        n = int(m.group(1)) if m else -1
        r["verdict"] = "accepted" if n == 0 else "rejected"
        r["diagnostics"] = n
        errs = [l for l in out.splitlines() if "error:" in l]
        r["first_error"] = errs[0].split("error:", 1)[1].strip() if errs else ""
        if any(("expected" in e and "cannot" not in e) or "is not a valid identifier" in e
               for e in errs):
            r["verdict"] = "SYNTAX?"
    m = re.search(r"counters\.user: (.*)", out)
    cs = dict(kv.split("=") for kv in m.group(1).split()) if m else {}
    r["counters"] = {k: int(cs[k]) for k in KEYS if k in cs}
    if trace:
        r["_trace"] = [l for l in out.splitlines() if l.startswith("[trace]")]
    return r


_STDLIB = {}


def stdlib_trace_lines(config, depth):
    """Returns the number of trace lines printed while typing the standard library."""
    k = (config, depth)
    if k not in _STDLIB:
        e = os.path.join(HERE, "experiments", "empty.hylo")
        _STDLIB[k] = len(run(e, config, depth, trace=True)["_trace"])
    return _STDLIB[k]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--configs", default="base,FULL")
    ap.add_argument("--depth", type=int, default=None)
    ap.add_argument("--out", default=os.path.join(HERE, "results.jsonl"))
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--timeout", type=int, default=60)
    ap.add_argument("--width", type=int, default=600)
    a = ap.parse_args()
    done = set()
    if os.path.exists(a.out) and not a.force and not a.trace:
        for l in open(a.out):
            try:
                j = json.loads(l)
                done.add((j["program"], j["config"], j["depth"]))
            except Exception:
                pass
    for f in a.files:
        f = os.path.abspath(f)
        rel = os.path.relpath(f, HERE)
        for c in a.configs.split(","):
            if (rel, c, a.depth or 10) in done:
                continue
            r = run(f, c, a.depth, trace=a.trace, timeout=a.timeout)
            t = r.pop("_trace", None)
            if t is not None:
                t = "\n".join(l[:a.width] for l in t[stdlib_trace_lines(c, a.depth):])
            else:
                with open(a.out, "a") as o:
                    o.write(json.dumps(r) + "\n")
            cs = r.get("counters", {})
            brief = " ".join(
                "%s=%s" % (k.split(".", 1)[1], v) for k, v in cs.items()
                if k in ("summon.calls", "summon.subgoals", "summon.matches", "summon.layers",
                         "summon.depthExhausted", "eqsolve.proved", "absmodel.refuted"))
            print("%-40s %-13s d=%-3s %-9s %s | %s" % (
                os.path.basename(f), c, r["depth"], r["verdict"], brief,
                r.get("first_error", "")[:100]))
            if t:
                print(t)
            sys.stdout.flush()


if __name__ == "__main__":
    main()
