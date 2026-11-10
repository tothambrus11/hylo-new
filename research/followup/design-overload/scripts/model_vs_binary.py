#!/usr/bin/env python3
"""Compares the model of the existing solver (model.py) with the binary, test by test.

For each test that has a model, the fork count, the number of overload sets and the number of
diagnostics that the model computes for the existing algorithm are compared with what tc-bench
reported (results/tests-current.jsonl, configuration base). The fork counts that the model
predicts for each step of the design are printed next to them.

  python3 scripts/model_vs_binary.py > results/model-vs-binary.jsonl
"""
import json
import os
import sys

import model
from model import ovl, ovr, plus_chain, first_pref, no_pref

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def cyc(k, n):
    return [i % k for i in range(n)]


def second_pref(name, a, b):
    return 'eq' if a == b else ('asc' if a > b else 'desc')


def only(names, pref):
    """`pref` for the sets in `names`, no preference for the others."""
    return lambda name, a, b: pref(name, a, b) if name in names else 'eq'


TWO = [('A', []), ('A', [])]  # a set with two candidates of the same type and no consequence
BAD2 = lambda ok: [
    ('ovl', 'h0', [(0, []), (1, [])]), ('ovl', 'h1', [(0, []), (1, [])]),
    ('chk', 'z', (), {(): 'fail'}, 'z'),
    ('chk', 'x0', ('h0',), {(0,): 'ok' if ok == 0 else 'fail', (1,): 'ok' if ok == 1 else 'fail'},
     'x0')]
F_QUIRKY_FIRST = ('ovl', 'f', [('B', [('ovl', 'n', TWO)]), ('A', [])])

# test -> list of (system, preference); a test with several statements has several systems
MODELS = {
    's01-args-4-8': [(ovl(4, cyc(4, 8)), no_pref)],
    's02-args-last-6': [(ovl(4, [3] * 6), no_pref)],
    's03-args-first-6': [(ovl(4, [0] * 6), no_pref)],
    's04-return-3-8': [(ovr(3, cyc(3, 8)), no_pref)],
    's05-return-4-9': [(ovr(4, cyc(4, 9)), no_pref)],
    's06-plus-chain-10': [(plus_chain(10), first_pref)],
    's07-method-chain-6': [(plus_chain(6), first_pref)],
    's08-mixed-operators': [(plus_chain(8), first_pref)],
    's09-independent-clean-6': [([('ovl', 'a%d' % i, [('Y', []), ('X', [])]) for i in range(6)],
                                second_pref)],
    'e01-bad-argument-2': [(BAD2(0), no_pref)],
    'e02-bad-argument-2b': [(BAD2(1), no_pref)],
    'e03-args-bad-6': [(ovl(4, [0] * 6, bad=True), no_pref)],
    'e04-return-bad-6': [(ovr(3, cyc(3, 6), bad=True), no_pref)],
    'm02-ambiguity-first': [([('ovl', 'a', [('X', []), ('Y', [])])], no_pref)],
    # takeA(S.f().n()): f -> A (member; A.n ambiguous), f -> B (local extension, preferred; error)
    'm04-preferred-error': [([('ovl', 'f', [('A', [('ovl', 'n', TWO)]), ('B', [])]),
                              ('chk', 'take', ('f',), {('A',): 'ok', ('B',): 'fail'}, 'take')],
                             only({'f'}, second_pref))],
    # S.f().n(): f -> A (member, clean), f -> B (local extension, preferred; B.n ambiguous)
    'm05-preferred-ambiguity': [([('ovl', 'f', [('A', []), ('B', [('ovl', 'n', TWO)])])],
                                 only({'f'}, second_pref))],
    # let s = S.a(); two(s, f().n())
    'm06-erase-before-clean': [([('ovl', 'a', [('C', []), ('C', [])])], second_pref),
                               ([F_QUIRKY_FIRST], no_pref)],
    # two(S.a(), f().n())
    'm07-twin-drop': [([('ovl', 'a', [('C', []), ('C', [])]), F_QUIRKY_FIRST],
                       only({'a'}, second_pref))],
}


def binary_results():
    out = {}
    for line in open(os.path.join(ROOT, 'results/tests-current.jsonl')):
        r = json.loads(line)
        if r['config'] == 'base' and r['exit'] == 0:
            out[r['test']] = r
    return out


if __name__ == '__main__':
    binary = binary_results()
    bad = 0
    for name, systems in MODELS.items():
        row = dict(test=name)
        tot = dict(forks=0, overloads=0, diagnostics=0)
        steps = {label: 0 for label, _ in model.VARIANTS}
        for sysm, pref in systems:
            c = model.Counters()
            b = model.baseline(sysm, pref, c)
            tot['forks'] += c.forks
            tot['overloads'] += c.overloads
            tot['diagnostics'] += len(b[1])
            for label, kw in model.VARIANTS:
                c2 = model.Counters()
                assert model.proposed(sysm, pref, c2, **kw) == b, (name, label)
                steps[label] += c2.forks
        r = binary[name]
        got = dict(forks=r['counters'].get('solver.forks', 0),
                   overloads=r['counters'].get('solver.overloads', 0),
                   diagnostics=r['diagnostics'])
        row.update(model_baseline=tot, binary_base=got, agree=(tot == got),
                   model_forks_after=steps)
        bad += tot != got
        print(json.dumps(row))
    sys.exit(1 if bad else 0)
