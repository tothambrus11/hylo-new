#!/usr/bin/env python3
"""Reviewer's check: runs every tests/*.hylo as it is on disk (base and FULL), and compares the
verdict, the number of diagnostics and the solver counters with the "// currently (...)" comments
of the file. Independent of make_tests.py. Sequential: one tc-bench process at a time.

  python3 scripts/review_check.py [name-prefix ...]

Raw results: results/review-tests.jsonl (one line per program and configuration; restartable:
a program whose text is unchanged is not run again).
"""
import glob, hashlib, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RESEARCH = os.path.dirname(os.path.dirname(ROOT))
BIN = os.path.join(RESEARCH, 'exp/bin/eq9-723cc0e6b0f8/tc-bench')
FIX = 'occurs,fixsubst,eqsolve,extorder,arrowenv,eqmgu,givencheck,budget'
FULL = FIX + ',symindex,coesrc,traitindex,memberskip,unify,index,absmodel,absquotient,typevec,reifymemo'
CONFIGS = {'base': '', 'FULL': FULL}
RESULTS = os.path.join(ROOT, 'results/review-tests.jsonl')


def run(path, config, timeout=150):
    env = dict(os.environ, HYLO_TC_EXPERIMENTS=CONFIGS[config])
    p = subprocess.run(['timeout', str(timeout), BIN, '--count', path], env=env,
                       capture_output=True, text=True)
    out = p.stdout
    if p.returncode != 0:
        return dict(exit=p.returncode, tail=(out + p.stderr)[-300:])
    counters = {}
    for line in out.split('\n'):
        if line.startswith('counters.user:'):
            for kv in line.split()[1:]:
                k, _, v = kv.partition('=')
                if k.startswith('solver.'):
                    counters[k] = int(v)
    m = re.search(r'^diagnostics: (\d+)\n((?:   .*\n)*)', out, re.M)
    diags = [re.sub(r'^\s*\S*?([^/\s]+\.hylo):', r'\1:', d.strip())
             for d in m.group(2).split('\n') if d.strip()]
    return dict(exit=0, diagnostics=int(m.group(1)), messages=diags, counters=counters)


def describe(r):
    if r['exit'] != 0:
        return 'exit code %d' % r['exit']
    c = r['counters']
    work = 'solver.forks=%d solver.overloads=%d' % (c.get('solver.forks', 0),
                                                    c.get('solver.overloads', 0))
    if r['diagnostics'] == 0:
        return 'accepted; ' + work
    msgs = '; '.join(re.sub(r'^\S+\.hylo:', '', m) for m in r['messages'])
    return 'rejected, %d diagnostic(s): %s; %s' % (r['diagnostics'], msgs, work)


def recorded(text, config):
    """The text of the "currently (config)" comment, continuation lines joined."""
    lines = text.split('\n')
    for i, l in enumerate(lines):
        if l.startswith('// currently (%s):' % config):
            s = l.split(':', 1)[1].strip()
            j = i + 1
            while j < len(lines) and lines[j].startswith('//   '):
                s += ' ' + lines[j][5:].strip()
                j += 1
            return s
    return None


def main(prefixes):
    cache = {}
    if os.path.exists(RESULTS):
        for line in open(RESULTS):
            r = json.loads(line)
            cache[(r['test'], r['sha'], r['config'])] = r
    bad = 0
    with open(RESULTS, 'a') as log:
        for path in sorted(glob.glob(os.path.join(ROOT, 'tests', '*.hylo'))):
            name = os.path.basename(path)[:-5]
            if prefixes and not any(name.startswith(p) for p in prefixes):
                continue
            text = open(path).read()
            sha = hashlib.sha1(text.encode()).hexdigest()[:12]
            for config in CONFIGS:
                key = (name, sha, config)
                if key in cache:
                    r = cache[key]
                else:
                    r = run(path, config)
                    r.update(test=name, sha=sha, config=config)
                    log.write(json.dumps(r) + '\n')
                    log.flush()
                want, got = recorded(text, config), describe(r)
                ok = (want == got)
                bad += (not ok)
                print('%s %-28s %-4s %s' % ('ok     ' if ok else 'DIFFERS', name, config, got))
                if not ok:
                    print('        recorded: %s' % want)
    return bad


if __name__ == '__main__':
    sys.exit(1 if main(sys.argv[1:]) else 0)
