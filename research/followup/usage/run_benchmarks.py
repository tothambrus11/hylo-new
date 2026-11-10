#!/usr/bin/env python3
"""Runs the benchmarks of ./benchmarks under the configurations base, FIX and FULL.

usage:  python3 run_benchmarks.py [--report-only]

For each benchmark `benchmarks/X.hylo` three kinds of copies are generated in `benchmarks/generated/`:
  X.neg.hylo        the `// NEG:` lines enabled: each is a false claim, so each must be reported;
  X.control.hylo    every `need<L, R>()` replaced by `need<L, Zz>()` and `need<R, Zz>()` for a fresh
                    type `Zz`: each must be reported, and no message may mention the error type
                    `#!` (this shows that every type expression of the benchmark resolves);
  X.fn-NAME.hylo    the benchmark with only one of its multi-line functions.
The files of `benchmarks/gaps/` are run as they are.

One checker process runs at a time, under `timeout 60`.  Results are appended to
`bench-results.jsonl`; a (file, configuration, content hash) that is already there is not run again.
`bench-results.md` is rewritten from the records.
"""
import hashlib, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
BENCH = os.path.join(HERE, "benchmarks")
GEN = os.path.join(BENCH, "generated")
B = "/home/user/hylo-new/research/exp/bin/eq9-723cc0e6b0f8/tc-bench"
FIX = "occurs,fixsubst,eqsolve,extorder,arrowenv,eqmgu,givencheck,budget"
FULL = FIX + ",symindex,coesrc,traitindex,memberskip,unify,index,absmodel,absquotient,typevec,reifymemo"
CONFIGS = [("base", ""), ("FIX", FIX), ("FULL", FULL)]
OUT = os.path.join(HERE, "bench-results.jsonl")
TIMEOUT = 60

NEED = re.compile(r"^(\s*)need<(.*)>\(\)\s*(//.*)?$")

def split_args(s):
    depth = 0
    for i, c in enumerate(s):
        if c == "<": depth += 1
        elif c == ">": depth -= 1
        elif c == "," and depth == 0: return s[:i].strip(), s[i + 1:].strip()
    raise ValueError(s)

def generate():
    os.makedirs(GEN, exist_ok=True)
    plan = []     # (path, kind, expected number of diagnostics or None)
    for f in sorted(os.listdir(BENCH)):
        if not f.endswith(".hylo"): continue
        name = f[:-5]
        src = open(os.path.join(BENCH, f)).read()
        lines = src.split("\n")
        plan.append((os.path.join(BENCH, f), "benchmark", 0))
        # negative copy
        neg = [re.sub(r"^(\s*)// NEG: ", r"\1", l) for l in lines]
        n_neg = sum(1 for l in lines if re.match(r"\s*// NEG: ", l))
        p = os.path.join(GEN, name + ".neg.hylo")
        open(p, "w").write("\n".join(neg)); plan.append((p, "false claims", n_neg))
        # control copy
        ctl, n = [], 0
        for l in lines:
            m = NEED.match(l)
            if m:
                a, b = split_args(m.group(2))
                ctl.append("%sneed<%s, Zz>()" % (m.group(1), a)); ctl.append("%sneed<%s, Zz>()" % (m.group(1), b)); n += 2
            else: ctl.append(l)
        ctl.append("struct Zz {}\n")
        p = os.path.join(GEN, name + ".control.hylo")
        open(p, "w").write("\n".join(ctl)); plan.append((p, "control", n))
        # one function at a time
        blocks, i = [], 0
        while i < len(lines):
            m = re.match(r"fun (\w+)<", lines[i])
            if m and not lines[i].rstrip().endswith("}"):
                j = i
                while lines[j] != "}": j += 1
                blocks.append((m.group(1), i, j)); i = j + 1
            else: i += 1
        if len(blocks) > 1:
            for fn, a, b in blocks:
                keep = [l for k, l in enumerate(lines) if not any(x <= k <= y for n2, x, y in blocks if n2 != fn)]
                p = os.path.join(GEN, "%s.fn-%s.hylo" % (name, fn))
                open(p, "w").write("\n".join(keep)); plan.append((p, "one function", 0))
    gaps = os.path.join(BENCH, "gaps")
    for f in sorted(os.listdir(gaps)):
        if f.endswith(".hylo"): plan.append((os.path.join(gaps, f), "gap", None))
    return plan

def run(path, flags):
    env = dict(os.environ, HYLO_TC_EXPERIMENTS=flags)
    p = subprocess.run(["timeout", str(TIMEOUT), B, "--count", path], env=env, capture_output=True, text=True)
    rec = {"exit": p.returncode, "diagnostics": None, "messages": [], "counters": {}, "type_user_ms": None}
    lines = p.stdout.split("\n")
    for k, l in enumerate(lines):
        if l.startswith("counters.user:"):
            for kv in l.split()[1:]:
                a, b = kv.split("="); rec["counters"][a] = int(b)
        elif l.startswith("diagnostics:"):
            rec["diagnostics"] = int(l.split()[1])
        elif l.startswith("type.user"):
            rec["type_user_ms"] = float(l.split()[1])
        m = re.match(r"\s+\S+\.hylo:(\d+)\.[\d-]+: error: (.*)$", l)
        if m: rec["messages"].append([int(m.group(1)), m.group(2)[:400]])
    return rec

def load():
    recs = {}
    if os.path.exists(OUT):
        for l in open(OUT):
            r = json.loads(l); recs[(r["file"], r["config"], r["sha1"])] = r
    return recs

def verdict(r, expected):
    if r["exit"] == 124: return "timeout (60 s)"
    if r["exit"] in (139, -11): return "crash (stack overflow)"
    if r["exit"] in (134, -6): return "crash (out of memory)"
    if r["exit"] != 0 or r["diagnostics"] is None: return "exit %d" % r["exit"]
    if r["diagnostics"] == 0: return "accepted"
    return "rejected (%d)" % r["diagnostics"]

def main():
    plan = generate()
    recs = load()
    if "--report-only" not in sys.argv:
        with open(OUT, "a") as out:
            for path, kind, expected in plan:
                sha = hashlib.sha1(open(path, "rb").read()).hexdigest()
                rel = os.path.relpath(path, BENCH)
                for cname, flags in CONFIGS:
                    if (rel, cname, sha) in recs: continue
                    r = run(path, flags)
                    r.update(file=rel, config=cname, sha1=sha, kind=kind, expected=expected)
                    recs[(rel, cname, sha)] = r
                    out.write(json.dumps(r) + "\n"); out.flush()
                    print(rel, cname, verdict(r, expected), flush=True)
    # report
    C = ["summon.calls", "summon.matches", "summon.layers", "eqsolve.proved", "eqsolve.refuted", "eqmgu.solved"]
    md = ["| File | Kind | Expected | Configuration | Verdict | `#!` in messages | " + " | ".join("`%s`" % c for c in C) + " | type.user ms (indicative) |",
          "|---|---|---|---|---|---:|" + "---:|" * (len(C) + 1)]
    for path, kind, expected in plan:
        sha = hashlib.sha1(open(path, "rb").read()).hexdigest()
        rel = os.path.relpath(path, BENCH)
        for cname, _ in CONFIGS:
            r = recs.get((rel, cname, sha))
            if r is None: continue
            exp = "see file" if expected is None else ("accepted" if expected == 0 else "%d errors" % expected)
            hb = sum("#!" in m[1] for m in r["messages"])
            cs = [str(r["counters"].get(c, 0)) if r["counters"] else "–" for c in C]
            t = "%.0f" % r["type_user_ms"] if r["type_user_ms"] is not None else "–"
            md.append("| `%s` | %s | %s | %s | %s | %d | %s | %s |" % (rel, kind, exp, cname, verdict(r, expected), hb, " | ".join(cs), t))
    open(os.path.join(HERE, "bench-results.md"), "w").write("\n".join(md) + "\n")

if __name__ == "__main__":
    main()
