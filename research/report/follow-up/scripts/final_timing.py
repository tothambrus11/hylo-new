"""Timings of the final binary for the tables of the report.

usage: final_timing.py BINID OUT.jsonl      (restartable; run on an idle machine)
For each workload and configuration: the minimum over three processes of the type-checking time
(each process reports the best of three in-process repetitions), and the number of diagnostics."""
import json, os, re, subprocess, sys
RES = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import tcrun
MINR = "index,typevec,symindex,traitindex,memberskip,twins,stackscan,coeset"
CONFIGS = {"base": "", "MINR": MINR, "FULL": tcrun.flags("FULL"), "NEW": tcrun.flags("NEW")}
W = {
 "stdlib": "workloads/empty.hylo", "members-big": "workloads/members-big.hylo", "breadth40": "workloads/breadth40.hylo",
 "div-branch": "round3/depth/div-branch.hylo", "div-loop-20": "workloads/div-loop-20.hylo",
 "trans-8": "round3/soundness/review/eqchain-fix/trans-8.hylo", "assoceq-8": "round3/soundness/review/eqchain-fix/assoceq-8.hylo",
 "coercion-cache": "workloads/round3/orig-coerc-cache.hylo", "assocneg-8": "round3/soundness/review/eqchain-fix/assocneg-8.hylo",
 "conditional-extension": "round3/soundness/review2/eq-regress-judge/x10b-ext-where-assoc.hylo",
 "open-equalities": "round3/soundness/review2/perf/open-wide-4.hylo", "tuple-equalities": "round3/soundness/review2/eq-regress-judge/p02-cc-big.hylo",
 "divergence-with-equality": "round3/soundness/review2/perf/div-eq-ovl-b3-1.hylo", "shared-bindings": "round3/soundness/review2/perf/occurs-dag-16.hylo",
 "overloads": "workloads/ovl-4-8.hylo", "return-type-overloads": "workloads/ovr-3-8.hylo",
 "plus-chain-14": "followup/overload/plus-chain-14.hylo", "assoceq-64": "followup/scaling/progs/assoceq-64.hylo",
 "swift-collection": "followup/usage/benchmarks/swift-collection-signature.hylo", "swift-string-protocol": "followup/usage/benchmarks/swift-string-protocol.hylo",
 "swift-transitive": "followup/usage/benchmarks/swift-transitive-parameters.hylo", "rust-flatten": "followup/usage/benchmarks/rust-flatten.hylo",
 "collection-example": "followup/headsubst/tests/c1-collection.hylo",
}
def sample(binary, flags, w):
    key = "stdlib" if w == "stdlib" else "user"
    try:
        p = subprocess.run(["taskset", "-c", "3", binary, "--repeat", "3", os.path.join(RES, W[w])],
                           env=dict(os.environ, HYLO_TC_EXPERIMENTS=flags), capture_output=True, text=True, timeout=90)
    except subprocess.TimeoutExpired:
        return None, "timeout"
    if p.returncode != 0: return None, "crash %d" % p.returncode
    m = re.search(r"type\." + key + r"\s+([\d.]+)", p.stdout); d = re.findall(r"diagnostics: (\d+)", p.stdout)
    return float(m.group(1)), "d=%s" % (d[-1] if d else "?")
binary = os.path.join(RES, "exp", "bin", sys.argv[1], "tc-bench"); out = sys.argv[2]
done = {(r["workload"], r["config"]) for r in map(json.loads, open(out))} if os.path.exists(out) else set()
with open(out, "a") as o:
    for w in W:
        for c in CONFIGS:
            if (w, c) in done: continue
            best, note = None, ""
            for _ in range(3):
                ms, note = sample(binary, CONFIGS[c], w)
                if ms is None: break
                best = ms if best is None else min(best, ms)
            o.write(json.dumps({"workload": w, "config": c, "ms": best, "note": note}) + "\n"); o.flush()
            print(w, c, best, note, flush=True)
