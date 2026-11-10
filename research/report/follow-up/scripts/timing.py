"""Careful timing of type-checker configurations.

usage: timing.py BINID OUT.jsonl [rounds]     (restartable)
       timing.py --report OUT.jsonl

Earlier measurements (minimum of three runs in one process, one session) differed by up to 20%
between sessions. This harness interleaves the configurations round-robin, so that drift of the
machine affects all of them alike, takes one sample per process (the best of three in-process
repetitions), and reports the median with a bootstrap 95% confidence interval, both for the time
and for the ratio to the baseline. Run it on an otherwise idle machine."""
import json, os, random, re, statistics, subprocess, sys
RES = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIX = ["occurs", "fixsubst", "eqsolve", "extorder", "arrowenv", "eqmgu", "givencheck", "budget"]
PERF = ["symindex", "coesrc", "traitindex", "memberskip", "unify", "index", "absmodel", "absquotient", "typevec", "reifymemo"]
FULL = FIX + PERF
MIN5 = ["index", "memberskip", "typevec", "symindex", "traitindex"]
CONFIGS = {"baseline": [], "FIX": FIX, "FULL": FULL, "MIN5": MIN5,
           "MIN5+reifymemo": MIN5 + ["reifymemo"], "MIN5+unify": MIN5 + ["unify"],
           "MIN5+coesrc": MIN5 + ["coesrc"], "MIN5+absmodel": MIN5 + ["absmodel", "absquotient"]}
CONFIGS |= {"+" + f: [f] for f in PERF}
CONFIGS |= {"FULL-" + f: [x for x in FULL if x != f] for f in PERF}
W = {"stdlib": "workloads/empty.hylo"}

def sample(binary, flags, workload):
    p = subprocess.run(["taskset", "-c", "3", binary, "--repeat", "3", os.path.join(RES, W[workload])],
                       env=dict(os.environ, HYLO_TC_EXPERIMENTS=",".join(flags)), capture_output=True, text=True, timeout=600)
    k = "stdlib" if workload == "stdlib" else "user"
    return float(re.search(r"type\." + k + r"\s+([\d.]+)", p.stdout).group(1))

def run(binid, out, rounds):
    binary = os.path.join(RES, "exp", "bin", binid, "tc-bench")
    done = {}
    if os.path.exists(out):
        for r in map(json.loads, open(out)): done[(r["config"], r["workload"])] = done.get((r["config"], r["workload"]), 0) + 1
    with open(out, "a") as o:
        for i in range(rounds):
            names = list(CONFIGS); random.Random(i).shuffle(names)
            for w in W:
                for c in names:
                    if done.get((c, w), 0) > i: continue
                    o.write(json.dumps({"config": c, "workload": w, "round": i, "ms": sample(binary, CONFIGS[c], w)}) + "\n"); o.flush()

def ci(xs, f, n=2000):
    rng = random.Random(1)
    v = sorted(f([rng.choice(xs) for _ in xs]) for _ in range(n))
    return v[int(0.025 * n)], v[int(0.975 * n)]

def report(out):
    t = {}
    for r in map(json.loads, open(out)): t.setdefault((r["config"], r["workload"]), []).append(r["ms"])
    for w in W:
        base = t.get(("baseline", w), [])
        print(f"### {w}\n\n| configuration | runs | median (ms) | 95% CI | speed-up over baseline | 95% CI |\n|---|---:|---:|---|---:|---|")
        for c in CONFIGS:
            xs = t.get((c, w))
            if not xs: continue
            m = statistics.median(xs); lo, hi = ci(xs, statistics.median)
            if base and c != "baseline":
                rng = random.Random(2); rs = []
                for _ in range(2000):
                    a = statistics.median([rng.choice(base) for _ in base]); b = statistics.median([rng.choice(xs) for _ in xs]); rs.append(a / b)
                rs.sort(); sp = f"{statistics.median(base) / m:.2f}×"; spci = f"{rs[50]:.2f}–{rs[1950]:.2f}"
            else: sp, spci = "", ""
            print(f"| {c} | {len(xs)} | {m:.1f} | {lo:.1f}–{hi:.1f} | {sp} | {spci} |")
        print()

if __name__ == "__main__":
    if sys.argv[1] == "--report": report(sys.argv[2])
    else: run(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 15)
