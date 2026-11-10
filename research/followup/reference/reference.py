"""Reference resolver for the fragment specified in spec.md.

The code follows the specification rule by rule and favours clarity over speed. It works on an
abstract representation of problems, not on Hylo source text.

Abstract representation
-----------------------
Types are nested tuples:

    ("var", name)              a generic parameter (rigid in a query, a pattern variable in a
                               conformance declaration)
    ("app", head, (t1,...,tn)) a nominal type applied to n >= 0 arguments; a tuple type of n
                               elements is written with the head "{n}"
    ("proj", base, trait)      the associated type of `trait` on `base` (source form `base.X`);
                               each trait has at most one associated type
    ("atom", name)             internal: an associated type through a where-clause requirement

A world is a dict:

    traits:  {name: assoc}                 assoc is the associated type's name or None
    structs: {name: arity}
    confs:   [conformance declaration]     {"params": [names], "premises": [requirement],
                                            "type": type, "trait": name, "impl": type or None}
    queries: [query]                       {"params": [names], "reqs": [requirement],
                                            "goal": goal}

A requirement is ("conf", type, trait) or ("eq", type, type).
A goal is ("conf", type, trait), ("eq", type, type) or ("coerce", type, type).

Answers
-------
`answer(world, query)` returns a dict with, among others:

    verdict     "derivable" | "underivable" | "illformed-goal" | "unspecified"
    count       number of distinct derivations of a conformance goal, capped at CAP
    size        number of rule applications in a smallest conformance derivation (0 for equalities)
    eq_needed   smallest number of equality requirements with which the goal is still derivable
    congruence  True if the goal is not derivable when the congruence rule is removed
    sem         the same question in the theory with injectivity and conflict (an upper bound on
                what any sound checker may accept): "valid" | "invalid" | "vacuous"
    ordered     True if each requirement of the where clause only mentions associated types that
                denote a type in the scope formed by the requirements written before it
"""

import itertools
import json

CAP = 3          # derivation counts are capped at this value
DEPTH = 12       # bound on the height of conformance derivations


class IllFormed(Exception):
    """A projection `t.X` that does not denote a type (rule PROJ of the specification)."""


class Unspecified(Exception):
    """The specification does not determine the meaning of the problem."""


# --------------------------------------------------------------------------------------------
# Terms


def var(n):
    return ("var", n)


def app(h, *args):
    return ("app", h, tuple(args))


def proj(base, trait):
    return ("proj", base, trait)


def subterms(t):
    yield t
    if t[0] == "app":
        for a in t[2]:
            yield from subterms(a)
    elif t[0] == "proj":
        yield from subterms(t[1])


def variables(t):
    return {s[1] for s in subterms(t) if s[0] == "var"}


def has_proj(t):
    return any(s[0] == "proj" for s in subterms(t))


def substitute(t, s):
    """Replaces the variables of `t` according to the dict `s` (variable name -> term)."""
    if t[0] == "var":
        return s.get(t[1], t)
    if t[0] == "app":
        return ("app", t[1], tuple(substitute(a, s) for a in t[2]))
    if t[0] == "proj":
        return ("proj", substitute(t[1], s), t[2])
    return t


def term_size(t):
    return sum(1 for _ in subterms(t))


def show(t):
    if t[0] == "var":
        return t[1]
    if t[0] == "atom":
        return "<" + t[1] + ">"
    if t[0] == "proj":
        return show(t[1]) + "." + t[2] + "::X"
    if t[1].startswith("{"):
        return "{" + ", ".join(show(a) for a in t[2]) + "}"
    return t[1] + ("<" + ", ".join(show(a) for a in t[2]) + ">" if t[2] else "")


def to_tuple(x):
    """Converts the JSON form (nested lists) to nested tuples."""
    if isinstance(x, list):
        return tuple(to_tuple(y) for y in x)
    return x


def load_world(d):
    return {
        "traits": dict(d["traits"]),
        "structs": dict(d["structs"]),
        "confs": [
            {"params": list(c["params"]), "premises": [to_tuple(p) for p in c["premises"]],
             "type": to_tuple(c["type"]), "trait": c["trait"],
             "impl": to_tuple(c["impl"]) if c.get("impl") is not None else None}
            for c in d["confs"]],
        "queries": [
            {"params": list(q["params"]), "reqs": [to_tuple(r) for r in q["reqs"]],
             "goal": to_tuple(q["goal"])}
            for q in d["queries"]],
    }


# --------------------------------------------------------------------------------------------
# Equality theory: congruence closure (rules REFL, SYM, TRANS, FACT and CONG of the specification)


class EGraph:
    """The equivalence classes of a set of projection-free terms under a set of ground equations.

    The implementation is the textbook one, without any optimization: after every change, the
    congruence rule is applied until nothing changes.
    """

    def __init__(self, congruence=True):
        self.congruence = congruence
        self.terms = []      # id -> term
        self.ids = {}        # term -> id
        self.parent = []     # union-find

    def find(self, i):
        while self.parent[i] != i:
            i = self.parent[i]
        return i

    def add(self, t):
        """Returns the identifier of `t`, adding `t` and its subterms if necessary."""
        assert t[0] in ("var", "app", "atom"), t
        if t in self.ids:
            return self.ids[t]
        if t[0] == "app":
            for a in t[2]:
                self.add(a)
        i = len(self.terms)
        self.terms.append(t)
        self.ids[t] = i
        self.parent.append(i)
        self.close()
        return i

    def merge(self, a, b):
        """Adds the equation a == b (rule FACT)."""
        i, j = self.find(self.add(a)), self.find(self.add(b))
        if i != j:
            self.parent[max(i, j)] = min(i, j)
            self.close()

    def close(self):
        """Applies rule CONG until nothing changes: two applications of the same constructor to
        pairwise equal arguments are equal."""
        if not self.congruence:
            return
        changed = True
        while changed:
            changed = False
            table = {}
            for i, t in enumerate(self.terms):
                if t[0] != "app":
                    continue
                k = (t[1], tuple(self.find(self.ids[a]) for a in t[2]))
                j = table.setdefault(k, i)
                ri, rj = self.find(i), self.find(j)
                if ri != rj:
                    self.parent[max(ri, rj)] = min(ri, rj)
                    changed = True

    def cls(self, t):
        return self.find(self.add(t))

    def equal(self, a, b):
        return self.cls(a) == self.cls(b)

    def members(self, c):
        c = self.find(c)
        return [t for i, t in enumerate(self.terms) if self.find(i) == c]

    def representative(self, c):
        """A smallest member of the class `c` (any member would do)."""
        return min(self.members(c), key=lambda t: (term_size(t), repr(t)))

    def ematch(self, pattern, c, params, s):
        """Yields the extensions of `s` (parameter -> class) under which `pattern` is a member of
        class `c` up to the theory (rule INST of the specification: matching modulo equality)."""
        c = self.find(c)
        if not (variables(pattern) & set(params)):
            if self.cls(pattern) == c:
                yield s
            return
        if pattern[0] == "var":
            p = pattern[1]
            if p in s:
                if self.find(s[p]) == c:
                    yield s
            else:
                yield {**s, p: c}
            return
        assert pattern[0] == "app", pattern
        for t in self.members(c):
            if t[0] == "app" and t[1] == pattern[1] and len(t[2]) == len(pattern[2]):
                yield from self._ematch_list(pattern[2], [self.cls(a) for a in t[2]], params, s)

    def _ematch_list(self, patterns, classes, params, s):
        if not patterns:
            yield s
            return
        for s1 in self.ematch(patterns[0], classes[0], params, s):
            yield from self._ematch_list(patterns[1:], classes[1:], params, s1)


# --------------------------------------------------------------------------------------------
# A scope: the givens visible from the body of one query function


class Scope:
    """The equality theory and the conformance givens of one query (section 3 of the spec)."""

    def __init__(self, world, reqs, congruence=True, check_stability=True):
        self.world = world
        self.eg = EGraph(congruence)
        self.conf_reqs = []        # (requirement index, trait, elaborated type)
        self.memo = {}
        self.bounded = False       # True if the depth bound cut a search
        self.elaborated = {}       # requirement index -> elaborated requirement
        self.order = []            # the order in which the requirements entered the scope

        # Staged elaboration of the where clause (rule SCOPE): a requirement enters the scope as
        # soon as the projections it mentions denote types in the scope built so far.
        pending = list(enumerate(reqs))
        progress = True
        while pending and progress:
            progress = False
            for i, r in list(pending):
                try:
                    e = self.elaborate_requirement(r)
                except IllFormed:
                    continue
                pending.remove((i, r))
                self.enter(i, e)
                progress = True
        if pending:
            raise Unspecified("a requirement mentions a projection that denotes no type")

        # The meaning of a requirement must not depend on the stage at which it was elaborated.
        if check_stability:
            for i, r in enumerate(reqs):
                try:
                    e = self.elaborate_requirement(r)
                except IllFormed:
                    raise Unspecified("projection in requirement %d is ambiguous in the full scope" % i)
                f = self.elaborated[i]
                if not (self.eg.equal(e[1], f[1]) and (e[0] == "conf" or self.eg.equal(e[2], f[2]))):
                    raise Unspecified("projection in requirement %d changes meaning" % i)

    def enter(self, i, e):
        self.elaborated[i] = e
        self.order.append(i)
        self.memo = {}
        if e[0] == "eq":
            self.eg.merge(e[1], e[2])
        else:
            self.eg.add(e[1])
            self.conf_reqs.append((i, e[2], e[1]))

    # ---- associated types (section 5 of the specification)

    def elaborate_requirement(self, r):
        if r[0] == "conf":
            return ("conf", self.elaborate(r[1]), r[2])
        return ("eq", self.elaborate(r[1]), self.elaborate(r[2]))

    def elaborate(self, t):
        """Replaces every projection in `t` by the type it denotes (rules PROJ-REQ, PROJ-DECL)."""
        if t[0] == "app":
            return ("app", t[1], tuple(self.elaborate(a) for a in t[2]))
        if t[0] != "proj":
            return t
        base = self.elaborate(t[1])
        trait = t[2]
        if self.world["traits"].get(trait) is None:
            raise IllFormed("trait has no associated type")
        d = self.select(trait, base)
        if d[0] == "req":
            return ("atom", "r%d" % d[1])
        c = self.world["confs"][d[1]]
        if c["impl"] is None:
            raise IllFormed("conformance declares no implementation")
        s = {p: self.eg.representative(k) for p, k in d[2]}
        return substitute(c["impl"], s)

    def select(self, trait, base):
        """The derivation that a projection on `base` goes through (rule SELECT)."""
        ds = self.derivations(trait, self.eg.cls(base), DEPTH)
        if len(ds) == 1:
            return ds[0]
        if not ds:
            raise IllFormed("no conformance")
        # Rule DIRECT (a guess, see the open questions): a requirement stated on exactly this
        # type wins over derivations that need a coercion or a declaration.
        direct = [("req", i) for (i, tr, ty) in self.conf_reqs if tr == trait and ty == base]
        if len(direct) == 1:
            return direct[0]
        raise IllFormed("ambiguous conformance")

    # ---- conformance (section 4 of the specification)

    def derivations(self, trait, c, depth):
        """Up to CAP distinct derivations of `trait<t>` for the types `t` of class `c`, of height
        at most `depth`. A derivation is ("req", i) or ("conf", j, bindings, premises)."""
        c = self.eg.find(c)
        key = (trait, c, depth)
        if key in self.memo:
            return self.memo[key]
        if depth == 0:
            self.bounded = True
            return []
        out = []
        # Rule REQ: a where-clause requirement on a type equal to the goal's type.
        for (i, tr, ty) in self.conf_reqs:
            if tr == trait and self.eg.cls(ty) == c:
                out.append(("req", i))
        # Rule DECL: an instance of a conformance declaration whose head is equal to the goal and
        # whose premises are derivable.
        for j, d in enumerate(self.world["confs"]):
            if d["trait"] != trait:
                continue
            seen = set()
            for s in list(self.eg.ematch(d["type"], c, d["params"], {})):
                b = tuple(sorted((p, self.eg.find(k)) for p, k in s.items()))
                if b in seen or len(b) != len(d["params"]):
                    continue
                seen.add(b)
                for ps in self.premises(d, dict(b), depth - 1):
                    out.append(("conf", j, b, ps))
                    if len(out) >= CAP:
                        break
        out = out[:CAP]
        self.memo[key] = out
        return out

    def premises(self, d, s, depth):
        """Yields the tuples of derivations of the conformance premises of `d` under `s`; nothing
        if an equality premise does not hold."""
        rep = {p: self.eg.representative(k) for p, k in s.items()}
        choices = []
        for pr in d["premises"]:
            if pr[0] == "eq":
                if not self.eg.equal(substitute(pr[1], rep), substitute(pr[2], rep)):
                    return
            else:
                ds = self.derivations(pr[2], self.eg.cls(substitute(pr[1], rep)), depth)
                if not ds:
                    return
                choices.append(ds)
        yield from itertools.product(*choices)

    def min_size(self, trait, c, depth=DEPTH):
        """The number of rule applications in a smallest derivation, or None."""
        c = self.eg.find(c)
        key = ("size", trait, c, depth)
        if key in self.memo:
            return self.memo[key]
        best = None
        if depth > 0:
            for (i, tr, ty) in self.conf_reqs:
                if tr == trait and self.eg.cls(ty) == c:
                    best = 1
            for d in self.world["confs"]:
                if d["trait"] != trait:
                    continue
                for s in list(self.eg.ematch(d["type"], c, d["params"], {})):
                    if len(s) != len(d["params"]):
                        continue
                    rep = {p: self.eg.representative(k) for p, k in s.items()}
                    total = 1
                    for pr in d["premises"]:
                        if pr[0] == "eq":
                            if not self.eg.equal(substitute(pr[1], rep), substitute(pr[2], rep)):
                                total = None
                        else:
                            n = self.min_size(pr[2], self.eg.cls(substitute(pr[1], rep)), depth - 1)
                            total = None if n is None else total + n
                        if total is None:
                            break
                    if total is not None and (best is None or total < best):
                        best = total
        self.memo[key] = best
        return best

    # ---- goals

    def decide(self, goal):
        """Returns (derivable, count, size) for an elaborated goal."""
        if goal[0] == "conf":
            c = self.eg.cls(goal[1])
            ds = self.derivations(goal[2], c, DEPTH)
            return (bool(ds), len(ds), self.min_size(goal[2], c))
        return (self.eg.equal(goal[1], goal[2]), None, 0)


# --------------------------------------------------------------------------------------------
# The upper bound: injectivity and conflict (section 6 of the specification)


def unify(equations):
    """Most general unifier of `equations` over free constructors, where variables and atoms may
    be instantiated; returns a dict or None if there is no unifier."""
    s = {}

    def walk(t):
        while t[0] in ("var", "atom") and t in s:
            t = s[t]
        return t

    def occurs(v, t):
        t = walk(t)
        if t == v:
            return True
        return t[0] == "app" and any(occurs(v, a) for a in t[2])

    work = list(equations)
    while work:
        a, b = work.pop()
        a, b = walk(a), walk(b)
        if a == b:
            continue
        if a[0] in ("var", "atom"):
            if occurs(a, b):
                return None
            s[a] = b
        elif b[0] in ("var", "atom"):
            work.append((b, a))
        elif a[1] == b[1] and len(a[2]) == len(b[2]):
            work.extend(zip(a[2], b[2]))
        else:
            return None

    def resolve(t):
        t = walk(t)
        if t[0] == "app":
            return ("app", t[1], tuple(resolve(x) for x in t[2]))
        return t

    return {k: resolve(v) for k, v in s.items()}, resolve


def semantic(world, reqs_elaborated, goal_elaborated):
    """Decides the elaborated goal in the theory of free constructors: "vacuous" if the equality
    requirements have no solution, else "valid" or "invalid"."""
    u = unify([(r[1], r[2]) for r in reqs_elaborated if r[0] == "eq"])
    if u is None:
        return "vacuous"
    _, resolve = u
    reqs = [("conf", resolve(r[1]), r[2]) for r in reqs_elaborated if r[0] == "conf"]
    scope = Scope(world, reqs, check_stability=False)
    g = (goal_elaborated[0], resolve(goal_elaborated[1]),
         goal_elaborated[2] if goal_elaborated[0] == "conf" else resolve(goal_elaborated[2]))
    return "valid" if scope.decide(g)[0] else "invalid"


# --------------------------------------------------------------------------------------------
# Entry point


def answer(world, query):
    """The reference answer for one query; see the module documentation."""
    out = {"verdict": None, "count": None, "size": None, "eq_needed": None,
           "congruence": None, "sem": None, "note": "", "ordered": None}
    reqs = query["reqs"]
    try:
        scope = Scope(world, reqs)
    except Unspecified as e:
        out.update(verdict="unspecified", note=str(e))
        return out
    # True if every requirement could be given its meaning from the requirements written
    # before it (the compiler elaborates a where clause from left to right).
    out["ordered"] = scope.order == sorted(scope.order)
    try:
        goal = scope.elaborate_requirement(query["goal"]) if query["goal"][0] != "coerce" else \
            ("coerce", scope.elaborate(query["goal"][1]), scope.elaborate(query["goal"][2]))
    except IllFormed as e:
        out.update(verdict="illformed-goal", note=str(e))
        return out
    ok, count, size = scope.decide(goal)
    if scope.bounded:
        out.update(verdict="unspecified", note="depth bound reached")
        return out
    out.update(verdict="derivable" if ok else "underivable", count=count, size=size)
    out["goal"] = goal
    elaborated = [scope.elaborated[i] for i in range(len(reqs))]
    out["sem"] = semantic(world, elaborated, goal)

    if ok:
        # Smallest number of equality requirements that still make the goal derivable, with the
        # same elaboration of the projections.
        eqs = [i for i, r in enumerate(elaborated) if r[0] == "eq"]
        for n in range(len(eqs) + 1):
            found = False
            for keep in itertools.combinations(eqs, n):
                rs = [r for i, r in enumerate(elaborated) if r[0] == "conf" or i in keep]
                if _decide_plain(world, rs, goal, True):
                    found = True
                    break
            if found:
                out["eq_needed"] = n
                break
        out["congruence"] = not _decide_plain(world, elaborated, goal, False)
    return out


def _decide_plain(world, elaborated_reqs, goal, congruence):
    """Decides an elaborated goal from elaborated requirements (no projection left)."""
    scope = Scope(world, [], congruence=congruence, check_stability=False)
    for i, r in enumerate(elaborated_reqs):
        scope.enter(i, r)
    return scope.decide(goal)[0]


if __name__ == "__main__":
    import sys
    for path in sys.argv[1:]:
        w = load_world(json.load(open(path)))
        for i, q in enumerate(w["queries"]):
            a = answer(w, q)
            a.pop("goal", None)
            print(path, i, a)
