"""Prints an abstract problem (see reference.py) as a Hylo program.

Every query becomes one generic function on one line, so that a diagnostic can be attributed to
its query by its line number. The program is accepted exactly when every query is derivable:

    conformance goal  t is P    ->  fun qN<params where reqs>() { needP<t>() }
    equality goal     a == b    ->  fun qN<params where reqs>() { needEq<a, b>() }
    coercion goal     a to b    ->  fun qN<params where reqs>(x: a) { check<b>(x) }

where `needP`, `needEq` and `check` are declared once:

    fun needP<W where W is P>() {}
    fun needEq<X, Y where X == Y>() {}
    fun check<X>(x: X) {}
"""

import json
import sys

from reference import load_world


class Unprintable(Exception):
    pass


def ty(world, t):
    if t[0] == "var":
        return t[1]
    if t[0] == "app":
        if t[1].startswith("{"):
            return "{" + ", ".join(ty(world, a) for a in t[2]) + "}"
        if not t[2]:
            return t[1]
        return t[1] + "<" + ", ".join(ty(world, a) for a in t[2]) + ">"
    if t[0] == "proj":
        # Only `T.X` and `S.X` are accepted in type position by this compiler.
        b = t[1]
        if not (b[0] == "var" or (b[0] == "app" and not b[2] and not b[1].startswith("{"))):
            raise Unprintable("projection on a compound type")
        return ty(world, b) + "." + world["traits"][t[2]]
    raise Unprintable(repr(t))


def requirement(world, r):
    if r[0] == "conf":
        return "%s is %s" % (ty(world, r[1]), r[2])
    return "%s == %s" % (ty(world, r[1]), ty(world, r[2]))


def clause(world, params, reqs):
    """`<T, U where ...>`, or the empty string."""
    if not params and not reqs:
        return ""
    s = ", ".join(params)
    if reqs:
        s += (" " if params else "") + "where " + ", ".join(requirement(world, r) for r in reqs)
    return "<" + s + ">"


def query_line(world, i, q, prefix="q"):
    c = clause(world, q["params"], q["reqs"])
    g = q["goal"]
    if g[0] == "conf":
        return "fun %s%d%s() { need%s<%s>() }" % (prefix, i, c, g[2], ty(world, g[1]))
    if g[0] == "eq":
        return "fun %s%d%s() { needEq<%s, %s>() }" % (prefix, i, c, ty(world, g[1]), ty(world, g[2]))
    return "fun %s%d%s(x: %s) { check<%s>(x) }" % (prefix, i, c, ty(world, g[1]), ty(world, g[2]))


def declarations(world):
    lines = []
    for t, x in world["traits"].items():
        lines.append("trait %s { type %s }" % (t, x) if x else "trait %s {}" % t)
    for s, n in world["structs"].items():
        ps = "<" + ", ".join("E%d" % k for k in range(n)) + ">" if n else ""
        lines.append("struct %s%s { public memberwise init }" % (s, ps))
    for c in world["confs"]:
        cl = clause(world, c["params"], c["premises"])
        body = "{}"
        if world["traits"][c["trait"]]:
            if c["impl"] is None:
                raise Unprintable("missing implementation")
            body = "{ type %s = %s }" % (world["traits"][c["trait"]], ty(world, c["impl"]))
        lines.append("given %s%s is %s %s" % (cl + " => " if cl else "", ty(world, c["type"]),
                                               c["trait"], body))
    for t in world["traits"]:
        lines.append("fun need%s<W where W is %s>() {}" % (t, t))
    return lines


HELPERS = ["fun needEq<X, Y where X == Y>() {}", "fun check<X>(x: X) {}"]


def program(world, only=None):
    """Returns (text, {line number: query index}). `only` restricts the queries printed."""
    lines = declarations(world) + HELPERS
    where = {}
    for i, q in enumerate(world["queries"]):
        if only is not None and i not in only:
            continue
        lines.append(query_line(world, i, q))
        where[len(lines)] = i
    return "\n".join(lines) + "\n", where


if __name__ == "__main__":
    w = load_world(json.load(open(sys.argv[1])))
    sys.stdout.write(program(w)[0])
