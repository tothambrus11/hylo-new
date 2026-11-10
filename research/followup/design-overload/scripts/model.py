#!/usr/bin/env python3
"""Executable model of the search performed by Solver.swift, and of the proposed speed-up.

The model keeps exactly the parts of the solver that decide which solution is returned:

  * the stack of fresh goals (popped last-in first-out);
  * `current.errors` (E): the number of goals that failed directly;
  * the diagnostics of a solution (D = their number), which is what candidates are scored by;
  * `best`, the cancellation rule `current > best`, the list `viable` with its reset/append
    rule, `minimalElements`, and the "ambiguous use" diagnostic.

Types and unification are abstracted. A goal is either an overload set or a *check* whose
outcome is a function of the types chosen so far.

  ('ovl', name, [(type, pushed), ...])   one pair per candidate, in declaration order. `type`
                                         stands for `NameResolutionCandidate.type`; `pushed` is
                                         the list of goals that the choice adds to the stack.
                                         Two candidates with the same `type` have the same
                                         `pushed` ("twins": they differ only in the declaration
                                         the name is bound to).
  ('chk', id, deps, table, key)          table: tuple of the types chosen for deps
                                           -> 'ok' | 'fail' | 'quirk'
                                         'fail'  : E += 1 and the diagnostic `key`
                                         'quirk' : the diagnostic `key`, E unchanged (a failure
                                                   that the solver does not count)

A solution is (bindings, diagnostics): bindings maps a name to the *index* of the chosen
candidate, diagnostics is a tuple of keys without duplicates.

Algorithms:
  baseline(system, pref, ctr)              Solver.swift as it is
  proposed(system, pref, ctr, ...)         the design of DESIGN.md:
      twins=True       reuse the result of a candidate with the same type (step 1)
      cleanfirst=True  look for the first clean candidate before anything else (step 2)
      lookahead=True   cut a subtree in which a pending goal is certain to fail (step 3)
      bound=True       the counted variant of the look-ahead, in the exact search (step 4)
      mutant=...       a deliberately wrong variant, see mutants.py

  python3 model.py workloads         fork counts for the tc-bench workloads
  python3 model.py fuzz N SEED OUT   compares the algorithms on N random systems
"""
import itertools
import json
import random
import sys
import zlib

INF = 1 << 40


class Counters:
    def __init__(self):
        self.forks = 0
        self.overloads = 0
        self.steps = 0
        self.scans = 0
        self.fallbacks = 0
        self.cuts = 0
        self.reused = 0

    def as_dict(self):
        return dict(forks=self.forks, overloads=self.overloads, steps=self.steps,
                    scans=self.scans, fallbacks=self.fallbacks, cuts=self.cuts,
                    reused=self.reused)


class State:
    __slots__ = ('stack', 'types', 'bindings', 'errors', 'diags', 'dropped')

    def __init__(self, stack, types, bindings, errors, diags):
        self.stack = stack        # list of goals, top of the stack is the end
        self.types = types        # dict name -> type of the chosen candidate
        self.bindings = bindings  # dict name -> index of the chosen candidate
        self.errors = errors      # current.errors
        self.diags = diags        # tuple of diagnostic keys, no duplicates
        self.dropped = False      # proposal only: see _overload2

    def fork(self):
        return State(list(self.stack), dict(self.types), dict(self.bindings), self.errors,
                     self.diags)


def insert(diags, key):
    return diags if key in diags else diags + (key,)


def check(goal, types):
    _, _, deps, table, key = goal
    return table[tuple(types[d] for d in deps)], key


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
    bindings, diags = viable[0][1]
    return (bindings, insert(diags, ('ambiguous', name)))


def step(s, g):
    outcome, key = check(g, s.types)
    if outcome == 'fail':
        s.errors += 1
        s.diags = insert(s.diags, key)
    elif outcome == 'quirk':
        s.diags = insert(s.diags, key)


def choose(s, g, i):
    f = s.fork()
    ty, pushed = g[2][i]
    f.stack.extend(reversed(pushed))
    f.types[g[1]] = ty
    f.bindings[g[1]] = i
    return f


# --- Solver.swift as it is -----------------------------------------------------------------

def baseline(system, pref, ctr):
    return _run(State(list(reversed(system)), {}, {}, 0, ()), INF, pref, ctr)


def _run(s, best, pref, ctr):
    while s.stack:
        g = s.stack.pop()
        ctr.steps += 1
        if g[0] == 'ovl':
            return _overload(s, g, best, pref, ctr)
        step(s, g)
        if s.errors > best:
            return None
    if s.errors > best:
        return None
    return (dict(s.bindings), s.diags)


def _overload(s, g, best, pref, ctr):
    ctr.overloads += 1
    viable = []
    for i in range(len(g[2])):
        ctr.forks += 1
        r = _run(choose(s, g, i), best, pref, ctr)
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
    the current state, because a choice is never revised below the state that made it.
    """
    ctr.scans += 1
    n = 0
    for g in s.stack:
        if g[0] == 'chk' and all(d in s.types for d in g[2]):
            o = check(g, s.types)[0]
            if o == 'fail' or (count_quirks and o == 'quirk'):
                n += 1
    return n


def proposed(system, pref, ctr, cleanfirst=True, twins=True, lookahead=True, bound=False,
             mutant=None):
    cfg = dict(twins=twins, lookahead=lookahead and cleanfirst, bound=bound, mutant=mutant)
    s = State(list(reversed(system)), {}, {}, 0, ())
    return _run2(s, INF, False, cleanfirst, pref, ctr, cfg)


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
            # Exact mode: Solver.swift as it is (plus twins and bounds, which are exact).
            return _overload2(s, g, best, optimistic, pref, ctr, cfg)
        step(s, g)
        if s.errors > best:
            return None
    if s.errors > best:
        return None
    return (dict(s.bindings), s.diags)


def _overload2(s, g, best, optimistic, pref, ctr, cfg):
    mutant = cfg['mutant']
    # Lower bound: every leaf below `s` has at least `errors + certain` errors.
    if (best == 0 or mutant == 'cut-any-bound') and cfg['lookahead']:
        if certain_failures(s, ctr, mutant == 'count-quirks') > 0:
            ctr.cuts += 1
            return None
    elif cfg['bound'] and best < INF:
        if s.errors + certain_failures(s, ctr) > best:
            ctr.cuts += 1
            return None
    ctr.overloads += 1
    viable = []
    memo = {}  # type -> (bound or None if optimistic, pure, result)
    for i in range(len(g[2])):
        ty = g[2][i][0]
        r = None
        reused = False
        if cfg['twins'] and ty in memo:
            m_bound, m_pure, m_result = memo[ty]
            if optimistic:
                # The twin was evaluated by the same procedure from the same state.
                reused = True
            elif m_bound is None:
                # Evaluated optimistically, needed under best == 0: only if nothing was dropped.
                reused = (best == 0 and (m_pure or mutant == 'twins-no-purity'))
            else:
                # Evaluated exactly: same state, same bound, same result.
                reused = (m_bound == best or mutant == 'twins-any-bound')
            if reused:
                ctr.reused += 1
                if m_result is not None:
                    b = dict(m_result[0])
                    b[g[1]] = i
                    r = (b, m_result[1])
        if not reused:
            ctr.forks += 1
            f = choose(s, g, i)
            r = _run2(f, best, optimistic, False, pref, ctr, cfg)
            s.dropped = s.dropped or f.dropped
            memo[ty] = (None if optimistic else best, not f.dropped, r)
        if r is not None:
            score = len(r[1])
            if optimistic:
                # The existing solver has best >= 1 here. A clean solution resets `viable`;
                # any other solution would be erased by that reset, if it ever happens.
                if score == 0:
                    viable = [(i, r)] if mutant != 'no-erase' else viable + [(i, r)]
                    optimistic = False
                else:
                    s.dropped = True
                    if mutant in ('no-erase', 'trust-nonclean'):
                        viable.append((i, r))
            elif score < best:
                best = score
                viable = [(i, r)]
            else:
                viable.append((i, r))
    if optimistic and mutant != 'trust-nonclean':
        return None  # no clean candidate: the caller must not rely on this subtree
    return pick(g, viable, pref)


# --- Workloads ---------------------------------------------------------------------------------

def no_pref(name, a, b):
    return 'eq'


def first_pref(name, a, b):
    """The candidate declared first is preferred (stands for "extension member over requirement")."""
    return 'eq' if a == b else ('asc' if a < b else 'desc')


def table1(k, ok):
    return {(c,): ('ok' if c == ok else 'fail') for c in range(k)}


def ovl(k, pattern, bad=False):
    """g(f(A<p0>()), f(A<p1>()), ...) with f(x: Ai) -> Ai for i < k (workloads/ovl-k-n.hylo).

    A wrong choice for call i fails twice: at the argument of f (before the next overload set)
    and at the argument of g (after the last one). g's coercions are popped last-in first-out.
    With bad=True a last call is added whose value no parameter accepts.
    """
    full = list(pattern) + ([0] if bad else [])
    goals = []
    for i, p in enumerate(full):
        goals.append(('ovl', 'f%d' % i, [(c, []) for c in range(k)]))
        goals.append(('chk', 'arg%d' % i, ('f%d' % i,), table1(k, p), 'arg%d' % i))
    for i in reversed(range(len(full))):
        ok = full[i] if i < len(pattern) else -1
        goals.append(('chk', 'g%d' % i, ('f%d' % i,), table1(k, ok), 'g%d' % i))
    return goals


def ovr(k, pattern, bad=False):
    """g(h(), h(), ...) with h() -> Ai (workloads/ovr-k-n.hylo): a wrong choice fails only at g."""
    n = len(pattern) + (1 if bad else 0)
    goals = []
    for i in range(n):
        goals.append(('ovl', 'h%d' % i, [(c, []) for c in range(k)]))
    for i in reversed(range(n)):
        ok = pattern[i] if i < len(pattern) else -1
        goals.append(('chk', 'g%d' % i, ('h%d' % i,), table1(k, ok), 'g%d' % i))
    return goals


def plus_chain(n):
    """a + a + ... + a with n uses of +: each + has two candidates of the same type, and the set
    of the next + only appears once the type of its left operand is known."""
    def level(i):
        if i == n:
            return []
        pushed = level(i + 1)
        return [('ovl', 'plus%d' % i, [('Int', pushed), ('Int', pushed)])]
    return level(0)


# The steps of the implementation order (DESIGN.md section 7), cumulated.
VARIANTS = [
    ('twins', dict(cleanfirst=False, twins=True, lookahead=False)),
    ('twins+cleanfirst', dict(twins=True, lookahead=False)),
    ('twins+cleanfirst+lookahead', dict(twins=True, lookahead=True)),
    ('twins+cleanfirst+lookahead+bound', dict(twins=True, lookahead=True, bound=True)),
    # Not a step: each of the other two flags without `twins`.
    ('cleanfirst', dict(twins=False, lookahead=False)),
    ('cleanfirst+lookahead', dict(twins=False, lookahead=True)),
]


def measure(name, sysm, pref=no_pref):
    row = {'workload': name}
    c = Counters()
    b = baseline(sysm, pref, c)
    row['diagnostics'] = len(b[1])
    row['baseline'] = dict(forks=c.forks, overloads=c.overloads)
    for label, kw in VARIANTS:
        c = Counters()
        p = proposed(sysm, pref, c, **kw)
        assert p == b, (name, label)
        row[label] = dict(forks=c.forks, overloads=c.overloads, fallbacks=c.fallbacks)
    return row


def workloads():
    cyc = lambda k, n: [i % k for i in range(n)]
    return [
        measure('ovl-4-4', ovl(4, cyc(4, 4))),
        measure('ovl-4-6', ovl(4, cyc(4, 6))),
        measure('ovl-4-8', ovl(4, cyc(4, 8))),
        measure('ovl-8-8', ovl(8, cyc(8, 8))),
        measure('ovr-3-4', ovr(3, cyc(3, 4))),
        measure('ovr-3-6', ovr(3, cyc(3, 6))),
        measure('ovr-3-8', ovr(3, cyc(3, 8))),
        measure('ovl-ret-9', ovr(4, cyc(4, 9))),
        measure('plus-chain-4', plus_chain(4), first_pref),
        measure('plus-chain-8', plus_chain(8), first_pref),
        measure('plus-chain-14', plus_chain(14), first_pref),
    ]


# --- Random systems ----------------------------------------------------------------------------

def gen_system(rng):
    counter = itertools.count()
    domain = {}  # name -> list of the distinct types of its candidates

    def gen_check(avail):
        deps = tuple(rng.sample(avail, min(len(avail), rng.choice([0, 1, 1, 1, 2, 2, 3]))))
        style = rng.choice(['mostly-ok', 'one-ok', 'mixed', 'quirky', 'ok'])

        def cell():
            x = rng.random()
            if style == 'ok':
                return 'ok'
            if style == 'mostly-ok':
                return 'fail' if x < 0.15 else ('quirk' if x < 0.2 else 'ok')
            if style == 'mixed':
                return 'fail' if x < 0.5 else ('quirk' if x < 0.55 else 'ok')
            if style == 'quirky':
                return 'quirk' if x < 0.4 else ('fail' if x < 0.5 else 'ok')
            return 'fail'

        t = {c: cell() for c in itertools.product(*[domain[d] for d in deps])}
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
                k = rng.choice([1, 2, 2, 2, 3, 3, 4])
                domain[name] = list(range(k))
                inner = avail + [name]
                cands = []
                for ty in range(k):
                    if depth < 2 and rng.random() < 0.5:
                        cands.append((ty, gen_goals(inner, depth + 1, budget)))
                    else:
                        cands.append(
                            (ty, [gen_check(inner) for _ in range(rng.choice([0, 0, 1, 1, 2]))]))
                # Twins: repeat some candidates (same type, same consequences) anywhere.
                while rng.random() < 0.35 and len(cands) < 6:
                    cands.insert(rng.randrange(len(cands) + 1), rng.choice(cands))
                goals.append(('ovl', name, cands))
                avail.append(name)
            elif avail or rng.random() < 0.3:
                goals.append(gen_check(avail))
        return goals

    system = gen_goals([], 0, [rng.choice([1, 2, 3, 4, 5, 6])])
    # A preference relation with no structure: possibly not transitive, not even antisymmetric.
    seed = rng.getrandbits(32)
    mode = rng.choice(['none', 'random', 'order', 'order'])

    def pref(name, a, b):
        if a == b or mode == 'none':
            return 'eq'
        if mode == 'order':
            return 'asc' if a < b else 'desc'
        return ['asc', 'desc', 'eq', 'eq'][zlib.crc32(repr((seed, name, a, b)).encode()) % 4]

    return system, pref


def fuzz(n, seed, out):
    rng = random.Random(seed)
    stats = dict(systems=0, with_overloads=0, clean=0, nonclean=0, fallbacks=0, reused=0,
                 cuts=0, mismatches=0, baseline_forks=0, proposed_forks=0)
    for i in range(n):
        system, pref = gen_system(rng)
        cb = Counters()
        b = baseline(system, pref, cb)
        stats['systems'] += 1
        stats['with_overloads'] += cb.overloads > 0
        stats['clean' if len(b[1]) == 0 else 'nonclean'] += 1
        stats['baseline_forks'] += cb.forks
        for label, kw in VARIANTS:
            c = Counters()
            p = proposed(system, pref, c, **kw)
            if label == 'twins+cleanfirst+lookahead':
                stats['fallbacks'] += c.fallbacks
                stats['reused'] += c.reused
                stats['cuts'] += c.cuts
                stats['proposed_forks'] += c.forks
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
