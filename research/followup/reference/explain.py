"""A model of *why* the compiler rejects goals that the specification derives.

This is not part of the specification or of the reference. It encodes three hypotheses about
the implementation, read off its source (`Typer.match`, `Typer.canDeriveCoercions`), and tags a
derivable goal with the hypotheses that predict a rejection:

    DECOMP      Two types of the same shape are compared part by part, and only the innermost
                differing parts must be equal. An equality between two compound types that is
                not an equality of their parts (Box<A> == Box<B> without A == B) is not used.
    PREFILTER   A coercion between two differing parts is attempted only if each part is,
                syntactically, a side of some equality requirement of the scope. Types that are
                equal by congruence but are not written in the where clause are refused.
    DECL-HEAD   The head of a conformance declaration is matched against the goal's type part
                by part, so a declaration for Box<a> is not found for a parameter U with
                Box<T> == U (falls under DECOMP/PREFILTER at the head).

Two more hypotheses concern associated types, and come from observation (hand/p04.hylo,
hand/blanket-*.hylo), not from the source:

    BLANKET     The associated type of a conformance declared for a bare parameter
                (given <A where ...> => A is P { type X = ... A ... }) is not instantiated: it is
                one opaque type, the same for every instance.
    PROJ-APP    `T.X` is not found when T's conformance comes from a declaration for a generic
                type that T is equal to (T == Box<U>).

`tags(world, query)` returns the set of tags; the empty set predicts "accepted". report.py
tabulates the prediction against the compiler's verdicts, which tests the hypotheses.
"""
import reference
from reference import Scope, substitute


def mismatches(a, b, pattern_params=()):
    """The innermost pairs of differing parts of `a` and `b`, compared structurally. A pattern
    parameter on the left matches anything (first occurrence binds it)."""
    out = []
    binding = {}

    def walk(x, y):
        if x[0] == "var" and x[1] in pattern_params:
            if x[1] in binding:
                walk(binding[x[1]], y)
            else:
                binding[x[1]] = y
            return
        if x == y:
            return
        if x[0] == "app" and y[0] == "app" and x[1] == y[1] and len(x[2]) == len(y[2]):
            for p, q in zip(x[2], y[2]):
                walk(p, q)
        elif x[0] == "app" and y[0] == "app" and x[2] and y[2] \
                and not x[1].startswith("{") and not y[1].startswith("{"):
            # Two applications of different nominal types: the constructors themselves are
            # compared first, and they are never equal.
            out.append((("app", x[1], ()), ("app", y[1], ())))
        else:
            out.append((x, y))

    walk(a, b)
    return out, binding


def coercion_tags(scope, sides, a, b, pattern_params=()):
    """Tags for matching a given of type `a` against the goal type `b`."""
    tags = set()
    pairs, binding = mismatches(a, b, pattern_params)
    for x, y in pairs:
        x = substitute(x, binding)
        if reference.variables(x) & set(pattern_params):
            tags.add("DECL-HEAD")       # an unbound pattern variable inside a differing part
        elif not scope.eg.equal(x, y):
            tags.add("DECOMP")
        elif x not in sides or y not in sides:
            tags.add("PREFILTER")
    return tags, binding


def projection_tags(world, scope, query):
    out = set()
    types = [t for r in query["reqs"] + [query["goal"]] for t in r[1:] if isinstance(t, tuple)]
    for t in types:
        for s in reference.subterms(t):
            if s[0] != "proj":
                continue
            try:
                d = scope.select(s[2], scope.elaborate(s[1]))
            except reference.IllFormed:
                continue
            if d[0] != "conf":
                continue
            c = world["confs"][d[1]]
            if c["type"][0] == "var" and c["impl"] is not None and reference.variables(c["impl"]):
                out.add("BLANKET")
            if c["type"][0] == "app" and c["type"][2]:
                out.add("PROJ-APP")
    return out


def tags(world, query):
    """The set of predicted causes of rejection for a derivable goal (empty: accepted)."""
    scope = Scope(world, query["reqs"])
    return projection_tags(world, scope, query) | other_tags(world, scope, query)


def other_tags(world, scope, query):
    reqs = [scope.elaborated[i] for i in range(len(query["reqs"]))]
    sides = set()
    for r in reqs:
        if r[0] == "eq":
            sides.update((r[1], r[2]))
    g = query["goal"]
    if g[0] == "eq":
        return set()                      # decided by the equality procedure under FIX and FULL
    if g[0] == "coerce":
        a, b = scope.elaborate(g[1]), scope.elaborate(g[2])
        if a == b:
            return set()
        # The whole types are tried as one coercion when both pass the filter.
        if a in sides and b in sides:
            return set()
        t, _ = coercion_tags(scope, sides, a, b)
        return t
    return conf_tags(world, scope, reqs, sides, g[2], scope.elaborate(g[1]), 6)


def conf_tags(world, scope, reqs, sides, trait, ty, depth):
    """The smallest tag set over the ways the search could derive `trait<ty>`."""
    best = None
    if depth == 0:
        return {"DEPTH"}
    for r in reqs:
        if r[0] == "conf" and r[2] == trait and scope.eg.equal(r[1], ty):
            t, _ = coercion_tags(scope, sides, r[1], ty)
            if best is None or len(t) < len(best):
                best = t
    for d in world["confs"]:
        if d["trait"] != trait:
            continue
        t, binding = coercion_tags(scope, sides, d["type"], ty, d["params"])
        if len(binding) != len(d["params"]):
            # Usable only if the head is matched through an equality.
            t = t | {"DECL-HEAD"}
            if best is None or len(t) < len(best):
                best = t
            continue
        ok = True
        for pr in d["premises"]:
            if pr[0] == "eq":
                x, y = substitute(pr[1], binding), substitute(pr[2], binding)
                if not scope.eg.equal(x, y):
                    ok = False
            else:
                x = substitute(pr[1], binding)
                if scope.min_size(pr[2], scope.eg.cls(x)) is None:
                    ok = False
                else:
                    t = t | conf_tags(world, scope, reqs, sides, pr[2], x, depth - 1)
        if ok and (best is None or len(t) < len(best)):
            best = t
    return best if best is not None else {"DECL-HEAD"}
