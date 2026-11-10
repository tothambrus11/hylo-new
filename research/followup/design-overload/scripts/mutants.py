#!/usr/bin/env python3
"""Checks that the random systems of model.py can tell a wrong algorithm from a right one.

Each mutant breaks one clause of the correctness argument of DESIGN.md (section 5). The fuzzer
must find a system on which the mutant differs from the baseline; one such system is printed.

  no-erase        solutions found before the first clean one are kept in `viable`
                  (this is "run the existing solver with best = 0 and accept a clean result")
  trust-nonclean  the result of the optimistic pass is returned even when no candidate is clean
  count-quirks    the look-ahead also counts failures that the solver does not count as errors
  cut-any-bound   the look-ahead cuts on one certain failure whatever the value of `best`
"""
import json
import random
import sys

import model


def first_difference(mutant, n, seed):
    rng = random.Random(seed)
    found = 0
    example = None
    for i in range(n):
        system, pref = model.gen_system(rng)
        b = model.baseline(system, pref, model.Counters())
        p = model.proposed(system, pref, model.Counters(), lookahead=True, mutant=mutant)
        if p != b:
            found += 1
            if example is None or len(repr(system)) < len(example['system']):
                example = dict(index=i, baseline=repr(b), mutant=repr(p), system=repr(system))
    return found, example


if __name__ == '__main__':
    n, seed = int(sys.argv[1]), int(sys.argv[2])
    for m in ['no-erase', 'trust-nonclean', 'count-quirks', 'cut-any-bound']:
        found, example = first_difference(m, n, seed)
        print(json.dumps(dict(mutant=m, systems=n, seed=seed, differing=found, smallest=example)))
