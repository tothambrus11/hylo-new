#!/usr/bin/env python3
"""Runs tc-bench on Hylo programs under named configurations, one process at a time.

Usage:
  run.py [--trace] [--configs base,FULL] [--out results.jsonl] FILE.hylo...

For each (program, configuration) pair, appends one JSON line to the output file with the verdict,
the first diagnostic and the user-module counters, and prints a one-line summary. Pairs already in
the output file are skipped unless --force is given, so the script is restartable.
"""
import argparse, json, os, re, subprocess, sys

B = "/home/user/hylo-new/research/exp/bin/eq9-723cc0e6b0f8/tc-bench"
FIX = "occurs,fixsubst,eqsolve,extorder,arrowenv,eqmgu,givencheck,budget"
CONFIGS = {
    "base": "",
    "FIX": FIX,
    "FULL": FIX + ",symindex,coesrc,traitindex,memberskip,unify,index,absmodel,absquotient,typevec,reifymemo",
    # FULL without one equality mechanism at a time.
    "FULL-eqsolve": "occurs,fixsubst,extorder,arrowenv,eqmgu,givencheck,budget,symindex,coesrc,traitindex,memberskip,unify,index,absmodel,absquotient,typevec,reifymemo",
    "FULL-eqmgu": "occurs,fixsubst,eqsolve,extorder,arrowenv,givencheck,budget,symindex,coesrc,traitindex,memberskip,unify,index,absmodel,absquotient,typevec,reifymemo",
    "FULL-absquotient": FIX + ",symindex,coesrc,traitindex,memberskip,unify,index,absmodel,typevec,reifymemo",
}
KEYS = [
    "summon.calls", "summon.subgoals", "summon.matches", "summon.layers", "summon.depthExhausted",
    "summon.budgetExhausted", "coerced.slowPath", "eqsolve.proved", "eqsolve.refuted",
    "eqsolve.untrusted", "eqsolve.premises", "eqsolve.abstractBindings", "eqmgu.solved",
    "absmodel.refuted", "absmodel.quotient", "absmodel.inconclusive", "index.skipped",
    "index.fallback", "names.appliesCalls",
]


def run(path, config, trace=False, timeout=60):
    flags = CONFIGS[config]
    if trace:
        flags = (flags + ",trace") if flags else "trace"
    env = dict(os.environ, HYLO_TC_EXPERIMENTS=flags)
    try:
        p = subprocess.run(
            ["timeout", str(timeout), B, "--count", path], env=env, capture_output=True, text=True)
    except Exception as e:  # pragma: no cover
        return {"program": path, "config": config, "verdict": "error", "error": str(e)}
    out = p.stdout + p.stderr
    r = {"program": os.path.relpath(path, os.path.dirname(__file__)), "config": config,
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
        if any(("expected" in e and "cannot" not in e) or "is not a valid identifier" in e for e in errs):
            r["verdict"] = "SYNTAX?"
    m = re.search(r"counters\.user: (.*)", out)
    cs = dict(kv.split("=") for kv in m.group(1).split()) if m else {}
    r["counters"] = {k: int(cs[k]) for k in KEYS if k in cs}
    m = re.search(r"type\.user[^0-9]*([0-9.]+)", out)
    if m:
        r["type_user_ms"] = float(m.group(1))
    if trace:
        ls = [l for l in out.splitlines() if l.startswith("[trace]")]
        r["_trace_lines"] = len(ls)
        r["_trace"] = ls
    return r


_STDLIB_TRACE = {}


def stdlib_trace_lines(config):
    """Returns the number of trace lines printed while typing the standard library."""
    if config not in _STDLIB_TRACE:
        e = os.path.join(os.path.dirname(__file__), "experiments", "empty.hylo")
        _STDLIB_TRACE[config] = run(e, config, trace=True)["_trace_lines"]
    return _STDLIB_TRACE[config]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--configs", default="base,FULL")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "results.jsonl"))
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--timeout", type=int, default=60)
    ap.add_argument("--width", type=int, default=400)
    a = ap.parse_args()
    done = set()
    if os.path.exists(a.out) and not a.force and not a.trace:
        for l in open(a.out):
            try:
                j = json.loads(l)
                done.add((j["program"], j["config"]))
            except Exception:
                pass
    for f in a.files:
        f = os.path.abspath(f)
        rel = os.path.relpath(f, os.path.dirname(__file__))
        for c in a.configs.split(","):
            if (rel, c) in done:
                continue
            r = run(f, c, trace=a.trace, timeout=a.timeout)
            t = r.pop("_trace", None)
            r.pop("_trace_lines", None)
            if t is not None:
                t = "\n".join(l[:a.width] for l in t[stdlib_trace_lines(c):])
            if not a.trace:
                with open(a.out, "a") as o:
                    o.write(json.dumps(r) + "\n")
            cs = r.get("counters", {})
            brief = " ".join(
                "%s=%s" % (k.split(".", 1)[0][:3] + "." + k.split(".", 1)[1], v) for k, v in cs.items()
                if k in ("summon.subgoals", "summon.matches", "summon.depthExhausted", "eqsolve.proved",
                         "eqsolve.refuted", "eqsolve.untrusted", "eqmgu.solved", "coerced.slowPath"))
            print("%-44s %-16s %-9s %s | %s" % (
                os.path.basename(f), c, r["verdict"], brief, r.get("first_error", "")[:110]))
            if t:
                print(t)
            sys.stdout.flush()


if __name__ == "__main__":
    main()
