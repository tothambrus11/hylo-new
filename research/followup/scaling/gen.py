#!/usr/bin/env python3
"""Parametric program families for the scaling study.

Usage:
    gen.py FAMILY SIZE          print one program
    gen.py --list               list the families, their sizes and intended verdicts

Every family is a function of ONE size parameter. `FAMILIES` maps a family name to
(generator, sizes, intended verdict, environment, primary counter, one-line description).
The intended verdict is what the language should answer: "ok" (accepted) or "err" (rejected for
the stated reason). A configuration may answer otherwise (for example the existing checker
rejects a long equality chain because of its depth bound); that is recorded as data.
"""
import sys


def box(d, leaf, name="S"):
    t = leaf
    for _ in range(d):
        t = f"{name}<{t}>"
    return t


# ---------------------------------------------------------------- equality chains

def eqchain(n):
    """Valid: conformance and associated type transported along n equality links."""
    ps = ", ".join(f"T{i}" for i in range(n + 1))
    eqs = ", ".join(f"T{i} == T{i+1}" for i in range(n))
    return f"""trait P {{ type X }}
fun check<T>(x: T) {{}}
fun g<V where V is P>() {{}}
fun f<{ps} where {eqs}, T0 is P>(x: T{n}.X) {{
  g<T{n}>()
  check<T0.X>(x)
}}
"""


def eqchain_conf(n):
    """Valid: conformance transported along n equality links (no associated type)."""
    ps = ", ".join(f"T{i}" for i in range(n + 1))
    eqs = ", ".join(f"T{i} == T{i+1}" for i in range(n))
    return f"""trait P {{}}
fun g<V where V is P>() {{}}
fun f<{ps} where {eqs}, T0 is P>() {{ g<T{n}>() }}
"""


def eqchain_neg(n):
    """Ill-typed: the chain of n links has its middle link missing, so T{n} is not P."""
    ps = ", ".join(f"T{i}" for i in range(n + 1))
    reqs = [f"T{i} == T{i+1}" for i in range(n) if i != n // 2] + ["T0 is P"]
    return f"""trait P {{}}
fun g<V where V is P>() {{}}
fun f<{ps} where {", ".join(reqs)}>() {{ g<T{n}>() }}
"""


def eqchain_goals(n):
    """Valid: a chain of n links and n equality goals T0 == Ti, one per link."""
    ps = ", ".join(f"T{i}" for i in range(n + 1))
    eqs = ", ".join(f"T{i} == T{i+1}" for i in range(n))
    calls = "\n".join(f"  need<T0, T{i}>()" for i in range(1, n + 1))
    return f"""fun need<A, B where A == B>() {{}}
fun f<{ps} where {eqs}>() {{
{calls}
}}
"""


# ---------------------------------------------------------------- associated-type equalities

def assoceq(n):
    """Valid: n equalities T{i}.X == T{i+1}.X; goal T0.X == T{n}.X."""
    ps = ", ".join(f"T{i}" for i in range(n + 1))
    eqs = ", ".join(f"T{i}.X == T{i+1}.X" for i in range(n))
    confs = ", ".join(f"T{i} is P" for i in range(n + 1))
    return f"""trait P {{ type X }}
fun check<T>(x: T) {{}}
fun f<{ps} where {confs}, {eqs}>(x: T{n}.X) {{
  check<T0.X>(x)
}}
"""


def assocneg(n):
    """Ill-typed: like assoceq with the middle equality missing."""
    ps = ", ".join(f"T{i}" for i in range(n + 1))
    eqs = ", ".join(f"T{i}.X == T{i+1}.X" for i in range(n) if i != n // 2)
    confs = ", ".join(f"T{i} is P" for i in range(n + 1))
    return f"""trait P {{ type X }}
fun check<T>(x: T) {{}}
fun f<{ps} where {confs}{', ' + eqs if eqs else ''}>(x: T{n}.X) {{
  check<T0.X>(x)
}}
"""


# ---------------------------------------------------------------- breadth

def breadth_traits(n):
    """Valid: n conformances A{i} is P{i} (n traits, n types) and one lookup."""
    out = [f"trait P{i} {{}}" for i in range(n)]
    out += [f"struct A{i} {{}}" for i in range(n)]
    out += [f"given A{i} is P{i} {{}}" for i in range(n)]
    out += ["fun need<where A0 is P0>() {}", "public fun main() { need() }"]
    return "\n".join(out) + "\n"


def breadth_types(n):
    """Valid: n conformances A{i} is P (one trait, n types) and one lookup."""
    out = ["trait P {}"]
    out += [f"struct A{i} {{}}" for i in range(n)]
    out += [f"given A{i} is P {{}}" for i in range(n)]
    out += ["fun need<where A0 is P>() {}", "public fun main() { need() }"]
    return "\n".join(out) + "\n"


def breadth_square(n):
    """Valid: n traits x n types = n*n conformances and n lookups (the shape of breadth40)."""
    out = [f"trait P{i} {{}}" for i in range(n)]
    out += [f"struct A{j} {{}}" for j in range(n)]
    for i in range(n):
        out += [f"given A{j} is P{i} {{}}" for j in range(n)]
    for q in range(n):
        out.append(f"fun need{q}<where A{(q * 7) % n} is P{q % n}>() {{}}")
    out.append("public fun main() {")
    out += [f"  need{q}()" for q in range(n)]
    out.append("}")
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------- divergence

def _div_rules(b, trunc=False):
    out = []
    for j in range(1, b + 1):
        out.append(f"struct S{j}<T> {{}}")
        out.append(f"given <T where S{j}<T> is P> => T is P {{}}")
        if trunc:
            out.append(f"given S{j}<S{j}<Xi>> is P {{}}")
    return out


def div_branch(b):
    """Ill-typed: Yb is P is underivable; b givens `S_j<T> is P => T is P` make the search grow."""
    out = ["trait P {}", "struct Yb {}"] + _div_rules(b)
    out += ["fun need<where Yb is P>() {}", "public fun main() { need() }"]
    return "\n".join(out) + "\n"


def div_branch_eq(b):
    """Ill-typed: div_branch with an unrelated equality A == B in scope."""
    out = ["trait P {}", "struct Yb {}"] + _div_rules(b)
    out += ["fun need<where Yb is P>() {}", "fun f<A, B where A == B>() { need() }"]
    return "\n".join(out) + "\n"


def div_trunc(b):
    """Ill-typed: div_branch with base facts S_j<S_j<Xi>> is P (deeper than the model's truncation)."""
    out = ["trait P {}", "struct Xi {}", "struct Yb {}"] + _div_rules(b, trunc=True)
    out += ["fun need<where Yb is P>() {}", "public fun main() { need() }"]
    return "\n".join(out) + "\n"


def div_depth(d):
    """Ill-typed: div_branch with b = 2; the size is the depth bound HYLO_TC_MAXDEPTH = d (>= 5, below which the standard library fails)."""
    return div_branch(2)


def div_trunc_depth(d):
    """Ill-typed: div_trunc with b = 2; the size is the depth bound HYLO_TC_MAXDEPTH = d."""
    return div_trunc(2)


def div_valid(d):
    """Valid: two growing givens; Xi is P holds through S1^d<Xi> is P (a derivation of depth d)."""
    out = ["trait P {}", "struct Xi {}"] + _div_rules(2)
    out.append(f"given {box(d, 'Xi', 'S1')} is P {{}}")
    out += ["fun need<where Xi is P>() {}", "public fun main() { need() }"]
    return "\n".join(out) + "\n"


def cyc_ring(n):
    """Ill-typed: a ring of n givens A{i+1} is P => A{i} is P with no base case."""
    out = ["trait P {}"] + [f"struct A{i} {{}}" for i in range(n)]
    out += [f"given <where A{(i + 1) % n} is P> => A{i} is P {{}}" for i in range(n)]
    out += ["fun need<where A0 is P>() {}", "public fun main() { need() }"]
    return "\n".join(out) + "\n"


def cyc_clique(n):
    """Ill-typed: n types, A{j} is P => A{i} is P for every i != j (branching n - 1), no base case."""
    out = ["trait P {}"] + [f"struct A{i} {{}}" for i in range(n)]
    for i in range(n):
        out += [f"given <where A{j} is P> => A{i} is P {{}}" for j in range(n) if j != i]
    out += ["fun need<where A0 is P>() {}", "public fun main() { need() }"]
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------- member lookup

def _members(n_types, n_ext, n_uses):
    out = [f"struct T{j} {{ public memberwise init }}" for j in range(n_types)]
    out += [f"extension T{e % n_types} {{ fun m{e}() {{}} }}" for e in range(n_ext)]
    out.append("public fun main() {")
    for u in range(n_uses):
        e = (u * 13) % n_ext
        out.append(f"  T{e % n_types}().m{e}()")
    out.append("}")
    return "\n".join(out) + "\n"


def members_ext(n):
    """Valid: n extensions over n/10 types, 20 member lookups."""
    return _members(max(1, n // 10), n, 20)


def members_use(m):
    """Valid: 100 extensions over 10 types, m member lookups."""
    return _members(10, 100, m)


def members_both(n):
    """Valid: n extensions over n/10 types and n member lookups."""
    return _members(max(1, n // 10), n, n)


def condext(n):
    """Valid: n conditional extensions of Box<T> (each needs T is P{i}), 8 member lookups."""
    out = ["struct A { public memberwise init }", "struct Box<T> { public memberwise init }"]
    for i in range(n):
        out.append(f"trait P{i} {{}}")
        out.append(f"given A is P{i} {{}}")
        out.append(f"extension <T where T is P{i}> Box<T> {{ fun m{i}() {{}} }}")
    out.append("public fun main() {")
    for u in range(8):
        out.append(f"  Box<A>().m{(u * 13) % n}()")
    out.append("}")
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------- overloads

def _overloads(m, k):
    out = [f"struct A{i} {{ public memberwise init }}" for i in range(m)]
    out += [f"fun f(x: A{i}) -> A{i} {{ x }}" for i in range(m)]
    out.append("fun g(" + ", ".join(f"x{j}: A{j % m}" for j in range(k)) + ") {}")
    out.append("public fun main() { g(" + ", ".join(f"f(A{j % m}())" for j in range(k)) + ") }")
    return "\n".join(out) + "\n"


def ovl_calls(k):
    """Valid: one expression with k calls, each choosing among 4 overloads by argument type."""
    return _overloads(4, k)


def ovl_width(m):
    """Valid: one expression with 4 calls, each choosing among m overloads by argument type."""
    return _overloads(m, 4)


def _overloads_ret(m, n):
    out = [f"struct A{i} {{ public memberwise init }}" for i in range(m)]
    out += [f"fun h() -> A{i} {{ A{i}() }}" for i in range(m)]
    out.append("fun g(" + ", ".join(f"x{j}: A{j % m}" for j in range(n)) + ") {}")
    out.append("public fun main() { g(" + ", ".join("h()" for _ in range(n)) + ") }")
    return "\n".join(out) + "\n"


def ovr_args(n):
    """Valid: g(h(), ..., h()) with n arguments; h has 3 overloads differing in return type only."""
    return _overloads_ret(3, n)


def ovr_width(m):
    """Valid: g(h(), h(), h(), h()); h has m overloads differing in return type only."""
    return _overloads_ret(m, 4)


def ovl_stmts(k):
    """Valid: k separate statements, each one call choosing among 4 overloads."""
    out = [f"struct A{i} {{ public memberwise init }}" for i in range(4)]
    out += [f"fun f(x: A{i}) -> A{i} {{ x }}" for i in range(4)]
    out.append("fun g(x: A0) {}")
    out.append("public fun main() {")
    out += ["  g(f(A0()))" for _ in range(k)]
    out.append("}")
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------- nested conditional givens

def nest(d):
    """Valid: S<S<...<Z>>> is P at depth d through `T is P => S<T> is P`."""
    return f"""trait P {{}}
struct S<T> {{}}
struct Z {{}}
given Z is P {{}}
given <T where T is P> => S<T> is P {{}}
fun need<where {box(d, 'Z')} is P>() {{}}
public fun main() {{ need() }}
"""


def nest_neg(d):
    """Ill-typed: like nest but the leaf Y is not P."""
    return f"""trait P {{}}
struct S<T> {{}}
struct Z {{}}
struct Y {{}}
given Z is P {{}}
given <T where T is P> => S<T> is P {{}}
fun need<where {box(d, 'Y')} is P>() {{}}
public fun main() {{ need() }}
"""


def nest_diamond(d):
    """Valid: S<T> is P and S<T> is Q each need T is P and T is Q (2^d subgoals without sharing)."""
    return f"""trait P {{}}
trait Q {{}}
struct S<T> {{}}
struct Z {{}}
given Z is P {{}}
given Z is Q {{}}
given <T where T is P, T is Q> => S<T> is P {{}}
given <T where T is P, T is Q> => S<T> is Q {{}}
fun need<where {box(d, 'Z')} is P>() {{}}
public fun main() {{ need() }}
"""


def nest_diamond_neg(d):
    """Ill-typed: nest_diamond whose leaf Z is P but not Q."""
    return f"""trait P {{}}
trait Q {{}}
struct S<T> {{}}
struct Z {{}}
given Z is P {{}}
given <T where T is P, T is Q> => S<T> is P {{}}
given <T where T is P, T is Q> => S<T> is Q {{}}
fun need<where {box(d, 'Z')} is P>() {{}}
public fun main() {{ need() }}
"""


def refine(n):
    """Valid: T is Q{n} where Q{i} refines Q{i-1} ... refines P; the goal is T is P."""
    ls = ["trait P {}", "trait Q1 refines P {}"]
    ls += [f"trait Q{i} refines Q{i-1} {{}}" for i in range(2, n + 1)]
    return "\n".join(ls) + f"\nfun use<T>(x: T) {{}}\nfun f<T is Q{n}>() {{ use(summon[P<T>]) }}\n"


def nestwide(n):
    """Valid: n traits each declaring a nested given; n lookups, one per nested given."""
    ls = ["trait P {}"]
    for i in range(n):
        ls.append(f"struct S{i} {{}}")
        ls.append(f"trait R{i} {{ given S{i} is P }}")
    bounds = " & ".join(f"R{i}" for i in range(n))
    uses = "\n".join(f"  use(summon[P<S{i}>])" for i in range(n))
    return "\n".join(ls) + f"\nfun use<T>(x: T) {{}}\nfun f<T is {bounds}>() {{\n{uses}\n}}\n"


# ---------------------------------------------------------------- open equalities

def open_chain(n):
    """Valid: pick<T, U where U is Q, T == U>(x) with U inferred; A0 == ... == A{n}, A{n} is Q."""
    ps = ", ".join(f"A{i}" for i in range(n + 1))
    eqs = ", ".join(f"A{i} == A{i+1}" for i in range(n))
    return f"""trait Q {{}}
fun pick<T, U where U is Q, T == U>(x: T) {{}}
fun f<{ps} where {eqs}, A{n} is Q>(x: A0) {{ pick(x) }}
"""


def open_neg(n):
    """Ill-typed: open_chain without any conformance to Q."""
    ps = ", ".join(f"A{i}" for i in range(n + 1))
    eqs = ", ".join(f"A{i} == A{i+1}" for i in range(n))
    return f"""trait Q {{}}
fun pick<T, U where U is Q, T == U>(x: T) {{}}
fun f<{ps} where {eqs}>(x: A0) {{ pick(x) }}
"""


def open_wide(n):
    """Valid: pick has n inferred arguments U{i}, each with U{i} is Q and T == U{i}."""
    us = ", ".join(f"U{i}" for i in range(1, n + 1))
    reqs = ", ".join(f"U{i} is Q, T == U{i}" for i in range(1, n + 1))
    return f"""trait Q {{}}
fun pick<T, {us} where {reqs}>(x: T) {{}}
fun f<A0 where A0 is Q>(x: A0) {{ pick(x) }}
"""


# ---------------------------------------------------------------- where clauses

def req_traits(n):
    """Valid: f<T where T is P1..Pn> calls g<T> with the same n requirements."""
    ts = "\n".join(f"trait P{i} {{}}" for i in range(1, n + 1))
    reqs = ", ".join(f"T is P{i}" for i in range(1, n + 1))
    return f"""{ts}
fun g<T where {reqs}>() {{}}
fun f<T where {reqs}>() {{ g<T>() }}
"""


def req_params(n):
    """Valid: f<T1..Tn where Ti is P> calls g<T1, ..., Tn> with the same n requirements."""
    ps = ", ".join(f"T{i}" for i in range(1, n + 1))
    reqs = ", ".join(f"T{i} is P" for i in range(1, n + 1))
    return f"""trait P {{}}
fun g<{ps} where {reqs}>() {{}}
fun f<{ps} where {reqs}>() {{ g<{ps}>() }}
"""


def req_eq(n):
    """Valid: f<T1..Tn, U1..Un where Ti == Ui> calls g with the same n equality requirements."""
    ps = ", ".join(f"T{i}" for i in range(1, n + 1)) + ", " + ", ".join(f"U{i}" for i in range(1, n + 1))
    reqs = ", ".join(f"T{i} == U{i}" for i in range(1, n + 1))
    return f"""fun g<{ps} where {reqs}>() {{}}
fun f<{ps} where {reqs}>() {{ g<{ps}>() }}
"""


def req_neg(n):
    """Ill-typed: req_traits where the caller lacks the last requirement."""
    ts = "\n".join(f"trait P{i} {{}}" for i in range(1, n + 1))
    reqs = ", ".join(f"T is P{i}" for i in range(1, n + 1))
    have = ", ".join(f"T is P{i}" for i in range(1, n))
    w = f" where {have}" if have else ""
    return f"""{ts}
fun g<T where {reqs}>() {{}}
fun f<T{w}>() {{ g<T>() }}
"""


# ---------------------------------------------------------------- registry

M = "summon.matches"
# name: (generator, sizes, intended verdict, extra environment, primary counter)
FAMILIES = {
    "eqchain":        (eqchain,        [1, 2, 3, 4, 5, 6, 8, 12, 16, 24, 32, 64, 128, 256, 512, 1024], "ok", {}, M),
    "eqchain-conf":   (eqchain_conf,   [1, 2, 3, 4, 5, 6, 8, 12, 16, 24, 32, 64, 128, 256, 512, 1024], "ok", {}, M),
    "eqchain-neg":    (eqchain_neg,    [1, 2, 3, 4, 5, 6, 8, 12, 16, 24, 32, 64, 128, 256, 512, 1024], "err", {}, M),
    "eqchain-goals":  (eqchain_goals,  [1, 2, 3, 4, 5, 6, 8, 12, 16, 24, 32, 64, 128, 256, 512, 1024], "ok", {}, M),
    "assoceq":        (assoceq,        [1, 2, 3, 4, 5, 6, 8, 12, 16, 24, 32, 64, 128, 256, 512, 1024], "ok", {}, M),
    "assocneg":       (assocneg,       [1, 2, 3, 4, 5, 6, 8, 12, 16, 24, 32, 64, 128, 256, 512, 1024], "err", {}, M),
    "breadth-traits": (breadth_traits, [8, 16, 32, 64, 128, 256, 512, 1024], "ok", {}, M),
    "breadth-types":  (breadth_types,  [8, 16, 32, 64, 128, 256, 512, 1024], "ok", {}, M),
    "breadth-square": (breadth_square, [4, 6, 8, 12, 16, 24, 32, 40, 48], "ok", {}, M),
    "div-branch":     (div_branch,     [1, 2, 3, 4, 5, 6, 8, 12, 16, 32], "err", {}, M),
    "div-branch-eq":  (div_branch_eq,  [1, 2, 3, 4, 5, 6, 8, 12, 16, 32], "err", {}, M),
    "div-trunc":      (div_trunc,      [1, 2, 3, 4, 5, 6, 8, 12, 16, 32], "err", {}, M),
    "div-depth":      (div_depth,      [5, 6, 8, 10, 12, 14, 16, 20, 24, 32, 40], "err", {"HYLO_TC_MAXDEPTH": "{n}"}, M),
    "div-trunc-depth": (div_trunc_depth, [5, 6, 8, 10, 12, 14, 16, 20, 24, 32, 40], "err", {"HYLO_TC_MAXDEPTH": "{n}"}, M),
    "div-valid":      (div_valid,      [1, 2, 3, 4, 5, 6, 7, 8], "ok", {}, M),
    "div-valid-deep": (div_valid,      [2, 4, 6, 8, 10, 12, 14, 16, 20], "ok", {"HYLO_TC_MAXDEPTH": "1000"}, M),
    "cyc-ring":       (cyc_ring,       [2, 3, 4, 6, 8, 12, 16, 32, 64], "err", {}, M),
    "cyc-clique":     (cyc_clique,     [2, 3, 4, 5, 6, 8, 12, 16], "err", {}, M),
    "members-ext":    (members_ext,    [20, 40, 80, 160, 320, 640, 1280], "ok", {}, "names.appliesCalls"),
    "members-use":    (members_use,    [10, 20, 40, 80, 160, 320, 640], "ok", {}, "names.appliesCalls"),
    "members-both":   (members_both,   [20, 40, 80, 160, 320, 640], "ok", {}, "names.appliesCalls"),
    "condext":        (condext,        [2, 4, 8, 16, 32, 64, 128], "ok", {}, "names.appliesCalls"),
    "ovl-calls":      (ovl_calls,      [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 14, 16, 20], "ok", {}, "solver.forks"),
    "ovl-width":      (ovl_width,      [2, 3, 4, 6, 8, 12, 16], "ok", {}, "solver.forks"),
    "ovl-stmts":      (ovl_stmts,      [1, 2, 4, 8, 16, 32, 64], "ok", {}, "solver.forks"),
    "ovr-args":       (ovr_args,       [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12], "ok", {}, "solver.forks"),
    "ovr-width":      (ovr_width,      [2, 3, 4, 6, 8, 12, 16], "ok", {}, "solver.forks"),
    "nest":           (nest,           [1, 2, 3, 4, 5, 6, 7, 8], "ok", {}, M),
    "nest-deep":      (nest,           [4, 8, 16, 32, 64, 128], "ok", {"HYLO_TC_MAXDEPTH": "1000"}, M),
    "nest-neg":       (nest_neg,       [4, 8, 16, 32, 64, 128], "err", {"HYLO_TC_MAXDEPTH": "1000"}, M),
    "nest-diamond":   (nest_diamond,   [1, 2, 3, 4, 5, 6, 8, 10, 12, 14, 16, 20], "ok", {"HYLO_TC_MAXDEPTH": "1000"}, M),
    "nest-diamond-neg": (nest_diamond_neg, [1, 2, 3, 4, 5, 6, 8, 10, 12, 14, 16, 20], "err", {"HYLO_TC_MAXDEPTH": "1000"}, M),
    "refine":         (refine,         [1, 2, 3, 4, 5, 6, 7, 8], "ok", {}, M),
    "refine-deep":    (refine,         [4, 8, 16, 32, 64], "ok", {"HYLO_TC_MAXDEPTH": "1000"}, M),
    "nestwide":       (nestwide,       [2, 4, 8, 16, 32, 64], "ok", {}, M),
    "open-chain":     (open_chain,     [1, 2, 3, 4, 5, 6, 8, 12, 16, 24, 32, 64, 128, 256, 512], "ok", {}, M),
    "open-neg":       (open_neg,       [1, 2, 3, 4, 5, 6, 8, 12, 16, 24, 32, 64, 128, 256, 512], "err", {}, M),
    "open-wide":      (open_wide,      [1, 2, 3, 4, 5, 6, 8, 12, 16], "ok", {}, M),
    "req-traits":     (req_traits,     [1, 2, 4, 8, 16, 32, 64, 128], "ok", {}, M),
    "req-params":     (req_params,     [1, 2, 4, 8, 16, 32, 64, 128], "ok", {}, M),
    "req-eq":         (req_eq,         [1, 2, 4, 8, 16, 32, 64, 128, 256, 512], "ok", {}, M),
    "req-neg":        (req_neg,        [1, 2, 4, 8, 16, 32, 64, 128], "err", {}, M),
}


def program(family, n):
    return FAMILIES[family][0](n)


if __name__ == "__main__":
    if sys.argv[1] == "--list":
        for k, (g, sizes, verdict, env, counter) in FAMILIES.items():
            print(f"{k:18} {verdict:3} {counter:18} {sizes} {env or ''}\n{'':18} {g.__doc__}")
    else:
        print(program(sys.argv[1], int(sys.argv[2])), end="")
