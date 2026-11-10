#!/usr/bin/env python3
"""Reviewer's comparison of the implementation of `twins`, `cleanfirst` and `lookahead`
(hylo-impl commit 9dc04d7, binary exp/bin/eq25-c7cbd846a05c) with the existing search.

For each program and each reference configuration R, the program is type-checked under R and
under R plus each set of flags, and the two runs are compared: exit code, diagnostics (messages
in order), and the semantic dump (`--dump`). The solver counters of each run are recorded.

  python3 scripts/review_impl.py OUT.jsonl REFS FLAGSETS DIR_OR_FILE...
    REFS      ;-separated among base, FULL, NEWCORE (NEW of BRIEF2.md without the three flags)
    FLAGSETS  ;-separated lists of flags joined by +, e.g. "twins;twins+cleanfirst"

Sequential (one tc-bench process at a time); restartable (a line of OUT.jsonl is not redone).
"""
import hashlib, json, os, re, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RESEARCH = os.path.dirname(os.path.dirname(ROOT))
BIN = os.path.join(RESEARCH, 'exp/bin/eq25-c7cbd846a05c/tc-bench')
FIX = 'occurs,fixsubst,eqsolve,extorder,arrowenv,eqmgu,givencheck,budget'
FULL = FIX + ',symindex,coesrc,traitindex,memberskip,unify,index,absmodel,absquotient,typevec,reifymemo'
REFS = {'base': '', 'FULL': FULL,
        'NEWCORE': FULL + ',sigrounds,assocsubst,eqindex,eqeager,premsubst,headsubst,abstractstrict'}


def run(path, flags, timeout=200):
    with tempfile.NamedTemporaryFile(suffix='.dump', delete=False) as t:
        dump = t.name
    try:
        p = subprocess.run(['timeout', str(timeout), BIN, '--count', '--dump', dump, path],
                           env=dict(os.environ, HYLO_TC_EXPERIMENTS=flags),
                           capture_output=True, text=True)
        out = p.stdout
        text = open(dump, errors='replace').read() if os.path.exists(dump) else ''
    finally:
        if os.path.exists(dump):
            os.unlink(dump)
    counters = {}
    m = re.search(r'^counters.user:(.*)$', out, re.M)
    for kv in (m.group(1).split() if m else []):
        k, _, v = kv.partition('=')
        if k.startswith('solver.') or k.startswith('selfcheck.'):
            counters[k] = int(v)
    msgs = [re.sub(r'^\s*\S*?([^/\s]+\.hylo):', r'\1:', l.strip())
            for l in out.split('\n') if ': error: ' in l or ': warning: ' in l]
    d = re.search(r'^diagnostics: (\d+)', out, re.M)
    # Builtin function references print the raw identity of a machine type (`erased: 8800`),
    # which shifts when fewer types are interned; it is not part of the result.
    text = re.sub(r'erased: \d+', 'erased: _', text)
    # The dump of the user module only: the standard library is the same in every run compared.
    user = text.split('== module', 2)[-1] if text.count('== module') >= 2 else text
    return dict(exit=p.returncode, diagnostics=int(d.group(1)) if d else None, messages=msgs,
                counters=counters, dump=hashlib.sha1(text.encode()).hexdigest()[:12],
                user_dump=hashlib.sha1(user.encode()).hexdigest()[:12],
                violations=sorted(set(re.findall(r'\[selfcheck\] VIOLATION: (.*)', out))))


def main(out, refs, flagsets, where):
    files = []
    for w in where:
        if os.path.isdir(w):
            files += sorted(os.path.join(d, f) for d, _, fs in os.walk(w) for f in fs
                            if f.endswith('.hylo'))
        else:
            files.append(w)
    done = set()
    if os.path.exists(out):
        for line in open(out):
            r = json.loads(line)
            done.add((r['file'], r['ref'], r['flags']))
    bad = 0
    with open(out, 'a') as log:
        for f in files:
            rel = os.path.relpath(f, RESEARCH)
            for ref in refs:
                base = None
                for fs in flagsets:
                    if (rel, ref, fs) in done:
                        continue
                    if base is None:
                        base = run(f, REFS[ref])
                    r = run(f, ','.join(x for x in [REFS[ref]] + fs.split('+') if x))
                    same = dict(exit=base['exit'] == r['exit'],
                                messages=base['messages'] == r['messages'],
                                dump=base['dump'] == r['dump'],
                                user_dump=base['user_dump'] == r['user_dump'])
                    if 'selfcheck' in fs:
                        # The self-check solves each system twice; only its verdict, its
                        # messages and the violations it reports are compared.
                        same = dict(exit=same['exit'], messages=same['messages'])
                    row = dict(file=rel, ref=ref, flags=fs, same=same, reference=base, changed=r)
                    log.write(json.dumps(row) + '\n')
                    log.flush()
                    ok = all(same.values()) and not r['violations']
                    bad += not ok
                    c = r['counters']
                    print('%s %-44s %-8s %-28s forks %s -> %s%s' % (
                        'same   ' if ok else 'DIFFERS', os.path.basename(f)[:44], ref, fs,
                        base['counters'].get('solver.forks', 0), c.get('solver.forks', 0),
                        '' if ok else '  ' + json.dumps(same) + ' ' + '; '.join(r['violations'])))
    return bad


if __name__ == '__main__':
    a = sys.argv[1:]
    sys.exit(1 if main(a[0], a[1].split(';'), a[2].split(';'), a[3:]) else 0)
