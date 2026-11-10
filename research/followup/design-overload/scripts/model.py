#!/usr/bin/env python3
"""Executable model of the search performed by Solver.swift, and of the proposed speed-up.

The model keeps exactly the parts of the solver that decide which solution is returned:

  * the stack of fresh goals (popped last-in first-out);
  * `current.errors` (E): the number of goals that failed directly;
  * the diagnostics of a solution (D = their number), which is what candidates are scored by;
  * `best`, the cancellation rule `current > best`, the list `viable` with its reset/append
    rule, `minimalElements`, and the "ambiguous use" diagnostic.

Types and unification are abstracted: a goal is either an overload set or a *check* whose
outcome is a function of the choices made so far.

  ('ovl', name, [candidate, ...])   candidate = list of goals pushed when it is chosen
  ('chk', id, deps, table, key)     table: tuple of the choices of deps -> 'ok' | 'fail' | 'quirk'
                                    'fail'  : E += 1 and one diagnostic `key`
                                    'quirk' : one diagnostic `key`, E unchanged (a failure that the
                                              solver does not count, e.g. a stale coercion that
                                              cannot be simplified, section 2.4 of DESIGN.md)

Three algorithms:
  baseline(system)                 Solver.swift as it is
  proposed(system, lookahead=..)   clean-first search with exact fallback (DESIGN.md section 4)
  with bound=True                  additionally, the counted lower bound in exact mode (step 3)

`python3 model.py workloads` reproduces the fork counts of the tc-bench workloads.
`python3 model.py fuzz N SEED`   compares the algorithms on N random systems.
"""
import itertools
import json
import random
import sys

INF = 1 << 40


class Counters:
    def __init__(self):
        self.forks = 0
        self.overloads = 0
        self.steps = 0
        self.scans = 0
        self.fallbacks = 0
        self.cuts = 0

    def as_dict(self):
        return dict(forks=self.forks, overloads=self.overloads, steps=self.steps,
                    scans=self.scans, fallbacks=self.fallbacks, cuts=self.cuts)


class State:
    __slots__ = ('stack', 'choices', 'errors', 'diags')

    def __init__(self, stack, choices, errors, diags):
        self.stack = stack      # list of goals, top of the stack is the end
        self.choices = choices  # dict name -> candidate index
        self.errors = errors    # current.errors
        self.diags = diags      # tuple of diagnostic keys in insertion order, without duplicates

    def fork(self):
        return State(list(self.stack), dict(self.choices), self.errors, self.diags)


def insert(diags, key):
    return diags if key in diags else diags + (key,)


def check(goal, choices):
    _, _, deps, table, key = goal
    return table[tuple(choices[d] for d in deps)], key


def minimal_elements(xs, compare):
    """Sequence.minimalElements(by:) of Sources/Utilities/Sequence+Extensions.swift."""
    leaves = []
    for x in xs:
        if len(leaves) == 1:
            c = compare(leaves[0], x)
            if c == 'asc':
                continue
            if c == 'eq':
                leaves.append(x)
                continue
        if all(compare(x, y) == 'asc' for y in leaves):
            leaves = [x]
        else:
            leaves.append(x)
    return leaves


def pick(goal, viable, pref):
    """The end of solve(overload:among:): the preferred viable solution, or an ambiguity."""
    name = goal[1]
    if not viable:
        return None
    least = minimal_elements(viable, lambda a, b: pref(name, a[0], b[0]))
    if len(least) == 1:
        return least[0][1]
    choices, diags = viable[0][1]
    return (choices, insert(diags, ('ambiguous', name)))


# --- Solver.swift as it is -----------------------------------------------------------------

def baseline(system, pref, ctr):
    return _run(State(list(reversed(system)), {}, 0, ()), INF, pref, ctr)


def _run(s, best, pref, ctr):
    while s.stack:
        g = s.stack.pop()
        ctr.steps += 1
        if g[0] == 'ovl':
            return _overload(s, g, best, pref, ctr)
        outcome, key = check(g, s.choices)
        if outcome == 'fail':
            s.errors += 1
            s.diags = insert(s.diags, key)
        elif outcome == 'quirk':
            s.diags = insert(s.diags, key)
        if s.errors > best:
            return None
    if s.errors > best:
        return None
    return (dict(s.choices), s.diags)


def _overload(s, g, best, pref, ctr):
    ctr.overloads += 1
    viable = []
    for i, pushed in enumerate(g[2]):
        ctr.forks += 1
        f = s.fork()
        f.stack.extend(reversed(pushed))
        f.choices[g[1]] = i
        r = _run(f, best, pref, ctr)
        if r is not None:
            score = len(r[1])
            if score < best:
                best = score
                viable = [(i, r)]
            else:
                viable.append((i, r))
    return pick(g, viable, pref)


# --- The proposal ----------------------------------------------------------------------------

def certain_failures(s, ctr, count_quirks=False):
    """The number of pending checks that fail whatever the remaining choices are.

    A pending check whose dependencies are all chosen has the same outcome in every leaf below
    the current state (choices are never revised below a state).
    """
    ctr.scans += 1
    n = 0
    for g in s.stack:
        if g[0] == 'chk' and all(d in s.choices for d in g[2]):
            o = check(g, s.choices)[0]
            if o == 'fail' or (count_quirks and o == 'quirk'):
                n += 1
    return n


def proposed(system, pref, ctr, lookahead=True, bound=False, mutant=None):
    """`mutant` selects a deliberately wrong variant; see scripts/mutants.py."""
    cfg = dict(lookahead=lookahead, bound=bound, mutant=mutant)
    return _run2(State(list(reversed(system)), {}, 0, ()), INF, False, True, pref, ctr, cfg)


def _run2(s, best, optimistic, may_try, pref, ctr, cfg):
    """`optimistic` implies `best == 0`: the caller is looking for the first clean candidate."""
    while s.stack:
        g = s.stack.pop()
        ctr.steps += 1
        if g[0] == 'ovl':
            if may_try and s.errors == 0:
                # First overload set of the system: clean-first attempt on a copy.
                r = _overload2(s.fork(), g, 0, True, pref, ctr, cfg)
                if r is not None:
                    return r
                ctr.fallbacks += 1
                # Exact fallback: Solver.swift as it is (plus the optional counted bound).
            return _overload2(s, g, best, optimistic, pref, ctr, cfg)
        outcome, key = check(g, s.choices)
        if outcome == 'fail':
            s.errors += 1
            s.diags = insert(s.diags, key)
        elif outcome == 'quirk':
            s.diags = insert(s.diags, key)
        if s.errors > best:
            return None
    if s.errors > best:
        return None
    return (dict(s.choices), s.diags)


def _overload2(s, g, best, optimistic, pref, ctr, cfg):
    # Lower bound: every leaf below `s` has at least `errors + certain` errors.
    if (best == 0 or cfg['mutant'] == 'cut-any-bound') and cfg['lookahead']:
        if certain_failures(s, ctr, cfg['mutant'] == 'count-quirks') > 0:
            ctr.cuts += 1
            return None
    elif cfg['bound'] and best < INF:
        if s.errors + certain_failures(s, ctr) > best:
            ctr.cuts += 1
            return None
    ctr.overloads += 1
    viable = []
    for i, pushed in enumerate(g[2]):
        ctr.forks += 1
        f = s.fork()
        f.stack.extend(reversed(pushed))
        f.choices[g[1]] = i
        r = _run2(f, best, optimistic, False, pref, ctr, cfg)
        if r is not None:
            score = len(r[1])
            if optimistic:
                # The baseline's `best` is at least 1 here. A clean solution resets `viable`;
                # any other solution would be erased by that reset, if it ever happens.
                if score == 0:
                    viable = [(i, r)] if cfg['mutant'] != 'no-erase' else viable + [(i, r)]
                    optimistic = False
                elif cfg['mutant'] in ('no-erase', 'trust-nonclean'):
                    viable.append((i, r))
            elif score < best:
                best = score
                viable = [(i, r)]
            else:
                viable.append((i, r))
    if optimistic and cfg['mutant'] != 'trust-nonclean':
        return None  # no clean candidate: the caller must not rely on this subtree
    return pick(g, viable, pref)


# --- Workloads ---------------------------------------------------------------------------------

def no_pref(name, a, b):
    return 'eq'


def table(deps_sizes, f):
    return {t: f(*t) for t in itertools.product(*[range(k) for k in deps_sizes])}


def ovl(k, n):
    """workloads/ovl-k-n.hylo: g(f(A0()), f(A1()), ...), f(x: Ai) -> Ai.

    A wrong choice for call i fails twice: at the argument of f (before the next overload set)
    and at the argument of g (after the last one). g's coercions are popped last-in first-out.
    """
    goals = []
    for i in range(n):
        goals.append(('ovl', 'f%d' % i, [[] for _ in range(k)]))
        goals.append(('chk', 'arg%d' % i, ('f%d' % i,),
                      table([k], lambda c, i=i: 'ok' if c == i % k else 'fail'), 'arg%d' % i))
    for i in reversed(range(n)):
        goals.append(('chk', 'g%d' % i, ('f%d' % i,),
                      table([k], lambda c, i=i: 'ok' if c == i % k else 'fail'), 'g%d' % i))
    return goals


def ovr(k, n):
    """workloads/ovr-k-n.hylo: g(h(), h(), ...), h() -> Ai. A wrong choice fails only at g."""
    goals = []
    for i in range(n):
        goals.append(('ovl', 'h%d' % i, [[] for _ in range(k)]))
    for i in reversed(range(n)):
        goals.append(('chk', 'g%d' % i, ('h%d' % i,),
                      table([k], lambda c, i=i: 'ok' if c == i % k else 'fail'), 'g%d' % i))
    return goals


def workloads():
    rows = []
    for name, sysm in [('ovl-4-4', ovl(4, 4)), ('ovl-4-6', ovl(4, 6)), ('ovl-4-8', ovl(4, 8)),
                       ('ovl-8-8', ovl(8, 8)),
                       ('ovr-3-4', ovr(3, 4)), ('ovr-3-6', ovr(3, 6)), ('ovr-3-8', ovr(3, 8)),
                       ('ovl-ret-9', ovr(4, 9))]:
        row = {'workload': name}
        c = Counters()
        b = baseline(sysm, no_pref, c)
        row['baseline'] = c.as_dict()
        for label, kw in [('cleanfirst', dict(lookahead=False)),
                          ('cleanfirst+lookahead', dict(lookahead=True))]:
            c = Counters()
            p = proposed(sysm, no_pref, c, **kw)
            assert p == b, name
            row[label] = c.as_dict()
        rows.append(row)
    return rows


# --- Random systems ----------------------------------------------------------------------------

def gen_system(rng):
    counter = itertools.count()
    sizes = {}

    def gen_check(avail):
        deps = tuple(rng.sample(avail, min(len(avail), rng.choice([0, 1, 1, 1, 2, 2, 3]))))
        style = rng.choice(['mostly-ok', 'one-ok', 'mixed', 'quirky'])

        def cell():
            x = rng.random()
            if style == 'mostly-ok':
                return 'fail' if x < 0.15 else ('quirk' if x < 0.2 else 'ok')
            if style == 'mixed':
                return 'fail' if x < 0.5 else ('quirk' if x < 0.55 else 'ok')
            if style == 'quirky':
                return 'quirk' if x < 0.4 else ('fail' if x < 0.5 else 'ok')
            return 'fail'

        t = {c: cell() for c in itertools.product(*[range(sizes[d]) for d in deps])}
        if style == 'one-ok' and t:
            t[rng.choice(list(t))] = 'ok'
        cid = next(counter)
        # Some checks share a diagnostic, so that D < E happens (DiagnosticSet removes duplicates).
        key = ('shared', rng.randrange(3)) if rng.random() < 0.1 else ('chk', cid)
        return ('chk', cid, deps, t, key)

    def gen_goals(avail, depth, budget):
        goals = []
        avail = list(avail)
        for _ in range(rng.choice([1, 2, 2, 3, 3, 4, 5])):
            if budget[0] > 0 and rng.random() < (0.55 if depth == 0 else 0.3):
                budget[0] -= 1
                name = 'o%d' % next(counter)
                k = rng.choice([2, 2, 2, 3, 3, 4])
                sizes[name] = k
                inner = avail + [name]
                cands = []
                for _ in range(k):
                    if depth < 2 and rng.random() < 0.5:
                        cands.append(gen_goals(inner, depth + 1, budget))
                    else:
                        cands.append([gen_check(inner) for _ in range(rng.choice([0, 0, 1, 1, 2]))])
                goals.append(('ovl', name, cands))
                avail.append(name)
            elif avail or rng.random() < 0.3:
                goals.append(gen_check(avail))
        return goals

    system = gen_goals([], 0, [rng.choice([1, 2, 3, 4, 5, 6])])
    # A preference relation with no structure: possibly not transitive, not even antisymmetric.
    seed = rng.getrandbits(32)
    mode = rng.choice(['none', 'random', 'order'])

    def pref(name, a, b):
        if a == b or mode == 'none':
            return 'eq'
        if mode == 'order':
            return 'asc' if a > b else 'desc'
        return random.Random(hash((seed, name, a, b))).choice(['asc', 'desc', 'eq', 'eq'])

    return system, pref


def fuzz(n, seed, out):
    rng = random.Random(seed)
    stats = dict(systems=0, clean=0, nonclean=0, none=0, fallbacks=0, mismatches=0,
                 baseline_forks=0, proposed_forks=0, with_overloads=0)
    for i in range(n):
        system, pref = gen_system(rng)
        cb = Counters()
        b = baseline(system, pref, cb)
        results = {}
        for label, kw in [('cleanfirst', dict(lookahead=False)),
                          ('lookahead', dict(lookahead=True)),
                          ('lookahead+bound', dict(lookahead=True, bound=True))]:
            c = Counters()
            results[label] = (proposed(system, pref, c, **kw), c)
        stats['systems'] += 1
        stats['with_overloads'] += cb.overloads > 0
        if b is None:
            stats['none'] += 1
        elif len(b[1]) == 0:
            stats['clean'] += 1
        else:
            stats['nonclean'] += 1
        stats['fallbacks'] += results['lookahead'][1].fallbacks
        stats['baseline_forks'] += cb.forks
        stats['proposed_forks'] += results['lookahead'][1].forks
        for label, (p, c) in results.items():
            if p != b:
                stats['mismatches'] += 1
                out.write(json.dumps(dict(seed=seed, index=i, variant=label, baseline=repr(b),
                                          proposed=repr(p), system=repr(system))) + '\n')
    return stats


if __name__ == '__main__':
    if sys.argv[1] == 'workloads':
        for row in workloads():
            print(json.dumps(row))
    elif sys.argv[1] == 'fuzz':
        n, seed = int(sys.argv[2]), int(sys.argv[3])
        with open(sys.argv[4] if len(sys.argv) > 4 else '/dev/stdout', 'a') as out:
            stats = fuzz(n, seed, out)
            out.write(json.dumps(dict(seed=seed, summary=stats)) + '\n')
