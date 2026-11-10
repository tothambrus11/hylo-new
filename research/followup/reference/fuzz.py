"""Generates random problems, labels them with the reference, and runs the compiler on them.

    python3 fuzz.py gen                 writes problems.jsonl (deterministic, fixed seeds)
    python3 fuzz.py run FIX FULL        runs the configurations named; restartable
    python3 fuzz.py run base --kinds conf --limit 100

A problem ("world") is a set of declarations and a handful of queries. Every query has its own
generic function, so one compiler run gives one verdict per query. When a run crashes or times
out, each query of the world is rerun alone to find the culprit.

Rows of results.jsonl: {"id", "config", "status", "verdicts", "messages", "isolated"}.
"""

import argparse
import hashlib
import json
import os
import random
import sys

import harness
import reference
from reference import Scope, IllFormed, Unspecified, app, var, proj, subterms, variables

HERE = os.path.dirname(os.path.abspath(__file__))
PROBLEMS = os.path.join(HERE, "problems.jsonl")
RESULTS = os.path.join(HERE, "results.jsonl")
WORK = os.path.join(HERE, "work")

SEED = 20261110
# kind -> number of worlds
PLAN = {"conf": 500, "eq-param": 550, "eq-app": 550, "chain": 450, "cond": 500, "assoc": 650,
        "twin": 200, "blanket": 250}
# "blanket" is "assoc" with, in every world, a conformance declared for a bare parameter
# (given <A where A is Tr0> => A is Tr1 { type X1 = ... A ... }).


# --------------------------------------------------------------------------------------------
# Declarations


def gen_declarations(rng, kind):
    blanket = kind == "blanket"
    if blanket:
        kind = "assoc"
    ntraits = rng.randint(2, 3) if blanket else rng.randint(1, 3)
    traits = {}
    for i in range(ntraits):
        has = kind == "assoc" and (i == 0 or rng.random() < 0.5)
        if blanket:
            has = i == 1 or rng.random() < 0.4
        traits["Tr%d" % i] = "X%d" % i if has else None
    structs = {"St0": 0, "St1": 0, "St2": 1}
    if rng.random() < 0.7:
        structs["St3"] = 2
    if rng.random() < 0.4:
        structs["St4"] = 1
    world = {"traits": traits, "structs": structs, "confs": [], "queries": []}

    used = set()
    nullary = [s for s, n in structs.items() if n == 0]
    if blanket:
        used.add(("Tr1", "*"))
        leaves = [var("A")] + [app(s) for s in nullary]
        impl = rand_type(rng, structs, leaves, rng.choice([0, 0, 1]))
        if rng.random() < 0.8 and "A" not in variables(impl):
            impl = var("A")
        world["confs"].append({"params": ["A"], "premises": [("conf", var("A"), "Tr0")],
                               "type": var("A"), "trait": "Tr1", "impl": impl})
    for _ in range(rng.randint(1, 5)):
        trait = rng.choice(list(traits))
        ti = int(trait[2:])
        if rng.random() < 0.1 and ti > 0 and (trait, "*") not in used and \
                not any(u[0] == trait for u in used):
            # A conformance for every type that has another conformance:
            # given <A where A is Tr(i-1)> => A is Tri
            used.add((trait, "*"))
            c = {"params": ["A"], "premises": [("conf", var("A"), "Tr%d" % rng.randrange(ti))],
                 "type": var("A"), "trait": trait, "impl": None}
        else:
            head = rng.choice(list(structs))
            if (trait, head) in used or (trait, "*") in used:
                continue
            used.add((trait, head))
            params, args = [], []
            for k in range(structs[head]):
                if rng.random() < 0.75:
                    p = "AB"[len(params)]
                    params.append(p)
                    args.append(var(p))
                else:
                    args.append(app(rng.choice(nullary)))
            premises = []
            for p in params:
                if rng.random() < (0.75 if kind == "cond" else 0.45):
                    premises.append(("conf", var(p), rng.choice(list(traits))))
            if params and rng.random() < (0.3 if kind == "cond" else 0.1):
                if len(params) == 2 and rng.random() < 0.5:
                    premises.append(("eq", var("A"), var("B")))
                else:
                    premises.append(("eq", var(rng.choice(params)), app(rng.choice(nullary))))
            rng.shuffle(premises)
            c = {"params": params, "premises": premises, "type": app(head, *args),
                 "trait": trait, "impl": None}
        if traits[trait]:
            leaves = [var(p) for p in c["params"]] + [app(s) for s in nullary]
            c["impl"] = rand_type(rng, structs, leaves, rng.choice([0, 0, 1]))
        world["confs"].append(c)
    return world


def rand_type(rng, structs, leaves, depth, tuples=False):
    if depth == 0 or rng.random() < 0.3:
        return rng.choice(leaves)
    heads = [s for s, n in structs.items() if n > 0]
    if tuples and rng.random() < 0.2:
        n = 2
        return app("{%d}" % n, *[rand_type(rng, structs, leaves, depth - 1, tuples) for _ in range(n)])
    h = rng.choice(heads)
    return app(h, *[rand_type(rng, structs, leaves, depth - 1, tuples) for _ in range(structs[h])])


# --------------------------------------------------------------------------------------------
# Contexts (the where clause of a query function)


def gen_context(rng, world, kind):
    blanket = kind == "blanket"
    if blanket:
        kind = "assoc"
    structs, traits = world["structs"], list(world["traits"])
    nullary = [s for s, n in structs.items() if n == 0]
    unary = [s for s, n in structs.items() if n == 1]
    n = rng.randint(0, 3) if kind == "conf" else rng.randint(2, 5)
    params = ["T%d" % i for i in range(n)]
    P = [var(p) for p in params]
    reqs = []

    def pair():
        a, b = rng.sample(P, 2)
        return a, b

    if kind in ("eq-param", "cond", "assoc", "twin") and n >= 2:
        for _ in range(rng.randint(0 if kind == "assoc" else 1, 3 if kind != "assoc" else 1)):
            a, b = pair()
            reqs.append(("eq", a, b))
    if kind == "eq-app" and n >= 2:
        for _ in range(rng.randint(1, 3)):
            a, b = pair()
            c = rng.choice(P)
            form = rng.randrange(9)
            u, u2 = rng.choice(unary), rng.choice(unary)
            if form == 0:
                e = (a, app(u, b))
            elif form == 1:
                e = (app(u, a), b)
            elif form == 2:
                e = (app(u, a), app(u, b))
            elif form == 3:
                e = (a, app(rng.choice(nullary)))
            elif form == 4 and "St3" in structs:
                e = (app("St3", a, b), c)
            elif form == 5:
                e = (app("{2}", a, b), c)
            elif form == 6:
                e = (app("{2}", a, b), app("{2}", b, c))
            elif form == 7:
                e = (app(u, a), app(u2, app(rng.choice(nullary))))
            else:
                e = (a, b)
            if rng.random() < 0.5:
                e = (e[1], e[0])
            reqs.append(("eq",) + e)
    if kind == "chain":
        # T0 == T1 == ... == Tn, each link possibly under a constructor on one side.
        order = P[:]
        rng.shuffle(order)
        links = []
        for a, b in zip(order, order[1:]):
            r = rng.random()
            if r < 0.15:
                a = app(rng.choice(unary), a)
            elif r < 0.25:
                a, b = app(rng.choice(unary), a), app(rng.choice(unary), b)
            links.append(("eq", a, b) if rng.random() < 0.5 else ("eq", b, a))
        if len(links) > 1 and rng.random() < 0.25:
            links.pop(rng.randrange(len(links)))
        reqs.extend(links)

    seen = set()
    if kind == "cond" and n >= 2:
        # Requirements that satisfy the premises of a declaration only through an equality.
        cs = [c for c in world["confs"] if any(p[0] == "conf" for p in c["premises"])]
        if cs:
            c = rng.choice(cs)
            for pr in c["premises"]:
                if pr[0] == "conf" and rng.random() < 0.8:
                    r = ("conf", rng.choice(P), pr[2])
                    if r not in seen:
                        seen.add(r)
                        reqs.append(r)

    # Conformance requirements.
    for _ in range(rng.randint(0, 3) if n else 0):
        t = rng.choice(P)
        if rng.random() < 0.15 and unary:
            t = app(rng.choice(unary), t)
        r = ("conf", t, rng.choice(traits))
        if r not in seen:
            seen.add(r)
            reqs.append(r)

    if kind == "assoc":
        with_assoc = [(r[1], r[2]) for r in reqs if r[0] == "conf" and r[1][0] == "var"
                      and world["traits"][r[2]]]
        bases = with_assoc[:]
        if blanket:
            # Parameters that get the associated type through the blanket conformance.
            for _ in range(rng.randint(1, 3)):
                p = rng.choice(P)
                if ("conf", p, "Tr0") not in seen:
                    seen.add(("conf", p, "Tr0"))
                    reqs.append(("conf", p, "Tr0"))
                bases.append((p, "Tr1"))
        # A parameter without requirement may still have the projection through an equality.
        for p in P:
            for tr in traits:
                if world["traits"][tr] and rng.random() < 0.15:
                    bases.append((p, tr))
        for s in nullary:
            for tr in traits:
                if world["traits"][tr] and rng.random() < 0.3:
                    bases.append((app(s), tr))
        for _ in range(rng.randint(0, 3)):
            if not bases:
                break
            b, tr = rng.choice(bases)
            x = proj(b, tr)
            form = rng.randrange(6)
            if form <= 1:
                b2, tr2 = rng.choice(bases)
                y = proj(b2, tr2)
            elif form == 2 and P:
                y = rng.choice(P)
            elif form == 3:
                y = app(rng.choice(nullary))
            elif form == 4 and P:
                y = app(rng.choice(unary), rng.choice(P))
            else:
                r = ("conf", x, rng.choice(traits))
                if r not in seen:
                    seen.add(r)
                    reqs.append(r)
                continue
            if x != y:
                reqs.append(("eq", x, y) if rng.random() < 0.5 else ("eq", y, x))
    reqs = dedupe(reqs)
    rng.shuffle(reqs)
    return params, reqs


def dedupe(reqs):
    out = []
    for r in reqs:
        if r not in out and not (r[0] == "eq" and (r[1] == r[2] or ("eq", r[2], r[1]) in out)):
            out.append(r)
    return out


def satisfiable(reqs):
    """True if the projection-free equalities of `reqs` have a solution over free constructors."""
    eqs = [(r[1], r[2]) for r in reqs if r[0] == "eq" and not reference.has_proj(r[1])
           and not reference.has_proj(r[2])]
    return reference.unify(eqs) is not None


# --------------------------------------------------------------------------------------------
# Goals


def replace_at(t, path, new):
    if not path:
        return new
    if t[0] == "app":
        args = list(t[2])
        args[path[0]] = replace_at(args[path[0]], path[1:], new)
        return ("app", t[1], tuple(args))
    return ("proj", replace_at(t[1], path[1:], new), t[2])


def positions(t, prefix=()):
    """Paths to the subterms of `t` that may be replaced (not the bases of projections)."""
    yield prefix
    if t[0] == "app":
        for i, a in enumerate(t[2]):
            yield from positions(a, prefix + (i,))


def at(t, path):
    for i in path:
        t = t[2][i]
    return t


def gen_goals(rng, world, params, reqs, scope, kind):
    """Candidate goals for a context: some built to be derivable, some mutated."""
    blanket = kind == "blanket"
    if blanket:
        kind = "assoc"
    structs, traits = world["structs"], list(world["traits"])
    nullary = [app(s) for s, n in structs.items() if n == 0]
    pool = [var(p) for p in params] + nullary
    for r in reqs:
        for t in (r[1],) + ((r[2],) if r[0] == "eq" else ()):
            for s in subterms(t):
                if s not in pool and not (s[0] == "proj" and not printable_proj(s)):
                    pool.append(s)
    if kind == "assoc":
        for p in params:
            for tr in traits:
                if world["traits"][tr] and proj(var(p), tr) not in pool and rng.random() < 0.5:
                    pool.append(proj(var(p), tr))
        for s in nullary:
            for tr in traits:
                if world["traits"][tr] and proj(s, tr) not in pool and rng.random() < 0.5:
                    pool.append(proj(s, tr))

    elab = {}
    for t in list(pool):
        try:
            elab[t] = scope.eg.cls(scope.elaborate(t))
        except IllFormed:
            elab[t] = None
            if rng.random() < 0.9:
                pool.remove(t)

    def cls(t):
        try:
            return scope.eg.cls(scope.elaborate(t))
        except IllFormed:
            return None

    def equal_alternative(t):
        c = cls(t)
        if c is None:
            return None
        xs = [p for p in pool if p != t and elab[p] is not None and scope.eg.find(elab[p]) == c]
        return rng.choice(xs) if xs else None

    def rewrite(t, steps, equal=True):
        for _ in range(steps):
            ps = list(positions(t))
            rng.shuffle(ps)
            for path in ps:
                s = at(t, path)
                new = equal_alternative(s) if equal else rng.choice(pool)
                if new is not None and new != s:
                    t = replace_at(t, path, new)
                    break
        return t

    def some_type():
        r = rng.random()
        if r < 0.35:
            return rng.choice(pool)
        return rand_type(rng, structs, pool, rng.choice([1, 1, 2]), tuples=kind in ("eq-app", "eq-param"))

    out = []
    for _ in range(16 if kind == "cond" else 10):
        r = rng.random()
        if r < (0.6 if kind == "cond" else 0.3) and world["confs"]:
            c = rng.choice(world["confs"])
            leaves = [var(p) for p in params] if params and rng.random() < 0.7 else pool
            t = reference.substitute(c["type"], {p: rng.choice(leaves) for p in c["params"]})
            trait = c["trait"]
        elif r < 0.6 and any(q[0] == "conf" for q in reqs):
            q = rng.choice([q for q in reqs if q[0] == "conf"])
            t, trait = q[1], q[2]
            if rng.random() < 0.3 and any(n == 1 for n in structs.values()):
                t = app(rng.choice([s for s, n in structs.items() if n == 1]), t)
        else:
            t, trait = some_type(), rng.choice(traits)
        t = rewrite(t, rng.choice([0, 1, 1, 2]), equal=rng.random() < 0.8)
        out.append(("conf", t, trait))
    if kind != "conf":
        for _ in range(12):
            a = some_type()
            b = rewrite(a, rng.choice([1, 1, 2, 3]), equal=rng.random() < 0.75)
            if rng.random() < 0.3:
                a, b = b, a
            out.append((rng.choice(["eq", "coerce"]), a, b))
    if blanket:
        # Two associated types through the blanket conformance, possibly under a constructor.
        ps = [t for t in pool if t[0] == "proj" and t[2] == "Tr1"] + [var(p) for p in params]
        for _ in range(8):
            a, b = rng.choice(ps), rng.choice(ps)
            if a != b:
                if rng.random() < 0.3:
                    a, b = app("St2", a), app("St2", b)
                out.append((rng.choice(["eq", "coerce"]), a, b))
    return out


def printable_proj(t):
    b = t[1]
    return b[0] == "var" or (b[0] == "app" and not b[2] and not b[1].startswith("{"))


def printable(world, q):
    import to_hylo
    try:
        to_hylo.query_line(world, 0, q)
        return True
    except to_hylo.Unprintable:
        return False


def label(world, q):
    a = reference.answer(world, q)
    a.pop("goal", None)
    return a


def interest(a):
    """How much a derivable answer exercises the theory."""
    return (a["eq_needed"] or 0) + (a["size"] or 0) + (1 if a["congruence"] else 0)


def gen_queries(rng, world, kind, want=6):
    """Fills world["queries"]; returns the reference answers."""
    queries, answers = [], []
    tries = 0
    multi = 0
    while len(queries) < want and tries < 40:
        tries += 1
        params, reqs = gen_context(rng, world, kind)
        if not satisfiable(reqs) and rng.random() < 0.85:
            continue
        try:
            scope = Scope(world, reqs)
            if kind in ("assoc", "blanket") and rng.random() < 0.85:
                # Write the requirements in an order in which each one only uses associated
                # types made available by the previous ones (the compiler requires it).
                reqs = [reqs[i] for i in scope.order]
                scope = Scope(world, reqs)
        except Unspecified:
            continue
        pos, neg = [], []
        for g in gen_goals(rng, world, params, reqs, scope, kind):
            q = {"params": params, "reqs": reqs, "goal": g}
            if not printable(world, q) or any(q == x for x in queries):
                continue
            a = label(world, q)
            if a["verdict"] == "derivable":
                pos.append((q, a))
            elif a["verdict"] in ("underivable", "illformed-goal"):
                neg.append((q, a))
        chosen = []
        if pos:
            # Prefer goals that need equalities, congruence or a larger derivation.
            def score(x):
                g = x[0]["goal"]
                bonus = 2 if any(reference.has_proj(t) for t in g[1:] if isinstance(t, tuple)) else 0
                if kind == "blanket":
                    bonus += 2 * sum(1 for t in g[1:] if isinstance(t, tuple)
                                     for u in subterms(t) if u[0] == "proj" and u[2] == "Tr1")
                return interest(x[1]) + bonus
            pos.sort(key=lambda x: -score(x))
            top = [x for x in pos if score(x) == score(pos[0])]
            q, a = rng.choice(top)
            if a["count"] is not None and a["count"] >= 2:
                multi += 1
                if multi > 1:
                    q = None
            if q is not None:
                chosen.append((q, a))
                # A near miss: the same goal with one requirement removed.
                if reqs and rng.random() < 0.7:
                    k = rng.randrange(len(reqs))
                    q2 = {"params": params, "reqs": reqs[:k] + reqs[k + 1:], "goal": q["goal"]}
                    a2 = label(world, q2)
                    if a2["verdict"] == "underivable":
                        chosen.append((q2, a2))
        if kind == "blanket":
            # Prefer underivable goals that compare two associated types of the blanket trait.
            def two(x):
                g = x[0]["goal"]
                return sum(1 for t in g[1:] if isinstance(t, tuple)
                           for u in subterms(t) if u[0] == "proj" and u[2] == "Tr1") >= 2
            if any(two(x) for x in neg) and rng.random() < 0.7:
                neg = [x for x in neg if two(x)]
        if neg and (len(chosen) < 2 or rng.random() < 0.3):
            # Prefer underivable goals in a scope that has equalities, and that are valid with
            # injectivity (they separate the specification from stronger theories).
            def with_proj(x):
                g = x[0]["goal"]
                return any(reference.has_proj(t) for t in g[1:] if isinstance(t, tuple))
            if kind in ("assoc", "blanket") and rng.random() < 0.6 and any(with_proj(x) for x in neg):
                neg = [x for x in neg if with_proj(x)]
            neg.sort(key=lambda x: (x[1]["sem"] != "valid", x[1]["verdict"] != "underivable"))
            pick = neg[0] if neg[0][1]["sem"] == "valid" and rng.random() < 0.7 else rng.choice(neg)
            chosen.append(pick)
        for q, a in chosen:
            if len(queries) < want and q not in queries:
                queries.append(q)
                answers.append(a)
    world["queries"] = queries
    return answers


def gen_twin_queries(rng, world, want=4):
    """Queries with two derivations exchanged by a symmetry of the problem (certain ambiguity)."""
    queries, answers = [], []
    tries = 0
    while len(queries) < want and tries < 200:
        tries += 1
        params, reqs = gen_context(rng, world, "twin")
        try:
            scope = Scope(world, reqs)
        except Unspecified:
            continue
        for g in gen_goals(rng, world, params, reqs, scope, "twin"):
            if g[0] != "conf":
                continue
            q = {"params": params, "reqs": reqs, "goal": g}
            a = label(world, q)
            if a["verdict"] != "derivable" or a["count"] != 1 or not a["eq_needed"]:
                continue
            # Duplicate every parameter that the goal does not mention, with its requirements.
            keep = variables(g[1])
            dup = [p for p in params if p not in keep]
            if not dup:
                continue
            ren = {p: var(p + "b") for p in dup}
            extra = []
            for r in reqs:
                vs = set().union(*[variables(t) for t in r[1:] if isinstance(t, tuple)])
                if vs & set(dup):
                    r2 = tuple(reference.substitute(t, ren) if isinstance(t, tuple) else t for t in r)
                    extra.append(r2)
            twin = [flip(rng, r) for r in reqs + extra]
            rng.shuffle(twin)
            q2 = {"params": params + [p + "b" for p in dup], "reqs": twin, "goal": g}
            a2 = label(world, q2)
            if a2["verdict"] == "derivable" and a2["count"] >= 2 and printable(world, q2):
                a2["twin"] = True
                queries.append(q2)
                answers.append(a2)
                break
    world["queries"] = queries
    return answers


def flip(rng, r):
    if r[0] == "eq" and rng.random() < 0.5:
        return ("eq", r[2], r[1])
    return r


def gen_world(kind, index):
    seed = int(hashlib.sha1(("%d/%s/%d" % (SEED, kind, index)).encode()).hexdigest()[:12], 16)
    rng = random.Random(seed)
    for attempt in range(50):
        world = gen_declarations(rng, kind)
        if kind == "twin":
            answers = gen_twin_queries(rng, world)
        else:
            answers = gen_queries(rng, world, kind)
        if kind == "cond" and not any(p[0] == "conf" for c in world["confs"] for p in c["premises"]):
            continue
        if len(world["queries"]) >= (1 if kind == "twin" else 3):
            break
    return {"id": "%s-%04d" % (kind, index), "kind": kind, "seed": seed, "world": world,
            "answers": answers}


# --------------------------------------------------------------------------------------------
# Commands


def cmd_gen(args):
    with open(PROBLEMS, "w") as f:
        for kind, n in PLAN.items():
            for i in range(n if args.limit is None else min(n, args.limit)):
                f.write(json.dumps(gen_world(kind, i)) + "\n")
    print("wrote", PROBLEMS)


def load_problems():
    out = []
    for l in open(PROBLEMS):
        p = json.loads(l)
        p["world"] = reference.load_world(p["world"])
        out.append(p)
    return out


def run_alone(args, out, p, c):
    """Runs one world alone; if the run fails, runs each of its queries alone."""
    path = os.path.join(WORK, p["id"] + ".hylo")
    limits = dict(harness.TIMEOUT)
    if args.timeout:
        limits[c] = args.timeout
    if args.isolate:
        r = {"status": "split", "code": 0, "verdicts": {}, "messages": {}}
    else:
        r = harness.run_world(p["world"], path, configs=(c,), timeouts=limits)[c]
    rows = [{"id": p["id"], "config": c, "isolated": None, **r}]
    if r["status"] in ("crash", "timeout", "split"):
        for i in range(len(p["world"]["queries"])):
            ipath = os.path.join(WORK, "%s-q%d.hylo" % (p["id"], i))
            ri = harness.run_world(p["world"], ipath, configs=(c,), only=[i], timeouts=limits)[c]
            rows.append({"id": p["id"], "config": c, "isolated": i, **ri})
    for row in rows:
        out.write(json.dumps(row) + "\n")
    out.flush()


def cmd_confirm(args):
    """Reruns alone every world that has a disagreement in a batch run."""
    import report
    problems, runs = report.load()
    todo = set()
    for r in report.rows(problems, runs, configs=args.configs):
        if r["class"] != "agree" and runs[(r["id"], r["config"])]["world"].get("batch"):
            todo.add((r["id"], r["config"]))
    print("to confirm:", len(todo))
    ps = {p["id"]: p for p in load_problems()}
    args.isolate, args.timeout = False, None
    with open(RESULTS, "a") as out:
        for n, (pid, c) in enumerate(sorted(todo)):
            run_alone(args, out, ps[pid], c)
            if n % 50 == 0:
                print("confirmed", n, flush=True)


def cmd_run(args):
    os.makedirs(WORK, exist_ok=True)
    done = set()
    if os.path.exists(RESULTS):
        for l in open(RESULTS):
            r = json.loads(l)
            if r.get("isolated") is None:
                done.add((r["id"], r["config"]))
    problems = load_problems()
    if args.kinds:
        problems = [p for p in problems if p["kind"] in args.kinds.split(",")]
    if args.limit is not None:
        per = {}
        kept = []
        for p in problems:
            per[p["kind"]] = per.get(p["kind"], 0) + 1
            if per[p["kind"]] <= args.limit:
                kept.append(p)
        problems = kept
    # Interleave the kinds, so that a partial run covers all of them.
    problems.sort(key=lambda p: (int(p["id"].rsplit("-", 1)[1]), p["kind"]))
    n = 0
    with open(RESULTS, "a") as out:
        for c in args.configs if args.batch > 1 else []:
            # Several worlds per compiler run, with disjoint names. A world that is part of a
            # failed batch is run alone below.
            todo = [p for p in problems if (p["id"], c) not in done]
            for k in range(0, len(todo), args.batch):
                group = todo[k:k + args.batch]
                path = os.path.join(WORK, "batch-%s-%s.hylo" % (c, group[0]["id"]))
                rs = harness.run_batch([p["world"] for p in group], path, c)
                if rs is None:
                    continue
                for p, r in zip(group, rs):
                    out.write(json.dumps({"id": p["id"], "config": c, "isolated": None,
                                          "batch": group[0]["id"], **r}) + "\n")
                    done.add((p["id"], c))
                out.flush()
                n += 1
                if n % 20 == 0:
                    print("ran", n, "batches;", group[0]["id"], c, flush=True)
        for p in problems:
            for c in args.configs:
                if (p["id"], c) in done:
                    continue
                run_alone(args, out, p, c)
                n += 1
                if n % 50 == 0:
                    print("ran", n, p["id"], c, flush=True)
    print("done:", n, "runs")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd")
    g = sub.add_parser("gen")
    g.add_argument("--limit", type=int)
    r = sub.add_parser("run")
    r.add_argument("configs", nargs="+")
    r.add_argument("--kinds")
    r.add_argument("--limit", type=int)
    r.add_argument("--isolate", action="store_true")
    r.add_argument("--timeout", type=int)
    r.add_argument("--batch", type=int, default=1, help="worlds per compiler run")
    c = sub.add_parser("confirm")
    c.add_argument("configs", nargs="+")
    a = ap.parse_args()
    {"gen": cmd_gen, "run": cmd_run, "confirm": cmd_confirm}[a.cmd](a)
