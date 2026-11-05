"""Depth-cap sensitivity of programs whose resolution is deep, fails or diverges.

usage: depthscan2.py BINID OUT.jsonl  (restartable). Runs each file in research/depth/*.hylo and
the divergence/chain workloads at several caps, with the baseline and with the sound flag set."""
import glob, json, os, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.dirname(os.path.dirname(HERE))
B = os.path.join(RES, "exp", "bin", sys.argv[1], "tc-bench")
OUT = sys.argv[2]
DEPTHS = [6, 8, 10, 12, 14, 16, 20]
CONFIGS = {"baseline": "", "sound": "symindex,coesrc,traitindex,memberskip,unify,index,absmodel,typevec"}
files = sorted(glob.glob(os.path.join(HERE, "*.hylo")))
files += [os.path.join(RES, "workloads", f + ".hylo") for f in
          ["div-loop", "div-grow", "div-dead", "div-loop-20", "div-grow-20", "div-dead-20",
           "chain3", "chain8", "chain9", "chain12"]]
done = set()
if os.path.exists(OUT):
    for l in open(OUT):
        r = json.loads(l); done.add((r["file"], r["depth"], r["config"]))

def run(job):
    f, d, c = job
    env = dict(os.environ, HYLO_TC_MAXDEPTH=str(d), HYLO_TC_EXPERIMENTS=CONFIGS[c])
    row = {"file": os.path.relpath(f, RES), "depth": d, "config": c}
    try:
        p = subprocess.run([B, "--count", f], env=env, capture_output=True, text=True, timeout=120)
        o = p.stdout + p.stderr
        g = lambda rx: (lambda m: m.group(1) if m else None)(re.search(rx, o))
        row.update(status="ok" if g(r"type\.user\s+([\d.]+)") else f"rc{p.returncode}",
                   ms=float(g(r"type\.user\s+([\d.]+)") or "nan"), diags=int(g(r"diagnostics: (\d+)") or -1),
                   matches=int(g(r"counters\.user:.*?summon\.matches=(\d+)") or 0),
                   exhausted=int(g(r"counters\.user:.*?summon\.depthExhausted=(\d+)") or 0),
                   refuted=int(g(r"counters\.user:.*?absmodel\.refuted=(\d+)") or 0))
    except subprocess.TimeoutExpired:
        row.update(status="timeout")
    return row

jobs = [(f, d, c) for f in files for d in DEPTHS for c in CONFIGS
        if (os.path.relpath(f, RES), d, c) not in done]
with ThreadPoolExecutor(3) as ex, open(OUT, "a") as out:
    for r in ex.map(run, jobs):
        out.write(json.dumps(r) + "\n"); out.flush()
