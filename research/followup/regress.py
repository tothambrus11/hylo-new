"""Regression checks for the mechanisms of the follow-up: expected verdicts under RECJ+selfcheck (the recommended configuration).

usage: regress.py BINID [--config RECJ+selfcheck]"""
import sys, glob, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import tcrun
os.chdir(os.path.dirname(os.path.abspath(__file__)))
B = sys.argv[1]; config = sys.argv[3] if len(sys.argv) > 3 else "RECJ+selfcheck"
# The language designer's answer to "which witness does a requirement get": whichever satisfies the
# whole clause. Without the commit rule (`premcommit`), these programs are accepted, as intended.
JOINT = {'s1-attack-nonminimal-witness', 's1-attack-other-conformance-equality', 's1-attack-shadowed-local-given',
         's1-attack-shadowed-requirement', 's1-attack-shadowed-result-type', 's1-open-ambiguous-dependency',
         's1-reject-other-conformance', 'e07-premise-dropped-closed'}
checks = []
for f in sorted(glob.glob('headsubst/tests/*.hylo')): checks.append((f, 'reject' if 'reject' in f else 'accept'))
for l in open('design-order/tests/MANIFEST.tsv'):
    if l.startswith('#'): continue
    p = l.rstrip('\n').split('\t'); checks.append(('design-order/tests/' + p[0], p[2]))
eng = {n: 'reject' for n in ['s1-attack-capture-recursion-generic', 's1-attack-capture-recursion', 's1-attack-nonminimal-witness',
       's1-attack-other-conformance-equality', 's1-attack-shadowed-local-given', 's1-attack-shadowed-requirement',
       's1-attack-shadowed-result-type-own', 's1-attack-shadowed-result-type', 's1-attack-where-order-b', 's1-open-ambiguous-dependency']}
for f in sorted(glob.glob('design-engine/tests/s1-*.hylo')):
    n = os.path.basename(f)[:-5]; checks.append((f, eng.get(n, 'reject' if 'reject' in n else 'accept')))
REJECT = '''attack-assoc/p/e04-extension-twin-value.hylo attack-assoc/p/e02-extension-twin.hylo attack-assoc/p/c02-capture-value.hylo
attack-assoc/p/a04-nested-scopes.hylo attack-assoc/p/b11-refinement-twin-value.hylo attack-assoc/p/b12-launder-refinement.hylo
attack-assoc/p/a14d-member-alias-value.hylo attack-sigrounds/p/q04-refinement-satisfied-by-itself-value-flow.hylo
attack-sigrounds/p/e01-extension-named-requirement-used-before.hylo metamorphic/judge/progs/alias-args-lost.hylo
reference/hand/self/launder-5.hylo reference/hand/blanket-5.hylo reference/judge/p/u1-confusion.hylo reference/judge/p/u2-b.hylo
attack-premsubst/p/c09b-a7-nested-where.hylo attack-premsubst/p/c08-a7-alias-capture-value.hylo attack-premsubst/p/e07-premise-dropped-closed.hylo
attack-premsubst/p/q01-chain-head-two-witnesses.hylo attack-premsubst/p/v03b-extension-member-result-shadow.hylo
attack-headsubst/p/f02-refinement-value.hylo attack-headsubst/p/s02-extension-member-refinement.hylo
design-eqnorm/tests/keep-01-two-witnesses.hylo'''.split()
ACCEPT = '''attack-assoc/p/r22-method-on-assoc-value.hylo attack-assoc/p/r01-nested-given.hylo attack-assoc/p/r05-trait-calls-extension.hylo
attack-assoc/p/r11-conditional-given-on-assoc.hylo attack-assoc/p/k07-chain-2.hylo attack-assoc/p/e05-extension-concrete.hylo
attack-assoc/p/a01-term-witness.hylo attack-assoc/p/c01v-capture-valid.hylo attack-assoc/p/a14v-member-alias-valid.hylo
usage/benchmarks/rust-flatten.hylo usage/benchmarks/swift-collection-signature.hylo usage/benchmarks/swift-string-protocol.hylo
usage/benchmarks/swift-transitive-parameters.hylo attack-sigrounds/p/a01-ext-where-uses-member-alias.hylo
attack-sigrounds/p/a06-ext-where-member-alias-self-plain-requirement.hylo attack-premsubst/p/q01c-chain-head-one-witness.hylo
attack-premsubst/p/u02-same-type-twice.hylo attack-premsubst/p/u01b-order-same-type-reject.hylo attack-premsubst/p/n04-method-own-parameter.hylo
attack-premsubst/p/a08-mentioned-by-coercion.hylo attack-premsubst/p/e05-generic-conformance-projection.hylo attack-premsubst/p/t02-trait-nested-given-bound.hylo
attack-headsubst/p/k07-function-value-shadow.hylo attack-headsubst/p/r01-regress-recursion-equality.hylo attack-headsubst/p/d01-equality-nested-arg.hylo
design-eqnorm/tests/gain-01-wide-given.hylo design-eqnorm/tests/attack-01-alias-given-skipped-by-index.hylo design-eqnorm/tests/attack-04-budget-beyond-depth.hylo'''.split()
checks += [(f, 'reject') for f in REJECT] + [(f, 'accept') for f in ACCEPT]
bad = 0
joint = 'premcommit' not in tcrun.flags(config).split(',')
for f, e in checks:
    if joint and os.path.basename(f)[:-5] in JOINT: e = 'accept'
    r = tcrun.run(B, config, f, 180)
    if r['verdict'] != e or r['violations']:
        bad += 1; print('BAD', f, 'expected', e, 'got', r['verdict'], (r['violations'] or r['errors'] or [''])[0][:140])
print(len(checks), 'checks,', bad, 'bad')
