"""Baseline / FIX / FULL timing table for the final configuration.

usage: bench-final.py BINID OUT.jsonl   (restartable); bench-final.py --report OUT.jsonl > md
Each run is `--repeat 3` (best in-process time), pinned to one core, sequentially."""
import json, os, re, subprocess, sys
RES = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = {"stdlib": "workloads/empty.hylo", "members-big": "workloads/members-big.hylo",
     "breadth40": "workloads/breadth40.hylo", "div-loop-20": "workloads/div-loop-20.hylo",
     "div-branch": "round3/depth/div-branch.hylo", "wide-tuple-5": "round3/depth/wide-tuple-5.hylo",
     "trans-8": "workloads/round3/trans-8.hylo", "assoceq-5": "workloads/round3/assoceq-5.hylo",
     "assoceq-8": "workloads/round3/assoceq-8.hylo", "orig-coerc-cache": "workloads/round3/orig-coerc-cache.hylo",
     "assocneg-8": "workloads/round3/assocneg-8.hylo", "refine-8": "workloads/round3/refine-8.hylo",
     "nestwide-8": "workloads/round3/nestwide-8.hylo", "ovl-4-8": "workloads/ovl-4-8.hylo",
     "ovr-3-8": "workloads/ovr-3-8.hylo",
     "x10b-ext-where-assoc": "round3/soundness/review2/eq-regress-judge/x10b-ext-where-assoc.hylo",
     "open-wide-4": "round3/soundness/review2/perf/open-wide-4.hylo",
     "div-eq-ovl-b3-1": "round3/soundness/review2/perf/div-eq-ovl-b3-1.hylo",
     "occurs-dag-16": "round3/soundness/review2/perf/occurs-dag-16.hylo",
     "p02-cc-big": "round3/soundness/review2/eq-regress-judge/p02-cc-big.hylo",
     "perf-alias-7": "round3/soundness/review2/eq-unsound/perf-alias-7.hylo"}
FIX = "occurs,fixsubst,eqsolve,extorder,arrowenv,eqmgu,givencheck,budget"
FULL = FIX + ",symindex,coesrc,traitindex,memberskip,unify,index,absmodel,absquotient,typevec,reifymemo"
CONFIGS = {"baseline": "", "FIX": FIX, "FULL": FULL}

def run(binid, out):
    B = os.path.join(RES, "exp", "bin", binid, "tc-bench")
    done = set()
    if os.path.exists(out):
        done = {(r["config"], r["workload"]) for r in map(json.loads, open(out))}
    with open(out, "a") as o:
        for w, f in W.items():
            for c, flags in CONFIGS.items():
                if (c, w) in done: continue
                env = dict(os.environ, HYLO_TC_EXPERIMENTS=flags)
                ms, d, note = None, None, ""
                try:
                    p = subprocess.run(["taskset", "-c", "3", B, "--repeat", "3", os.path.join(RES, f)],
                                       env=env, capture_output=True, text=True, timeout=300)
                    k = "stdlib" if w == "stdlib" else "user"
                    m = re.search(r"type\." + k + r"\s+([\d.]+)", p.stdout)
                    ms = float(m.group(1)) if m else None
                    m = re.search(r"diagnostics: (\d+)", p.stdout)
                    d = int(m.group(1)) if m else None
                    if p.returncode != 0: note = "crash/OOM"
                except subprocess.TimeoutExpired:
                    note = "timeout 300 s"
                o.write(json.dumps({"config": c, "workload": w, "ms": ms, "d": d, "note": note}) + "\n"); o.flush()

def report(out):
    t = {(r["config"], r["workload"]): r for r in map(json.loads, open(out))}
    print("| workload | " + " | ".join(CONFIGS) + " |")
    print("|---|" + "---|" * len(CONFIGS))
    for w in W:
        cells = []
        for c in CONFIGS:
            r = t.get((c, w))
            if r is None: cells.append("-")
            elif r["ms"] is None: cells.append(r["note"] or "?")
            else: cells.append(f"{r['ms']:.2f} (d={r['d'] if r['d'] is not None else '?'})")
        print(f"| {w} | " + " | ".join(cells) + " |")

if __name__ == "__main__":
    if sys.argv[1] == "--report": report(sys.argv[2])
    else: run(sys.argv[1], sys.argv[2])
