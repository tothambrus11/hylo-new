"""For conformance goals with several derivations: which kinds of derivations compete, and what
the compiler does. Informs open question 3 (ranking). Reads problems.jsonl and results.jsonl.

A root is described as: "requirement on the goal's type" (stated on exactly that type),
"requirement on an equal type" (needs a coercion), or "declaration".
"""
import collections

import reference
import report


def roots(world, q):
    scope = reference.Scope(world, q["reqs"])
    g = q["goal"]
    ty = scope.elaborate(g[1])
    out = []
    for d in scope.derivations(g[2], scope.eg.cls(ty), reference.DEPTH):
        if d[0] == "conf":
            out.append("declaration")
        else:
            r = scope.elaborated[d[1]]
            out.append("requirement on the goal's type" if r[1] == ty else "requirement on an equal type")
    return " + ".join(sorted(out))


def main():
    problems, runs = report.load()
    t = collections.Counter()
    for r in report.rows(problems, runs, configs=("FIX", "FULL")):
        a = r["answer"]
        if a["verdict"] != "derivable" or (a["count"] or 0) < 2 or r["verdict"] not in ("accept", "reject"):
            continue
        w = reference.load_world(problems[r["id"]]["world"])
        k = roots(w, w["queries"][r["q"]])
        t[("twin" if a.get("twin") else "other", k, r["config"], r["verdict"])] += 1
    print("| Problems | Competing derivations | FIX accepted | FIX rejected | FULL accepted | FULL rejected |")
    print("|---|---|---:|---:|---:|---:|")
    for kind, k in sorted({(x[0], x[1]) for x in t}):
        print("| %s | %s | %d | %d | %d | %d |" % (
            "symmetric (twin)" if kind == "twin" else "other kinds", k, t[(kind, k, "FIX", "accept")],
            t[(kind, k, "FIX", "reject")], t[(kind, k, "FULL", "accept")], t[(kind, k, "FULL", "reject")]))


if __name__ == "__main__":
    main()
