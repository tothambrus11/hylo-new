# Print a leave-one-out counter table: python3 loo.py DIR workload [stdlib|user]
import sys, os, re
d, w = sys.argv[1], sys.argv[2]; part = sys.argv[3] if len(sys.argv) > 3 else 'user'
FL = ['names','unify','index','absmodel','solver','loopcheck']; ALL = ','.join(FL)
cols = ['summon.subgoals','summon.matches','summon.matchOK','summon.layers','index.skipped','index.unavailable','index.fallback',
        'absmodel.refuted','absmodel.facts','absmodel.work','loopcheck.pruned','names.appliesCalls','names.skippedExtensions',
        'solver.probes','solver.forks','solver.goalSteps','summon.depthExhausted']
def load(c):
    p = os.path.join(d, f'{w}__{c}.txt')
    if not os.path.exists(p): return None
    t = open(p).read()
    if 'TIMEOUT' in t: return 'TIMEOUT'
    m = re.search(r'counters\.%s:\s*(.*)' % part, t); r = {}
    if m:
        for kv in m.group(1).split():
            k, v = kv.split('='); r[k] = int(v)
    tm = re.search(r'type\.%s\s+([\d.]+)' % ('stdlib' if part=='stdlib' else 'user'), t)
    r['ms'] = float(tm.group(1)) if tm else -1
    return r
rows = [('base','base'),('ALL',ALL)] + [('-'+f, ','.join(x for x in FL if x!=f)) for f in FL] + [(f, f) for f in FL]
short = lambda c: c.split('.')[-1][:9]
print(f'{w} [{part}]'); print('%-11s' % 'cfg' + ''.join('%10s' % short(c) for c in cols) + '%11s' % 'ms')
for name, c in rows:
    r = load(c)
    if r is None: continue
    if r == 'TIMEOUT': print('%-11s TIMEOUT' % name); continue
    print('%-11s' % name + ''.join('%10s' % r.get(k, '') for k in cols) + '%11.1f' % r['ms'])
