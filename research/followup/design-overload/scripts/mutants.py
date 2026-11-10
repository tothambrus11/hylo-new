#!/usr/bin/env python3
"""Checks that the random systems of model.py can tell a wrong algorithm from a right one.

Each mutant removes one clause of the correctness argument of DESIGN.md (section 5). The fuzzer
must find systems on which the mutant differs from the baseline; the smallest one is recorded.

  no-erase         solutions found before the first clean one are kept in `viable`
  trust-nonclean   the result of the clean-first pass is returned even when no candidate is clean
  count-quirks     the look-ahead also counts failures that the solver does not count as errors
  cut-any-bound    the look-ahead cuts on one certain failure whatever the value of `best`
  twins-no-purity  a result computed by the clean-first pass is reused under best == 0 although
                   a solution was dropped while computing it
  twins-any-bound  in the exact fallback, a result is reused although `best` changed since
  spotless-errors-only  rule T4 (added in review) reuses a result under another bound when no
                   goal failed during its exploration, without requiring that every solution
                   found was clean
  bound0           not a variant of the design but the obvious shortcut: run the existing search
                   with best == 0 from the start and keep its result if it is clean; otherwise
                   run the existing search

  python3 scripts/mutants.py N SEED > results/model-mutants.jsonl
"""
import json
import random
import sys

import model

MUTANTS = ['no-erase', 'trust-nonclean', 'count-quirks', 'cut-any-bound', 'twins-no-purity',
           'twins-any-bound', 'spotless-errors-only', 'bound0']


def bound0(system, pref):
    s = model.State(list(reversed(system)), {}, {}, 0, ())
    r = model._run(s, 0, pref, model.Counters())
    if r is not None and len(r[1]) == 0:
        return r
    return model.baseline(system, pref, model.Counters())


def differences(mutant, n, seed):
    rng = random.Random(seed)
    found = 0
    example = None
    for i in range(n):
        system, pref = model.gen_system(rng)
        b = model.baseline(system, pref, model.Counters())
        if mutant == 'bound0':
            p = bound0(system, pref)
        else:
            # The mutants of rule T4 are run with `twins` alone, where the rule matters most.
            alone = mutant.startswith('spotless')
            p = model.proposed(system, pref, model.Counters(), mutant=mutant,
                               cleanfirst=not alone, lookahead=not alone)
        if p != b:
            found += 1
            if example is None or len(repr(system)) < len(example['system']):
                example = dict(index=i, baseline=repr(b), mutant=repr(p), system=repr(system))
    return found, example


def bound0_counterexample():
    """A system on which `bound0` differs from the baseline. It needs a preference that is not
    transitive: m is preferred to a, a to b, and b and m are not comparable. Candidate a has a
    diagnostic that is not a counted error; b and m are clean.

    Baseline: a is erased when b is found; viable = [b, m]; ambiguity.
    bound0:   nothing is erased; viable = [a, b, m]; a eliminates b, m eliminates a; m wins.
    """
    system = [('ovl', 'o', [('a', [('chk', 1, (), {(): 'quirk'}, 'q')]), ('b', []), ('m', [])])]
    table = {(0, 1): 'asc', (1, 0): 'desc', (2, 0): 'asc', (0, 2): 'desc'}
    pref = lambda name, x, y: table.get((x, y), 'eq')
    b = model.baseline(system, pref, model.Counters())
    z = bound0(system, pref)
    p = model.proposed(system, pref, model.Counters())
    assert p == b and z != b
    return dict(mutant='bound0', explicit_counterexample=repr(system), baseline=repr(b),
                bound0=repr(z), design=repr(p))


if __name__ == '__main__':
    n, seed = int(sys.argv[1]), int(sys.argv[2])
    print(json.dumps(bound0_counterexample()))
    for m in MUTANTS:
        found, example = differences(m, n, seed)
        print(json.dumps(dict(mutant=m, systems=n, seed=seed, differing=found, smallest=example)))
