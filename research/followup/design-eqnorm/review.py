#!/usr/bin/env python3
"""Review runner: runs Hylo programs under named (binary, flags) configurations, one at a time.

Usage:
  review.py [--configs base,FULL,S1,S1check] [--out review.jsonl] [--force] [--trace] FILE.hylo...

Configurations:
  base      frozen binary eq9, no flag            (the existing checker)
  FULL      frozen binary eq9, every technique    (the reference of the design)
  FULL15    binary eq15 (stage 1 implemented), FULL flags only: must equal FULL
  S1        binary eq15, FULL + eqindex,eqeager   (stage 1 of the design, as implemented)
  S1check   S1 + selfcheck                        (double-run check of stage 1)
  S1a       binary eq15, FULL + eqindex
  S1b       binary eq15, FULL + eqeager

Appends one JSON line per (program, configuration) to the output file; pairs already there are
skipped unless --force is given. `verify` mode (--verify) compares base and FULL with
tests/current.jsonl and prints the differences. `record` mode (--record) rewrites the line
"// currently:" of each program from the results of base, FULL, S1 and S1check.
"""
import argparse, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
BIN = "/home/user/hylo-new/research/exp/bin/"
B9 = BIN + "eq9-723cc0e6b0f8/tc-bench"
B15 = BIN + "eq15-f2809c746ab9/tc-bench"
FIX = "occurs,fixsubst,eqsolve,extorder,arrowenv,eqmgu,givencheck,budget"
FULL = FIX + ",symindex,coesrc,traitindex,memberskip,unify,index,absmodel,absquotient,typevec,reifymemo"
CONFIGS = {
    "base": (B9, ""),
    "FULL": (B9, FULL),
    "FULL15": (B15, FULL),
    "S1": (B15, FULL + ",eqindex,eqeager"),
    "S1check": (B15, FULL + ",eqindex,eqeager,selfcheck"),
    "S1a": (B15, FULL + ",eqindex"),
    "S1b": (B15, FULL + ",eqeager"),
}
KEYS = [
    "summon.subgoals", "summon.matches", "summon.layers", "summon.depthExhausted",
    "summon.budgetExhausted", "coerced.slowPath", "eqsolve.proved", "eqsolve.refuted",
    "eqsolve.untrusted", "eqmgu.solved", "absmodel.refuted", "index.skipped", "index.fallback",
    "eqeager.matches", "eqeager.parts", "eqeager.refuted", "selfcheck.eager.confirmed",
    "selfcheck.eager.beyondSearch", "selfcheck.violations", "names.appliesCalls",
]


def run(path, config, trace=False, timeout=60, env_extra=None):
    binary, flags = CONFIGS[config]
    if trace:
        flags = (flags + ",trace") if flags else "trace"
    env = dict(os.environ, HYLO_TC_EXPERIMENTS=flags)
    env.update(env_extra or {})
    p = subprocess.run(
        ["timeout", str(timeout), binary, "--count", path], env=env, capture_output=True, text=True)
    out = p.stdout + p.stderr
    r = {"program": os.path.relpath(path, HERE), "config": config, "exit": p.returncode}
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
        r["errors"] = [e.split("error:", 1)[1].strip() for e in errs]
        if any(("expected" in e and "cannot" not in e) or "is not a valid identifier" in e for e in errs):
            r["verdict"] = "SYNTAX?"
    r["violations"] = sorted(set(re.findall(r"\[selfcheck\] VIOLATION: (.*)", out)))
    m = re.search(r"counters\.user: (.*)", out)
    cs = dict(kv.split("=") for kv in m.group(1).split()) if m else {}
    r["counters"] = {k: int(cs[k]) for k in KEYS if k in cs}
    if trace:
        r["_trace"] = [l for l in out.splitlines() if l.startswith("[trace]")]
    return r


SHOWN = ["summon.subgoals", "summon.matches", "summon.depthExhausted", "summon.budgetExhausted",
         "eqsolve.proved", "eqsolve.refuted", "index.fallback", "eqeager.matches"]


def record(path, rel, done):
    """Rewrites the "// currently:" line of `path` from the results in `done`."""
    names = {"base": "base", "FULL": "FULL", "S1": "stage 1 as first implemented (binary eq15, FULL,eqindex,eqeager)"}
    parts = []
    for c in ("base", "FULL", "S1"):
        r = done.get((rel, c))
        if r is None:
            continue
        v = {"crash(-6)": "out of memory", "timeout": "out of time"}.get(r["verdict"], r["verdict"])
        cs = " ".join("%s=%d" % (k, r["counters"][k]) for k in SHOWN if k in r.get("counters", {}))
        parts.append("%s %s%s" % (names[c], v, " (%s)" % cs if cs else ""))
    line = "// currently: " + "; ".join(parts) + "."
    for c in ("FULL", "S1"):
        r = done.get((rel, c))
        if r and r.get("errors"):
            line += " %s says: %s." % ("FULL" if c == "FULL" else "Stage 1", r["errors"][0][:110])
            break
    r = done.get((rel, "S1check"))
    if r is not None:
        line += " With selfcheck: " + (
            "VIOLATION, " + r["violations"][0][:80] if r.get("violations") else "no violation") + "."
    src = open(path).read().split("\n")
    src = [line if l.startswith("// currently:") else l for l in src]
    open(path, "w").write("\n".join(src))


_STD = {}


def stdlib_trace_lines(config):
    if config not in _STD:
        e = os.path.join(HERE, "experiments", "empty.hylo")
        _STD[config] = len(run(e, config, trace=True)["_trace"])
    return _STD[config]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--configs", default="base,FULL,FULL15,S1,S1check")
    ap.add_argument("--out", default=os.path.join(HERE, "review.jsonl"))
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--record", action="store_true")
    ap.add_argument("--timeout", type=int, default=60)
    ap.add_argument("--width", type=int, default=300)
    a = ap.parse_args()
    done = {}
    if os.path.exists(a.out) and not a.trace:
        for l in open(a.out):
            j = json.loads(l)
            done[(j["program"], j["config"])] = j
    recorded = {}
    if a.verify:
        for l in open(os.path.join(HERE, "tests", "current.jsonl")):
            j = json.loads(l)
            recorded[(j["program"], j["config"])] = j
    for f in a.files:
        f = os.path.abspath(f)
        rel = os.path.relpath(f, HERE)
        for c in a.configs.split(","):
            if (rel, c) in done and not a.force and not a.trace:
                r = done[(rel, c)]
            else:
                r = run(f, c, trace=a.trace, timeout=a.timeout)
                t = r.pop("_trace", None)
                if not a.trace:
                    with open(a.out, "a") as o:
                        o.write(json.dumps(r) + "\n")
                elif t is not None:
                    r["_t"] = "\n".join(l[:a.width] for l in t[stdlib_trace_lines(c):])
            cs = " ".join("%s=%s" % (k.replace("summon.", "s.").replace("selfcheck.", "sc."), v)
                          for k, v in r.get("counters", {}).items()
                          if k not in ("names.appliesCalls", "coerced.slowPath", "summon.layers"))
            note = ""
            if a.verify and (rel, c) in recorded:
                old = recorded[(rel, c)]
                same = old["verdict"] == r["verdict"] and all(
                    old["counters"].get(k) == r["counters"].get(k)
                    for k in old["counters"] if k in KEYS)
                note = "  [recorded: same]" if same else "  [RECORDED DIFFERS: %s %s]" % (
                    old["verdict"], old["counters"])
            print("%-46s %-8s %-9s %s | %s%s%s" % (
                os.path.basename(f), c, r["verdict"], cs, (r.get("errors") or [""])[0][:100],
                ("  VIOLATION: " + r["violations"][0][:200]) if r.get("violations") else "", note))
            if r.get("_t"):
                print(r["_t"])
            sys.stdout.flush()
            done[(rel, c)] = r
        if a.record:
            record(f, rel, done)


if __name__ == "__main__":
    main()
