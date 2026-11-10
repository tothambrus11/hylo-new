"""Leave-one-out ablation of the final configuration.

usage: ablation.py BINID OUT.jsonl   (restartable); ablation.py --report OUT.jsonl
For each technique, measures FULL without it (and FULL, and the baseline) on a set of workloads.
Minimum of 3 in-process runs, pinned to one core, 120 s limit."""
import json, os, re, subprocess, sys
RES = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = {"stdlib": "workloads/empty.hylo", "members-big": "workloads/members-big.hylo",
     "breadth40": "workloads/breadth40.hylo", "div-branch": "round3/depth/div-branch.hylo",
     "trans-8": "workloads/round3/trans-8.hylo", "assoceq-8": "workloads/round3/assoceq-8.hylo",
     "nestwide-8": "workloads/round3/nestwide-8.hylo", "ovl-4-8": "workloads/ovl-4-8.hylo",
     "x10b": "round3/soundness/review2/eq-regress-judge/x10b-ext-where-assoc.hylo",
     "div-eq-ovl": "round3/soundness/review2/perf/div-eq-ovl-b3-1.hylo"}
FIX = ["occurs", "fixsubst", "eqsolve", "extorder", "arrowenv", "eqmgu", "givencheck", "budget"]
PERF = ["symindex", "coesrc", "traitindex", "memberskip", "unify", "index", "absmodel", "absquotient", "typevec", "reifymemo"]
FULL = FIX + PERF
CONFIGS = {"baseline": [], "FULL": FULL} | {"-" + f: [x for x in FULL if x != f] for f in FULL}

def run(binid, out):
    B = os.path.join(RES, "exp", "bin", binid, "tc-bench")
    done = set()
    if os.path.exists(out):
        done = {(r["config"], r["workload"]) for r in map(json.loads, open(out))}
    with open(out, "a") as o:
        for w, f in W.items():
            for c, flags in CONFIGS.items():
                if (c, w) in done: continue
                env = dict(os.environ, HYLO_TC_EXPERIMENTS=",".join(flags))
                ms = d = None; note = ""
                try:
                    p = subprocess.run(["taskset", "-c", "3", B, "--repeat", "3", os.path.join(RES, f)],
                                       env=env, capture_output=True, text=True, timeout=120)
                    m = re.search(r"type\." + ("stdlib" if w == "stdlib" else "user") + r"\s+([\d.]+)", p.stdout)
                    ms = float(m.group(1)) if m else None
                    m = re.search(r"diagnostics: (\d+)", p.stdout); d = int(m.group(1)) if m else None
                    if p.returncode != 0: note = "crash/OOM"
                except subprocess.TimeoutExpired:
                    note = "timeout"
                o.write(json.dumps({"config": c, "workload": w, "ms": ms, "d": d, "note": note}) + "\n"); o.flush()

def report(out):
    t = {(r["config"], r["workload"]): r for r in map(json.loads, open(out))}
    print("| configuration | " + " | ".join(W) + " |")
    print("|---|" + "---:|" * len(W))
    for c in CONFIGS:
        cells = []
        for w in W:
            r = t.get((c, w)); full = t.get(("FULL", w))
            if r is None: cells.append("-")
            elif r["ms"] is None: cells.append(r["note"] or "?")
            else:
                s = f"{r['ms']:.1f}" if r["ms"] < 100 else f"{r['ms']:.0f}"
                if c not in ("FULL", "baseline") and full and full["ms"]:
                    x = r["ms"] / full["ms"]
                    if x > 1.15 or x < 0.87: s += f" (**{x:.1f}×**)"
                    if r["d"] != full["d"]: s += f" [d={r['d']}]"
                cells.append(s)
        print(f"| {c} | " + " | ".join(cells) + " |")

if __name__ == "__main__":
    if sys.argv[1] == "--report": report(sys.argv[2])
    else: run(sys.argv[1], sys.argv[2])
