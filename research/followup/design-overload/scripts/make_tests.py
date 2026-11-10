#!/usr/bin/env python3
"""Writes tests/*.hylo and records the current verdict of each program on the binary.

  python3 scripts/make_tests.py           writes the tests; runs base and FULL for each one
  python3 scripts/make_tests.py --check   re-runs the binary and fails if a recorded verdict or
                                          counter differs from the "currently" comment

Every test starts with three comments: what is expected once the change is in, why, and what
the binary does today. Raw results go to results/tests-current.jsonl (one line per program and
configuration). Runs are sequential (one tc-bench process at a time) and restartable: a result
is reused when the program text and the configuration are unchanged.
"""
import hashlib
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RESEARCH = os.path.dirname(os.path.dirname(ROOT))
BIN = os.path.join(RESEARCH, 'exp/bin/eq9-723cc0e6b0f8/tc-bench')
FIX = 'occurs,fixsubst,eqsolve,extorder,arrowenv,eqmgu,givencheck,budget'
FULL = FIX + ',symindex,coesrc,traitindex,memberskip,unify,index,absmodel,absquotient,typevec,reifymemo'
CONFIGS = {'base': '', 'FULL': FULL}
RESULTS = os.path.join(ROOT, 'results/tests-current.jsonl')


def structs(names):
    return ''.join('struct %s { public memberwise init }\n' % n for n in names)


def ovl(k, pattern, bad=False):
    s = structs(['A%d' % i for i in range(k)] + (['Z'] if bad else []))
    s += ''.join('fun f(x: A%d) -> A%d { x }\n' % (i, i) for i in range(k))
    params = ['x%d: A%d' % (i, p) for i, p in enumerate(pattern)] + (['z: Z'] if bad else [])
    args = ['f(A%d())' % p for p in pattern] + (['f(A0())'] if bad else [])
    return s + 'fun g(%s) {}\npublic fun main() { g(%s) }\n' % (', '.join(params), ', '.join(args))


def ovr(k, pattern, bad=False):
    s = structs(['A%d' % i for i in range(k)] + (['Z'] if bad else []))
    s += ''.join('fun h() -> A%d { A%d() }\n' % (i, i) for i in range(k))
    params = ['x%d: A%d' % (i, p) for i, p in enumerate(pattern)] + (['z: Z'] if bad else [])
    args = ['h()'] * (len(pattern) + (1 if bad else 0))
    return s + 'fun g(%s) {}\npublic fun main() { g(%s) }\n' % (', '.join(params), ', '.join(args))


def cyc(k, n):
    return [i % k for i in range(n)]


def plus_chain(n):
    return 'public fun main() {\n  let a = 1\n  let x = %s\n}\n' % ' + '.join(['a'] * (n + 1))


def from_file(path):
    """The program at `path` without its leading comment."""
    lines = open(os.path.join(RESEARCH, path)).read().split('\n')
    while lines and (lines[0].startswith('//') or not lines[0].strip()):
        lines.pop(0)
    return '\n'.join(lines).rstrip('\n') + '\n'


SAME = 'same verdict, diagnostics and inferred types as today'

METHOD_CHAIN = '''trait Stepper { fun next() -> Self }
struct C {
  public memberwise init
  public fun next() -> C { C() }
}
given C is Stepper {}
public fun main() {
  let c = C()
  let d = c.next().next().next().next().next().next()
}
'''

MIXED = '''public fun main() {
  let a = 1
  let b = 2
  let t = (a + b) * (a - b) + a * b == a + b + a
}
'''

INDEPENDENT = '''struct X { public memberwise init }
struct Y { public memberwise init }
struct S {
  public memberwise init
  public static fun a() -> Y { Y() }
}
fun k<V0, V1, V2, V3, V4, V5>(x0: V0, x1: V1, x2: V2, x3: V3, x4: V4, x5: V5) {}
public fun main() {
  extension S { static fun a() -> X { X() } }
  k(S.a(), S.a(), S.a(), S.a(), S.a(), S.a())
}
'''

BAD2 = '''struct A0 { public memberwise init }
struct A1 { public memberwise init }
struct Z { public memberwise init }
fun h() -> A0 { A0() }
fun h() -> A1 { A1() }
fun g(x0: %s, z: Z) {}
public fun main() { g(h(), h()) }
'''

RANK = '''struct X { public memberwise init }
struct Y { public memberwise init }
struct S {
  public memberwise init
  public static fun a() -> Y { Y() }
  public static fun b() -> X { X() }
}
fun k<V>(x: V, y: V) -> V { x }
fun takeX(x: X) {}
fun takeY(y: Y) {}
fun main() {
  extension S {
    static fun a() -> X { X() }
    static fun b() -> Y { Y() }
  }
  let p = k(S.a(), S.b())
  takeX(p)
  let q = k(S.b(), S.a())
  takeY(q)
}
'''

AMBIGUITY = '''struct X { public memberwise init }
struct Y { public memberwise init }
fun a() -> %s { %s() }
fun a() -> %s { %s() }
fun take%s(x: %s) {}
public fun main() {
  let v = a()
  take%s(v)
}
'''

QUIRKY = '''struct C { public memberwise init }
struct A {
  public memberwise init
  public fun n() -> A { A() }
}
struct B {
  public memberwise init
  public fun n() -> A { A() }
  public fun n() -> A { A() }
}
struct S {
  public memberwise init
  public static fun a() -> C { C() }
}
fun f() -> B { B() }
fun f() -> A { A() }
fun two(x: C, y: A) {}
public fun main() {
  extension S { static fun a() -> C { C() } }
%s}
'''

ALIAS = '''struct A0 { public memberwise init }
struct A1 { public memberwise init }
type X = A1
fun h() -> A0 { A0() }
fun h() -> X { A1() }
fun g(x: A1, y: A1) {}
public fun main() { g(h(), h()) }
'''

# (name, expected after the change, reason, program)
TESTS = [
    # --- must become fast ------------------------------------------------------------------
    ('s01-args-4-8', SAME + '; solver.forks at most 32 with `cleanfirst`',
     'workloads/ovl-4-8.hylo. A wrong candidate fails at its own argument, before the next '
     'overload set is reached; the clean-first pass abandons it there.',
     ovl(4, cyc(4, 8))),
    ('s02-args-last-6', SAME + '; solver.forks at most 24 with `cleanfirst`',
     'The right candidate is the one declared last, the worst order for the existing solver.',
     ovl(4, [3] * 6)),
    ('s03-args-first-6', SAME + '; solver.forks stays 24',
     'The right candidate is declared first: the existing solver is already linear. The '
     'clean-first pass must not add forks.',
     ovl(4, [0] * 6)),
    ('s04-return-3-8', SAME + '; solver.forks at most 24 with `cleanfirst,lookahead` '
     '(unchanged, 9840, with `cleanfirst` alone)',
     'workloads/ovr-3-8.hylo. The candidates differ only in their return type, and a wrong '
     'choice fails at an argument of g, a goal that is popped after every overload set. The '
     'look-ahead sees that pending argument as soon as its type is known.',
     ovr(3, cyc(3, 8))),
    ('s05-return-4-9', SAME + '; solver.forks at most 36 with `cleanfirst,lookahead`',
     'round3/soundness/review2/perf/ovl-ret-9.hylo. Takes about 15 s today: run with a 120 s '
     'limit.',
     ovr(4, cyc(4, 9))),
    ('s06-plus-chain-10', SAME + '; solver.forks at most 10 with `cleanfirst,twins`',
     'Each + on Int has two candidates of the same type (the member of Int and the requirement '
     'of AdditiveArithmetic), and every combination is a solution. Twins share one exploration.',
     plus_chain(10)),
    ('s07-method-chain-6', SAME + '; solver.forks at most 6 with `cleanfirst,twins`',
     'The same situation in user code: a method declared in a struct and required by a trait '
     'that the struct conforms to.',
     METHOD_CHAIN),
    ('s08-mixed-operators', SAME + '; solver.forks at most 8 with `cleanfirst,twins`',
     'Eight operators on Int values, not all in one chain.',
     MIXED),
    ('s09-independent-clean-6', SAME + '; solver.forks unchanged (126)',
     'NOT fixed by this design, recorded so that nobody expects otherwise: six independent sets, '
     'each with two clean candidates of different types. Only solving connected components '
     'separately would help (DESIGN.md, option c).',
     INDEPENDENT),
    # --- erroneous systems: exact fallback -----------------------------------------------------
    ('e01-bad-argument-2', SAME + ' (three diagnostics, two of them ambiguities)',
     'One argument has no matching candidate. The existing solver also reports an ambiguity for '
     'the first call, whose two candidates end with equally bad scores. The clean-first pass '
     'finds no clean candidate and must fall back to the existing search.',
     BAD2 % 'A0'),
    ('e02-bad-argument-2b', SAME + ' (two diagnostics)',
     'As e01, but the first parameter matches the candidate declared last: the existing solver '
     'reports no ambiguity for the first call. Together with e01 this pins the order in which '
     'candidates are tried and scored.',
     BAD2 % 'A1'),
    ('e03-args-bad-6', SAME + '; solver.forks at most 308 (280 today plus the failed attempt)',
     'Six good calls and one bad one. The system has no clean solution, so the existing search '
     'runs after the clean-first pass has failed.',
     ovl(4, [0] * 6, bad=True)),
    ('e04-return-bad-6', SAME + ' (six diagnostics); solver.forks at most 3300 with '
     '`cleanfirst,twins,lookahead`, and at most 6558 (twice today) with `cleanfirst` alone',
     'As e03 for candidates that differ in their return type. Five of the six diagnostics are '
     'ambiguities that exist only because of the order of the search; they must be reproduced.',
     ovr(3, cyc(3, 6), bad=True)),
    ('e05-error-in-both', SAME,
     'review/solver/s01_err_commit.hylo. Both candidates of f lead to an error, in different '
     'places; the one reported depends on the scores of complete solutions.',
     from_file('review/solver/s01_err_commit.hylo')),
    ('e06-literal-tuple', SAME,
     'review/solver/t15_literal_tuple.hylo. Errors that only appear when stale coercions are '
     'turned into equalities, after the fresh goals are exhausted.',
     from_file('review/solver/t15_literal_tuple.hylo')),
    ('e07-literal-as-bool', SAME,
     'review/solver/t16_literal_as_bool.hylo.',
     from_file('review/solver/t16_literal_as_bool.hylo')),
    ('e08-first-binder', SAME,
     'review/solver/verify-S3/v2_as_leak.hylo. The first goal that assigns a type variable '
     'decides which later goal fails and therefore which diagnostic is printed. Any change in '
     'the order in which goals are processed shows here.',
     from_file('review/solver/verify-S3/v2_as_leak.hylo')),
    # --- meaning that must not change ----------------------------------------------------------
    ('m01-rank-nested', SAME + ' (p: X, q: Y)',
     'Both (X, X) and (Y, Y) are clean. The set of the first argument is the outer one and only '
     'the outer set is ranked across both: p is X and q is Y. takeX and takeY make a wrong '
     'choice an error.',
     RANK),
    ('m02-ambiguity-first', SAME + ' (one diagnostic; v: X)',
     'Two clean candidates that are not comparable: an ambiguity is reported and the solution '
     'of the candidate declared first is kept, so takeX(v) is not an error.',
     AMBIGUITY % ('X', 'X', 'Y', 'Y', 'X', 'X', 'X')),
    ('m03-ambiguity-second', SAME + ' (two diagnostics)',
     'As m02 but v is used as a Y: the kept solution is still that of the first candidate, so '
     'the use is a second error.',
     AMBIGUITY % ('X', 'X', 'Y', 'Y', 'Y', 'Y', 'Y')),
    ('m04-preferred-error', SAME + ' (the error of the preferred candidate is reported)',
     'review/solver/t01_quirk_prune.hylo. The preferred candidate of S.f has an error; the other '
     'one has a nested ambiguity, which is a diagnostic but not a counted error. Both stay '
     'viable and the preferred one wins.',
     from_file('review/solver/t01_quirk_prune.hylo')),
    ('m05-preferred-ambiguity', SAME + ' (rejected although S.f -> A is clean)',
     'review/solver/s27_baseline_viable_quirk.hylo. A solution with a nested ambiguity is kept '
     'next to a clean one found earlier, and wins because its candidate is preferred.',
     from_file('review/solver/s27_baseline_viable_quirk.hylo')),
    ('m06-erase-before-clean', SAME + ' (accepted)',
     'f -> B (declared first) has a nested ambiguity, f -> A is clean. Because no clean solution '
     'was known when f -> B was tried, the clean one replaces it. Tests the rule "a solution '
     'found before the first clean one is dropped" of the clean-first pass.',
     QUIRKY % '  let s = S.a()\n  two(s, f().n())\n'),
    ('m07-twin-drop', SAME + ' (rejected, two ambiguities)',
     'The same call as m06, after an overload set S.a with two candidates of the same type. For '
     'the first one, f -> B is dropped as in m06. For the second one a clean solution is already '
     'known, so f -> B stays viable and makes f ambiguous; and the second candidate of S.a is '
     'the preferred one. Tests the rule that a twin may reuse a result of the clean-first pass '
     'only if nothing was dropped while computing it.',
     QUIRKY % '  two(S.a(), f().n())\n'),
    ('m08-where-equality', SAME + ' (accepted)',
     'review/solver/s18_where_eq_reject.hylo. Accepted only if the overload is resolved before '
     'the arguments of k are coerced.',
     from_file('review/solver/s18_where_eq_reject.hylo')),
    ('m09-branch-order', SAME,
     'review/solver/s15_branch_order.hylo.',
     from_file('review/solver/s15_branch_order.hylo')),
    ('m10-outer-ambiguous', SAME + ' (rejected: ambiguous use of a)',
     'review/solver/t02_ambig_flip_accept.hylo.',
     from_file('review/solver/t02_ambig_flip_accept.hylo')),
    ('m11-outer-preferred', SAME + ' (accepted)',
     'review/solver/t03_ambig_flip_reject.hylo.',
     from_file('review/solver/t03_ambig_flip_reject.hylo')),
    ('m12-three-sets', SAME,
     'review/solver/t13_three_sets.hylo.',
     from_file('review/solver/t13_three_sets.hylo')),
    ('m13-overload-priority', SAME,
     'Tests/CompilerTests/positive/overload-priority.hylo, the compiler test that the earlier '
     'attempt changed.',
     open(os.path.join(os.path.dirname(RESEARCH),
                       'Tests/CompilerTests/positive/overload-priority.hylo')).read()),
    ('m14-lookahead-alias', SAME + ' (accepted)',
     'A pending argument whose type is closed and differs from the parameter type as an '
     'identity (X is an alias of A1), but coerces to it. The look-ahead must ask `coerced`, not '
     'compare identities.',
     ALIAS),
    ('m15-literals', SAME,
     'review/solver/t17_literal_valid.hylo.',
     from_file('review/solver/t17_literal_valid.hylo')),
    ('m16-lambdas', SAME,
     'review/solver/s09_lambda.hylo.',
     from_file('review/solver/s09_lambda.hylo')),
    ('m17-where-outer-choice', SAME,
     'review/solver/t19_where_outer_choice.hylo.',
     from_file('review/solver/t19_where_outer_choice.hylo')),
]


def load_results():
    cache = {}
    if os.path.exists(RESULTS):
        for line in open(RESULTS):
            r = json.loads(line)
            cache[(r['sha'], r['config'])] = r
    return cache


def run(path, config, timeout):
    env = dict(os.environ, HYLO_TC_EXPERIMENTS=CONFIGS[config])
    try:
        p = subprocess.run(['timeout', str(timeout), BIN, '--count', path], env=env,
                           capture_output=True, text=True)
    except Exception as e:  # pragma: no cover
        return dict(exit=-1, error=str(e))
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


def wrap(prefix, text, width=96):
    words, lines, cur = text.split(), [], prefix
    for w in words:
        if len(cur) + 1 + len(w) > width and cur.strip('/ ') != prefix.strip('/ '):
            lines.append(cur)
            cur = '//   ' + w
        else:
            cur = cur + ' ' + w
    lines.append(cur)
    return '\n'.join(lines) + '\n'


def main(check):
    cache = load_results()
    os.makedirs(os.path.join(ROOT, 'tests'), exist_ok=True)
    failures = 0
    with open(RESULTS, 'a') as log:
        for name, expected, reason, body in TESTS:
            path = os.path.join(ROOT, 'tests', name + '.hylo')
            sha = hashlib.sha1(body.encode()).hexdigest()[:12]
            # The verdict is measured on the program without its header, written to a scratch
            # file named like the test, so that diagnostics carry the same file name.
            scratch = os.path.join(ROOT, 'results', 'scratch')
            os.makedirs(scratch, exist_ok=True)
            # The header has a fixed number of lines only after wrapping; measure the final file.
            current = {}
            header = (wrap('// expected after the change:', expected)
                      + wrap('// reason:', reason))
            # Two passes: the line numbers of diagnostics depend on the height of the header,
            # which depends on the "currently" comment. Reserve one line per configuration.
            placeholder = '// currently (base): ?\n// currently (FULL): ?\n'
            text = header + placeholder + body
            tmp = os.path.join(scratch, name + '.hylo')
            open(tmp, 'w').write(text)
            for config in CONFIGS:
                key = (sha + ':' + hashlib.sha1(header.encode()).hexdigest()[:8], config)
                if key in cache and not check:
                    r = cache[key]
                else:
                    r = run(tmp, config, 120)
                    r.update(sha=key[0], config=config, test=name)
                    if not check:
                        log.write(json.dumps(r) + '\n')
                        log.flush()
                if check and key in cache:
                    old = cache[key]
                    same = all(old.get(f) == r.get(f) for f in
                               ('exit', 'diagnostics', 'messages', 'counters'))
                    if not same:
                        failures += 1
                        print('DIFFERS', name, config, describe(old), '=>', describe(r))
                current[config] = r
            lines = ''.join('// currently (%s): %s\n' % (c, describe(current[c]))
                            for c in CONFIGS)
            assert lines.count('\n') == 2, name  # keeps the line numbers of the diagnostics
            if not check:
                open(path, 'w').write(header + lines + body)
            print(name, '|', describe(current['base']), '|', describe(current['FULL']))
    return failures


if __name__ == '__main__':
    sys.exit(1 if main('--check' in sys.argv) else 0)
