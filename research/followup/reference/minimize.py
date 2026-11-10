"""Shrinks a disagreement between the compiler and the reference by delta debugging.

    python3 minimize.py PROBLEM-ID QUERY CONFIG [NAME]

Starting from one query of a generated problem, it repeatedly tries to delete a declaration, a
premise, a requirement or a parameter, or to replace a type by one of its parts, and keeps the
change when the reference answer has the same verdict and the compiler's verdict under CONFIG
falls in the same class (harness.classify). The result is written to minimized/NAME.hylo and
minimized/NAME.json.
"""
import copy
import json
import os
import sys

import harness
import reference
import to_hylo
from reference import subterms, variables

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "minimized")


def key(world, config, path, twin=False):
    """(reference verdict, class) of the single query of `world`, or None if not comparable."""
    q = world["queries"][0]
    try:
        text = to_hylo.program(world)
    except (to_hylo.Unprintable, KeyError):
        return None
    try:
        a = reference.answer(world, q)
    except Exception:
        return None
    if a["verdict"] == "unspecified":
        return None
    r = harness.run_world(world, path, configs=(config,))[config]
    if r["status"] == "invalid":
        return None
    if r["status"] != "ok":
        return (a["verdict"], (a["count"] or 0) >= 2, r["status"].upper())
    v = r["verdicts"][0]
    k = harness.classify(a, v)
    if twin and (a["count"] or 0) >= 2:
        k = "agree" if v == "reject" else "AMBIGUITY-MISSED"
    return (a["verdict"], (a["count"] or 0) >= 2, k)


def shrink_type(t):
    """Smaller types that may replace `t`."""
    if t[0] == "app":
        for a in t[2]:
            yield a
        for i, a in enumerate(t[2]):
            for b in shrink_type(a):
                yield ("app", t[1], t[2][:i] + (b,) + t[2][i + 1:])
    elif t[0] == "proj":
        for b in shrink_type(t[1]):
            yield ("proj", b, t[2])


def variants(world):
    """Yields worlds that are smaller than `world`."""
    q = world["queries"][0]

    def with_query(**kw):
        w = copy.deepcopy(world)
        w["queries"][0].update(kw)
        return w

    for i in range(len(world["confs"])):
        w = copy.deepcopy(world)
        del w["confs"][i]
        yield w
    for i in range(len(q["reqs"])):
        yield with_query(reqs=q["reqs"][:i] + q["reqs"][i + 1:])
    for i, c in enumerate(world["confs"]):
        for j in range(len(c["premises"])):
            w = copy.deepcopy(world)
            del w["confs"][i]["premises"][j]
            yield w
        for t in shrink_type(c["type"]):
            if set(c["params"]) <= variables(t) and t[0] != "var":
                w = copy.deepcopy(world)
                w["confs"][i]["type"] = t
                yield w
    # Shrink the types of the goal and of the requirements.
    g = q["goal"]
    for k in (1, 2):
        if isinstance(g[k], tuple):
            for t in shrink_type(g[k]):
                yield with_query(goal=g[:k] + (t,) + g[k + 1:])
    for i, r in enumerate(q["reqs"]):
        for k in (1, 2):
            if isinstance(r[k], tuple):
                for t in shrink_type(r[k]):
                    r2 = r[:k] + (t,) + r[k + 1:]
                    yield with_query(reqs=q["reqs"][:i] + [r2] + q["reqs"][i + 1:])
    # Merge two parameters.
    for a in q["params"]:
        for b in q["params"]:
            if a < b:
                s = {b: ("var", a)}
                sub = lambda r: tuple(reference.substitute(x, s) if isinstance(x, tuple) else x for x in r)
                reqs = []
                for r in q["reqs"]:
                    r2 = sub(r)
                    if r2 not in reqs and not (r2[0] == "eq" and r2[1] == r2[2]):
                        reqs.append(r2)
                yield with_query(params=[p for p in q["params"] if p != b], reqs=reqs, goal=sub(g))


def prune(world):
    """Removes the parameters, structs and traits that nothing mentions."""
    q = world["queries"][0]
    used_vars, used_heads, used_traits = set(), set(), set()

    def visit(t):
        for s in subterms(t):
            if s[0] == "var":
                used_vars.add(s[1])
            elif s[0] == "app":
                used_heads.add(s[1])
            elif s[0] == "proj":
                used_traits.add(s[2])

    for r in q["reqs"] + [q["goal"]] + [p for c in world["confs"] for p in c["premises"]]:
        visit(r[1])
        if r[0] == "conf":
            used_traits.add(r[2])
        else:
            visit(r[2])
    for c in world["confs"]:
        visit(c["type"])
        used_traits.add(c["trait"])
        if c["impl"] is not None:
            visit(c["impl"])
    w = copy.deepcopy(world)
    w["queries"][0]["params"] = [p for p in q["params"] if p in used_vars]
    w["structs"] = {s: n for s, n in world["structs"].items() if s in used_heads}
    w["traits"] = {t: x for t, x in world["traits"].items() if t in used_traits}
    return w


def minimize(world, config, name, twin=False):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name + ".hylo")
    target = key(world, config, path, twin)
    assert target is not None and target[2] != "agree", "nothing to minimize: %r" % (target,)
    runs = 1
    changed = True
    while changed:
        changed = False
        for w in variants(world):
            runs += 1
            if key(w, config, path, twin) == target:
                world = w
                changed = True
                break
    world = prune(world)
    assert key(world, config, path, twin) == target
    text, _ = to_hylo.program(world)
    a = reference.answer(world, world["queries"][0])
    a.pop("goal", None)
    with open(path, "w") as f:
        f.write(text)
    with open(os.path.join(OUT, name + ".json"), "w") as f:
        json.dump({"config": config, "class": target[2], "reference": a, "world": world,
                   "compiler_runs": runs}, f)
    return world, target, a


if __name__ == "__main__":
    pid, qi, config = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    name = sys.argv[4] if len(sys.argv) > 4 else "%s-q%d-%s" % (pid, qi, config)
    for l in open(os.path.join(HERE, "problems.jsonl")):
        p = json.loads(l)
        if p["id"] == pid:
            break
    else:
        sys.exit("unknown problem " + pid)
    world = reference.load_world(p["world"])
    twin = bool(p["answers"][qi].get("twin"))
    world["queries"] = [world["queries"][qi]]
    world, target, a = minimize(world, config, name, twin)
    print("class:", target, "reference:", a)
    print(to_hylo.program(world)[0])
