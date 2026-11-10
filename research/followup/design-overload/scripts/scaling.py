#!/usr/bin/env python3
"""Records the solver counters of the three named workloads and of chains of + on the binary.

  python3 scripts/scaling.py     appends to results/workloads-binary.jsonl (restartable)

One tc-bench process at a time. Times are indicative only (the machine is shared).
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_tests as mt

OUT = os.path.join(mt.ROOT, 'results/workloads-binary.jsonl')
W = os.path.join(mt.RESEARCH, 'workloads')
CASES = [('ovl-4-8', os.path.join(W, 'ovl-4-8.hylo')),
         ('ovr-3-8', os.path.join(W, 'ovr-3-8.hylo')),
         ('ovl-ret-9', os.path.join(mt.RESEARCH, 'round3/soundness/review2/perf/ovl-ret-9.hylo'))]

if __name__ == '__main__':
    scratch = os.path.join(mt.ROOT, 'results', 'scratch')
    os.makedirs(scratch, exist_ok=True)
    for n in [2, 4, 6, 8, 10, 12, 14]:
        path = os.path.join(scratch, 'plus-chain-%d.hylo' % n)
        open(path, 'w').write(mt.plus_chain(n))
        CASES.append(('plus-chain-%d' % n, path))
    done = set()
    if os.path.exists(OUT):
        done = {(json.loads(l)['workload'], json.loads(l)['config']) for l in open(OUT)}
    with open(OUT, 'a') as out:
        for name, path in CASES:
            for config in mt.CONFIGS:
                if (name, config) in done:
                    continue
                env = dict(os.environ, HYLO_TC_EXPERIMENTS=mt.CONFIGS[config])
                import subprocess
                p = subprocess.run(['timeout', '120', mt.BIN, '--count', path], env=env,
                                   capture_output=True, text=True)
                r = mt.run(path, config, 120)
                ms = [l.split()[1] for l in p.stdout.split('\n') if l.startswith('type.user')]
                r.update(workload=name, config=config, type_user_ms=float(ms[0]) if ms else None)
                out.write(json.dumps(r) + '\n')
                out.flush()
                print(name, config, r.get('counters'), r.get('type_user_ms'))
