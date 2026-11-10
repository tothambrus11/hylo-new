"""Judge's independent validity check, for queries without associated types.

Model: types are finite trees; the parameters of a query stand for arbitrary types that satisfy
the where clause. The equalities of the where clause are solved by first-order unification
(parameters are the unknowns). A goal is VALID if it holds for the most general solution,
VACUOUS if the equalities have no solution, INVALID otherwise. A conformance goal holds if it has
a derivation in which every equality is syntactic identity after substitution.

This file shares no code with reference.py. It reads problems.jsonl and results.jsonl only.
"""
import json, collections, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))

def has_proj(t):
    return t[0] == "proj" or (t[0] == "app" and any(has_proj(a) for a in t[2]))

def T(t):
    if t[0] == "var": return ("v", t[1])
    return ("a", t[1], tuple(T(a) for a in t[2]))

def walk(t, s):
    while t[0] == "v" and t[1] in s: t = s[t[1]]
    return t

def occurs(v, t, s):
    t = walk(t, s)
    if t[0] == "v": return t[1] == v
    return any(occurs(v, a, s) for a in t[2])

def unify(a, b, s):
    a, b = walk(a, s), walk(b, s)
    if a == b: return True
    if a[0] == "v":
        if occurs(a[1], b, s): return False
        s[a[1]] = b; return True
    if b[0] == "v": return unify(b, a, s)
    if a[1] != b[1] or len(a[2]) != len(b[2]): return False
    return all(unify(x, y, s) for x, y in zip(a[2], b[2]))

def resolve(t, s):
    t = walk(t, s)
    if t[0] == "v": return t
    return ("a", t[1], tuple(resolve(x, s) for x in t[2]))

def match(pat, t, params, m):
    if pat[0] == "v" and pat[1] in params:
        if pat[1] in m: return m[pat[1]] == t
        m[pat[1]] = t; return True
    if pat[0] == "v": return pat == t
    if t[0] != "a" or pat[1] != t[1] or len(pat[2]) != len(t[2]): return False
    return all(match(p, x, params, m) for p, x in zip(pat[2], t[2]))

def subst(t, m):
    if t[0] == "v": return m.get(t[1], t)
    return ("a", t[1], tuple(subst(x, m) for x in t[2]))

class Unknown(Exception): pass

def count_derivations(world, reqs, trait, t, depth=0):
    """Number of derivations of trait<t>, capped at 2 (requirements are syntactic after substitution)."""
    if depth > 14: raise Unknown()
    n = 0
    for r in reqs:
        if r[0] == "conf" and r[2] == trait and r[1] == t: n += 1
    for c in world["confs"]:
        if c["trait"] != trait: continue
        m = {}
        if not match(T(c["type"]), t, set(c["params"]), m): continue
        if any(p not in m for p in c["params"]): raise Unknown()
        k = 1
        for p in c["premises"]:
            if p[0] == "conf":
                k *= count_derivations(world, reqs, p[2], subst(T(p[1]), m), depth + 1)
            else:
                k *= 1 if subst(T(p[1]), m) == subst(T(p[2]), m) else 0
            if k == 0: break
        n += k
    return min(n, 2)

def validity(world, q):
    """'valid' | 'invalid' | 'vacuous' | None (not applicable or unknown), and a derivation count."""
    rs = [tuple(r) for r in q["reqs"]]; g = q["goal"]
    ts = [r[1] for r in rs] + [r[2] for r in rs if r[0] == "eq"] + [g[1]] + ([g[2]] if g[0] != "conf" else [])
    if any(has_proj(t) for t in ts): return None, None
    for c in world["confs"]:
        if has_proj(c["type"]) or any(has_proj(p[1]) or (p[0] == "eq" and has_proj(p[2])) for p in c["premises"]):
            return None, None
    s = {}
    for r in rs:
        if r[0] == "eq" and not unify(T(r[1]), T(r[2]), s): return "vacuous", None
    if g[0] != "conf":
        return ("valid" if resolve(T(g[1]), s) == resolve(T(g[2]), s) else "invalid"), None
    reqs = [("conf", resolve(T(r[1]), s), r[2]) for r in rs if r[0] == "conf"]
    try:
        n = count_derivations(world, reqs, g[2], resolve(T(g[1]), s))
    except Unknown:
        return None, None
    return ("valid" if n else "invalid"), n

def main():
    P = {}
    for l in open(os.path.join(HERE, "..", "problems.jsonl")):
        p = json.loads(l); P[p["id"]] = p
    rows = collections.defaultdict(list)
    for l in open(os.path.join(HERE, "..", "results.jsonl")):
        r = json.loads(l); rows[(r["id"], r["config"])].append(r)
    def verdict(pid, c, i):
        rs = rows.get((pid, c))
        if not rs: return None
        whole = [r for r in rs if r["isolated"] is None]
        alone = [r for r in whole if not r.get("batch")]
        w = (alone or whole or [None])[-1]
        if w is not None and w["status"] == "ok": return w["verdicts"][str(i)]
        iso = [r for r in rs if r["isolated"] == i]
        if iso: return iso[-1]["verdicts"][str(i)] if iso[-1]["status"] == "ok" else iso[-1]["status"]
        return w["status"] if w else None
    cmp_ref = collections.Counter(); cmp_tc = collections.Counter(); na = collections.Counter()
    examples = collections.defaultdict(list)
    for pid, p in P.items():
        for i, q in enumerate(p["world"]["queries"]):
            a = p["answers"][i]
            mine, n = validity(p["world"], q)
            if mine is None:
                na[p["kind"]] += 1; continue
            refv = a["verdict"] + ("/" + a["sem"] if a["verdict"] == "underivable" else "")
            cmp_ref[(mine, refv, a["sem"])] += 1
            for c in ("base", "FIX", "FULL"):
                v = verdict(pid, c, i)
                if v is None: continue
                cmp_tc[(c, mine, v)] += 1
                if (mine == "invalid" and v == "accept") and len(examples[(c, "UNSOUND")]) < 10:
                    examples[(c, "UNSOUND")].append((pid, i))
            if a["verdict"] == "derivable" and mine != "valid": examples["ref-derivable-not-valid"].append((pid, i, mine))
            if a["sem"] != mine: examples["sem-differs"].append((pid, i, mine, a["sem"]))
            if q["goal"][0] == "conf" and mine == "valid" and a["verdict"] == "derivable":
                cmp_ref[("count", n, a["count"])] += 1
    print("queries without associated types checked:", sum(v for k, v in cmp_ref.items() if k[0] != "count"))
    print("not applicable, by kind:", dict(na))
    print("\nmine vs reference (mine, reference verdict, reference sem):")
    for k in sorted(cmp_ref, key=str): print("  ", k, cmp_ref[k])
    print("\ncompiler vs mine (config, mine, compiler):")
    for k in sorted(cmp_tc): print("  ", k, cmp_tc[k])
    for k, v in examples.items(): print(k, len(v), v[:10])

if __name__ == "__main__":
    main()
