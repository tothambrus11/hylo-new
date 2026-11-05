#!/usr/bin/env python3
"""Uncached differential test: baseline vs configs, on one program (possibly several files).

usage: difft.py [--configs index;names,index] [--counters] FILE [FILE...]   (all files = one module)
       difft.py --each FILE...   (each file is its own program)
"""
import os, subprocess, sys, difflib, tempfile, re

B = "/home/hylo/hylo-tc/research/exp/bin/15f1d9abd0da/tc-bench"
OUT = "/home/hylo/hylo-tc/research/review/index/out"
os.makedirs(OUT, exist_ok=True)


def run(cfg, files, tag):
    env = dict(os.environ)
    env["HYLO_TC_ABSDEPTH"] = "2"
    if cfg:
        env["HYLO_TC_EXPERIMENTS"] = cfg
    else:
        env.pop("HYLO_TC_EXPERIMENTS", None)
    d = os.path.join(OUT, f"{tag}.{cfg or 'baseline'}.dump")
    try:
        p = subprocess.run([B, "--count", "--dump", d] + files, env=env, capture_output=True,
                           text=True, timeout=600)
    except subprocess.TimeoutExpired:
        return "timeout", "", ""
    if p.returncode != 0:
        return "crash(%d)" % p.returncode, "", (p.stdout + p.stderr)[-1500:]
    user = ""
    for l in p.stdout.splitlines():
        if l.startswith("counters.user:"):
            user = l
    txt = re.sub(r"\(erased: \d+\)", "(erased: _)", open(d).read())
    # drop the stdlib module part to keep diffs short but keep diags
    return "ok", txt, user


def main(argv):
    cfgs = ["index"]
    counters = False
    each = False
    files = []
    i = 0
    while i < len(argv):
        if argv[i] == "--configs":
            cfgs = [c for c in argv[i + 1].split(";") if c]; i += 2; continue
        if argv[i] == "--counters":
            counters = True; i += 1; continue
        if argv[i] == "--each":
            each = True; i += 1; continue
        files.append(os.path.abspath(argv[i])); i += 1
    groups = [[f] for f in files] if each else [files]
    bad = 0
    for g in groups:
        tag = "+".join(os.path.basename(f) for f in g)
        s0, t0, c0 = run("", g, tag)
        n_user = sum(1 for l in t0.splitlines() if l.startswith("diag") or "Test" in l)
        diags = [l for l in t0.splitlines() if l.startswith("diag")]
        print(f"== {tag}: baseline {s0}, {len(diags)} diags")
        for l in diags[:6]:
            print("     ", l[:200])
        if s0 != "ok":
            print(c0)
        if counters:
            print("   base ", pick(c0))
        for c in cfgs:
            s, t, cu = run(c, g, tag)
            same = (s, t) == (s0, t0)
            print(f"   [{c}] {s} {'IDENTICAL' if same else 'MISMATCH'}")
            if counters:
                print("   ", c, pick(cu))
            if not same:
                bad += 1
                for l in itertools_islice(difflib.unified_diff(t0.splitlines(True), t.splitlines(True), "baseline", c, n=0), 40):
                    print("      ", l, end="")
                if s != "ok":
                    print(cu)
    return 1 if bad else 0


def pick(c):
    ks = ["summon.subgoals", "summon.matches", "summon.layers", "summon.matchOK", "index.fallback",
          "index.skipped", "index.unavailable", "summon.depthExhausted", "coerced.slowPath"]
    d = dict(re.findall(r"([\w.]+)=(\d+)", c))
    return " ".join(f"{k.split('.')[-1]}={d.get(k, 0)}" for k in ks)


def itertools_islice(it, n):
    import itertools
    return itertools.islice(it, n)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
