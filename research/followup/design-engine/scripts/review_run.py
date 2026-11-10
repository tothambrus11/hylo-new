#!/usr/bin/env python3
"""Runs programs on a chosen tc-bench binary under chosen flag sets (used by the design review).

Usage:
  review_run.py [--bin eq25-c7cbd846a05c] [--configs FULL,FULL+premsubst] [--out FILE.jsonl]
                [--trace] [--selfcheck] [--depth N] [--force] FILE.hylo...

A configuration is a name of run.py (base, FIX, FULL, MIN5) optionally followed by +flag+flag.
One tc-bench process at a time (the lock of run.py). Results already in the output are skipped.
With --trace nothing is recorded; the trace of the user module is printed.
"""
import argparse, json, os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run as R

BIN = "/home/user/hylo-new/research/exp/bin/%s/tc-bench"
KEYS = R.KEYS + ["premsubst.binders", "premsubst.bound", "premsubst.deferred",
                 "premsubst.released", "premsubst.normalized", "premsubst.stuck"]


# NEW is the configuration of ../BRIEF2.md: FULL plus the mechanisms of the follow-up.
CONFIGS = dict(R.CONFIGS, NEW=R.CONFIGS["FULL"]
               + ",sigrounds,assocsubst,eqindex,eqeager,premsubst,headsubst,abstractstrict")


def flags(config):
    parts = config.split("+")
    return ",".join(x for x in [CONFIGS.get(parts[0], parts[0])] + parts[1:] if x)


def run(binid, path, config, depth=None, trace=False, timeout=60):
    env = dict(os.environ, HYLO_TC_EXPERIMENTS=flags(config) + (",trace" if trace else ""))
    if depth is not None:
        env["HYLO_TC_MAXDEPTH"] = str(depth)
    p = subprocess.run(["flock", R.LOCK, "timeout", str(timeout), BIN % binid, "--count", path],
                       env=env, capture_output=True, text=True, errors="replace")
    out = p.stdout + p.stderr
    r = {"program": os.path.relpath(path, R.HERE), "bin": binid, "config": config,
         "depth": depth or 10, "exit": p.returncode}
    m = re.search(r"diagnostics: (\d+)", out)
    if p.returncode == 124:
        r["verdict"] = "timeout"
    elif p.returncode != 0 or not m:
        r["verdict"] = "crash(%d)" % p.returncode
    else:
        r["verdict"] = "accepted" if m.group(1) == "0" else "rejected"
        errs = [l for l in out.splitlines() if "error:" in l]
        r["errors"] = [e.split("error:", 1)[1].strip() for e in errs]
        if any(("expected" in e and "cannot" not in e) or "is not a valid identifier" in e
               for e in errs):
            r["verdict"] = "SYNTAX?"
    m = re.search(r"counters\.user: (.*)", out)
    cs = dict(kv.split("=") for kv in m.group(1).split()) if m else {}
    r["counters"] = {k: int(cs[k]) for k in KEYS if k in cs}
    r["violations"] = sorted(set(re.findall(r"\[selfcheck\] VIOLATION: (.*)", out)))
    if trace:
        r["_trace"] = [l for l in out.splitlines() if l.startswith("[trace]")]
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--bin", default="eq25-c7cbd846a05c")
    ap.add_argument("--configs", default="FULL,FULL+premsubst")
    ap.add_argument("--out", default=os.path.join(R.HERE, "review", "results.jsonl"))
    ap.add_argument("--depth", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--tail", type=int, default=40, help="trace lines printed (from the end)")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()
    done = set()
    if os.path.exists(a.out) and not a.force and not a.trace:
        for l in open(a.out):
            j = json.loads(l)
            done.add((j["program"], j["bin"], j["config"], j["depth"]))
    for f in a.files:
        f = os.path.abspath(f)
        for c in a.configs.split(","):
            if (os.path.relpath(f, R.HERE), a.bin, c, a.depth or 10) in done:
                continue
            r = run(a.bin, f, c, a.depth, a.trace)
            t = r.pop("_trace", None)
            if t is None:
                with open(a.out, "a") as o:
                    o.write(json.dumps(r) + "\n")
            cs = r["counters"]
            brief = " ".join("%s=%s" % (k.split(".", 1)[1] if k.startswith("summon") else k, v)
                             for k, v in cs.items()
                             if k in ("summon.subgoals", "summon.matches", "summon.depthExhausted",
                                      "eqsolve.premises") or k.startswith("premsubst"))
            if not a.quiet:
                print("%-44s %-22s %-9s %s | %s" % (
                    os.path.basename(f)[:44], c[:22], r["verdict"], brief,
                    (r["violations"] or r.get("errors") or [""])[0][:120]))
            if t:
                print("\n".join(l[:700] for l in t[-a.tail:]))
            sys.stdout.flush()


if __name__ == "__main__":
    main()
