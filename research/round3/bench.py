"""Per-flag timing table for the technique docs.

usage: bench.py BINID OUT.jsonl   (restartable; then bench.py --report OUT.jsonl > bench.md)
Each (config, workload) is run once with `--repeat 3` (best in-process time), pinned to one core,
sequentially. Configurations: baseline, each sound flag alone, and the sound set."""
import json, os, re, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.dirname(HERE)
EMPTY = os.path.join(RES, "workloads", "empty.hylo")
W = {"stdlib": EMPTY, "members-big": "workloads/members-big.hylo", "breadth40": "workloads/breadth40.hylo",
     "div-loop-20": "workloads/div-loop-20.hylo", "div-branch": "round3/depth/div-branch.hylo",
     "wide-tuple-5": "round3/depth/wide-tuple-5.hylo", "trans-8": "workloads/round3/trans-8.hylo",
     "assoceq-5": "workloads/round3/assoceq-5.hylo", "coerc-cache": "workloads/round3/orig-coerc-cache.hylo",
     "refine-8": "workloads/round3/refine-8.hylo", "nestwide-8": "workloads/round3/nestwide-8.hylo"}
SOUND = ["symindex", "coesrc", "traitindex", "memberskip", "unify", "index", "absmodel", "typevec"]
CONFIGS = {"baseline": ""} | {f: f for f in SOUND} | {"sound set": ",".join(SOUND)}

def run(binid, out):
    B = os.path.join(RES, "exp", "bin", binid, "tc-bench")
    done = set()
    if os.path.exists(out):
        done = {(r["config"], r["workload"]) for r in map(json.loads, open(out))}
    with open(out, "a") as o:
        for w, f in W.items():
            for c, flags in CONFIGS.items():
                if (c, w) in done: continue
                env = dict(os.environ, HYLO_TC_EXPERIMENTS=flags, HYLO_TC_ABSDEPTH="2")
                try:
                    p = subprocess.run(["taskset", "-c", "3", B, "--repeat", "3", os.path.join(RES, f)],
                                       env=env, capture_output=True, text=True, timeout=600)
                    m = re.search(r"type\.(stdlib|user)\s+([\d.]+)" if w == "stdlib" else r"type\.user\s+([\d.]+)", p.stdout)
                    ms = float(m.group(m.lastindex)) if m else None
                    if w == "stdlib": ms = float(re.search(r"type\.stdlib\s+([\d.]+)", p.stdout).group(1))
                except subprocess.TimeoutExpired:
                    ms = None
                o.write(json.dumps({"config": c, "workload": w, "ms": ms}) + "\n"); o.flush()

def report(out):
    rows = list(map(json.loads, open(out)))
    t = {(r["config"], r["workload"]): r["ms"] for r in rows}
    print("Typing time (ms), best of --repeat 3, pinned to one core; stdlib = stdlib typing, others = user typing.")
    print("Each cell: time (speed-up vs baseline). TO = timeout (600 s).\n")
    print("| config | " + " | ".join(W) + " |"); print("|---" * (len(W) + 1) + "|")
    for c in CONFIGS:
        cells = []
        for w in W:
            v, b = t.get((c, w)), t.get(("baseline", w))
            cells.append("TO" if v is None else (f"{v:.0f}" if c == "baseline" or not b else f"{v:.0f} ({b / v:.1f}×)"))
        print(f"| {c} | " + " | ".join(cells) + " |")

if sys.argv[1] == "--report": report(sys.argv[2])
else: run(sys.argv[1], sys.argv[2])
