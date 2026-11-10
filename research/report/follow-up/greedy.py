"""Greedy forward selection of techniques on standard-library type checking.

usage: greedy.py BINID OUT.json
Starting from no technique, repeatedly adds the technique that reduces the time most. Each
configuration is timed as the minimum over 4 processes of `--repeat 3` (12 runs), pinned to one
core. Stops when no addition improves the time by more than 2%."""
import json, os, re, subprocess, sys
RES = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FLAGS = ["occurs", "fixsubst", "eqsolve", "extorder", "arrowenv", "eqmgu", "givencheck", "budget",
         "symindex", "coesrc", "traitindex", "memberskip", "unify", "index", "absmodel", "absquotient",
         "typevec", "reifymemo"]
B = os.path.join(RES, "exp", "bin", sys.argv[1], "tc-bench")
cache = {}
def t(flags):
    k = ",".join(sorted(flags))
    if k not in cache:
        best = 1e9
        for _ in range(4):
            p = subprocess.run(["taskset", "-c", "3", B, "--repeat", "3", os.path.join(RES, "workloads/empty.hylo")],
                               env=dict(os.environ, HYLO_TC_EXPERIMENTS=k), capture_output=True, text=True, timeout=300)
            best = min(best, float(re.search(r"type\.stdlib\s+([\d.]+)", p.stdout).group(1)))
        cache[k] = best
    return cache[k]
chosen, steps = [], [{"added": None, "ms": t([])}]
while True:
    cands = [(t(chosen + [f]), f) for f in FLAGS if f not in chosen]
    if not cands: break
    ms, f = min(cands)
    if ms > steps[-1]["ms"] * 0.98: 
        steps.append({"stopped": True, "best_candidate": f, "ms": ms}); break
    chosen.append(f); steps.append({"added": f, "ms": ms})
    print(f, ms, flush=True)
steps.append({"all": t(FLAGS)})
json.dump({"steps": steps, "cache": cache}, open(sys.argv[2], "w"), indent=1)
print(json.dumps(steps))
