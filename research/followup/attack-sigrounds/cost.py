#!/usr/bin/env python3
"""Generates chains of dependent declarations and measures the cost of sigrounds on them.

usage: cost.py [N ...]      (default: 2 4 6 8 10 12 16 24 32)

Shapes (written to cost/SHAPE-N.hylo):
  given   N givens, each with a subject that is an alias through the previous given (tests/33).
  ext     N extensions, each extending the member type declared by the previous one.
  wide    one dependency of depth 1 and N unrelated generic givens with a where clause.
  flip    the unstable pair of tests/29 followed by a chain of N extensions that hang on it.
Each program is run under FULL, NEW and NEW+selfcheck, one process at a time; the verdict, the
sigrounds counters, summon.calls, summon.matches, names.appliesCalls and the time of the user
module (indicative only) are appended to cost.jsonl and printed."""
import json, os, re, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import tcrun
B = os.path.join(tcrun.RES, "exp", "bin", "eq22-554540c3a507", "tc-bench")

def given(n):
    s = ["trait P { type E }", "struct A {}", "struct Foo<T> {}", "given A is P { type E = A }", "type X0 = A.E"]
    for i in range(n - 1):
        s += [f"type F{i} = Foo<X{i}>", f"given F{i} is P {{ type E = F{i} }}", f"type X{i+1} = F{i}.E"]
    return "\n".join(s + [f"fun f(x: X{n-1}) {{}}"]) + "\n"

def ext(n):
    s = ["struct A {}"] + [f"struct S{i} {{}}" for i in range(n + 1)]
    s += ["extension A { type M0 = S0 }"]
    for i in range(n - 1):
        s += [f"extension S{i} {{ type M{i+1} = S{i+1} }}".replace(f"extension S{i} ", f"extension {'A.M0' if i == 0 else f'S{i-1}.M{i}'} ")]
    return "\n".join(s + [f"fun f(x: S{n-2}.M{n-1}) {{}}" if n > 1 else "fun f(x: A.M0) {}"]) + "\n"

def wide(n):
    s = ["trait P { type E }", "trait Q {}", "struct A {}", "given A is P { type E = Int }", "given A.E is Q {}"]
    for i in range(n):
        s += [f"struct W{i}<C> {{}}", f"given <C where C is P, C.E is Q> => W{i}<C> is Q {{}}"]
    return "\n".join(s) + "\n"

def flip(n):
    s = ["struct A {}"] + [f"struct S{i} {{}}" for i in range(n + 1)]
    s += ["extension A { type Me = A }", "extension A.Me { type Me = Int }", "extension A.Me { type M0 = S0 }"]
    for i in range(n - 1):
        s += [f"extension {'A.M0' if i == 0 else f'S{i-1}.M{i}'} {{ type M{i+1} = S{i+1} }}"]
    return "\n".join(s) + "\n"

def run(config, path):
    p = subprocess.run([B, "--count", path], env=dict(os.environ, HYLO_TC_EXPERIMENTS=tcrun.flags(config)),
                       capture_output=True, text=True, timeout=300)
    m = re.search(r"diagnostics: (\d+)", p.stdout)
    c = re.search(r"counters.user:(.*)", p.stdout)
    cs = {k: int(v) for k, v in (x.split("=") for x in (c.group(1).split() if c else []))}
    t = re.search(r"type\.user\s*[:=]?\s*([0-9.]+)", p.stdout)
    return {"verdict": ("crash %d" % p.returncode) if p.returncode else ("accept" if m and m.group(1) == "0" else "reject"),
            "ndiag": int(m.group(1)) if m else None, "ms": float(t.group(1)) if t else None,
            **{k: cs.get(k, 0) for k in ("sigrounds.nodes", "sigrounds.rounds", "sigrounds.restores", "summon.calls",
                                         "summon.matches", "names.appliesCalls", "index.unavailable")}}

if __name__ == "__main__":
    ns = [int(x) for x in sys.argv[1:]] or [2, 4, 6, 8, 10, 12, 16, 24, 32]
    out = open(os.path.join(HERE, "cost.jsonl"), "a")
    for shape in (given, ext, wide, flip):
        for n in ns:
            path = os.path.join(HERE, "cost", f"{shape.__name__}-{n:02}.hylo")
            open(path, "w").write(shape(n))
            for config in ("FULL", "NEW", "NEW+selfcheck"):
                try: r = run(config, path)
                except subprocess.TimeoutExpired: r = {"verdict": "timeout"}
                r.update(shape=shape.__name__, n=n, config=config)
                out.write(json.dumps(r) + "\n"); out.flush()
                print(f"{shape.__name__:5} n={n:2} {config:14} {r['verdict']:7} " + " ".join(
                    f"{k.split('.')[-1]}={v}" for k, v in r.items() if k not in ("shape", "n", "config", "verdict")), flush=True)
