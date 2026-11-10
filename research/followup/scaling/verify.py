#!/usr/bin/env python3
"""Re-measures chosen points of results.jsonl and compares verdict and counters with the record.

Usage: verify.py [--timeout S] [--out verify.jsonl] FAMILY:N:CONFIG ...

One tc-bench process at a time. Appends one record per point to the output file, with
`same_status` and `same_counters` (every counter of the user module except the time-valued
`absmodel.micros`), and the full list of diagnostics. Restartable: finished points are skipped.
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import run  # noqa: E402


def main():
    a = sys.argv[1:]
    opt = lambda k, d: a[a.index(k) + 1] if k in a else d
    timeout = int(opt("--timeout", "60"))
    out = opt("--out", os.path.join(HERE, "verify.jsonl"))
    points = [x for x in a if x.count(":") == 2]
    rec = {}
    for l in open(os.path.join(HERE, "results.jsonl")):
        if l.strip():
            r = json.loads(l)
            if r.get("pass", 0) == 0:
                rec[(r["family"], r["n"], r["config"])] = r
    done = set()
    if os.path.exists(out):
        done = {(r["family"], r["n"], r["config"]) for r in map(json.loads, open(out))}
    strip = lambda d: {k: v for k, v in (d or {}).items() if k != "absmodel.micros"}
    with open(out, "a") as f:
        for p in points:
            fam, n, cfg = p.split(":")
            n = int(n)
            if (fam, n, cfg) in done:
                continue
            r = run.measure(fam, n, cfg, timeout, 9)
            r0 = rec.get((fam, n, cfg))
            r["recorded_status"] = r0 and r0["status"]
            r["recorded_ms"] = r0 and r0.get("type_user_ms")
            r["same_status"] = bool(r0) and r0["status"] == r["status"]
            r["same_counters"] = bool(r0) and strip(r0.get("counters")) == strip(r["counters"])
            f.write(json.dumps(r) + "\n"); f.flush()
            c = r["counters"]
            print(f"{fam:20} n={n:<5} {cfg:14} {r['status']:7} (recorded {r['recorded_status']}) "
                  f"counters {'same' if r['same_counters'] else 'DIFFER'} "
                  f"matches={c.get('summon.matches')} forks={c.get('solver.forks')} "
                  f"depthEx={c.get('summon.depthExhausted')} budgetEx={c.get('summon.budgetExhausted')} "
                  f"ms={r['type_user_ms']} (recorded {r['recorded_ms']}) {(r['diags'] or [''])[0][:90]}",
                  flush=True)


if __name__ == "__main__":
    main()
