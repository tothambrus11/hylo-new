#!/usr/bin/env python3
"""Random programs for model.py: compares the on-demand semantics, in every order of the
declarations, with the round semantics.

usage: fuzz_model.py N SEED OUT.jsonl

Generates N programs of 3 to 5 declarations (aliases, extensions and givens of one trait) over
two structs. For each, runs both semantics of model.py on every permutation and classifies it:

  stable-accept   on-demand accepts in every order
  stable-reject   on-demand rejects in every order
  order-dependent on-demand accepts in some orders only

(once for the plain on-demand semantics and once for the "checked" one)

and records the verdict of the round semantics, whether that verdict or the final types of the
aliases vary with the order (they must not), and, for stable-accept programs, whether the round
semantics computes the same alias types as the on-demand semantics. Writes one line per program
on which the semantics disagree or the on-demand verdict depends on the order to OUT.jsonl, and a
summary line at the end.
"""
import itertools, json, random, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import model

NAMES = ["A", "B", "Int"]
MEMBERS = ["M", "N"]

def texpr(rng, aliases, projections=True):
    """A type expression: a name, or a name followed by one or two member selections."""
    base = rng.choice(aliases) if aliases and rng.random() < 0.35 else rng.choice(NAMES)
    r = rng.random()
    if not projections or r < 0.45: return base
    e = base + "." + rng.choice(MEMBERS + ["E"])
    return e if r < 0.85 else e + "." + rng.choice(MEMBERS + ["E"])

def program(rng):
    k = rng.randint(3, 5)
    aliases = [x for x in ["X", "Y"] if rng.random() < 0.7]
    ds = [f"type {a} = {texpr(rng, aliases)}" for a in aliases]
    while len(ds) < k:
        r = rng.random()
        if r < 0.5:
            ds.append(f"extension {texpr(rng, aliases)} {{ type {rng.choice(MEMBERS)} = {texpr(rng, aliases, rng.random() < 0.3)} }}")
        elif r < 0.9:
            ds.append(f"given {texpr(rng, aliases)} is P {{ type E = {texpr(rng, aliases, rng.random() < 0.3)} }}")
        else:
            ds.append(f"extension <T where T is P> T {{ type {rng.choice(MEMBERS)} = {rng.choice(NAMES)} }}")
    rng.shuffle(ds)
    return ds

PRELUDE = "trait P { type E }\nstruct A { type N = B }\nstruct B {}\n"

def alias_types(c):
    return {d["name"]: c.memo.get(id(d)) for d in c.decls if d["kind"] == "alias"}

def main():
    n, seed, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
    rng = random.Random(seed)
    summary = {}
    with open(out, "w") as o:
        for i in range(n):
            ds = program(rng)
            od, ck, rv, rt, ot, rounds = [], [], set(), set(), set(), set()
            for p in itertools.permutations(range(len(ds))):
                text = PRELUDE + "\n".join(ds[j] for j in p) + "\n"
                decls = model.parse(text)
                c = model.Checker(decls)
                for d in decls: c.check(d)
                ck.append(model.ondemand(model.parse(text), True)[0] == "accept")
                od.append(not c.errors)
                if not c.errors: ot.add(json.dumps(alias_types(c), sort_keys=True))
                decls = model.parse(text)
                v, errs, k, final = model.rounds(decls, True)
                rv.add(v); rounds.add(k)
                rt.add(json.dumps(alias_types(final), sort_keys=True) if v == "accept" else "-")
            kind = "stable-accept" if all(od) else ("stable-reject" if not any(od) else "order-dependent")
            kind += ", checked: " + ("stable-accept" if all(ck) else ("stable-reject" if not any(ck) else "order-dependent"))
            same = (kind.startswith("stable-accept") and rv == {"accept"} and rt == ot)
            key = f"{kind} / rounds: {'|'.join(sorted(rv))}" + ("" if not kind.startswith("stable-accept") or rv != {"accept"} else (" same types" if same else " DIFFERENT TYPES"))
            if len(rv) > 1 or len(rt) > 1: key = "ROUNDS VARY " + key
            summary[key] = summary.get(key, 0) + 1
            summary["max rounds"] = max(summary.get("max rounds", 0), max(rounds))
            if (not same or len(rv) > 1) and not (not any(od) and not any(ck) and rv == {"reject"}):
                o.write(json.dumps({"program": ds, "class": key, "ondemand_accepting_orders": sum(od), "checked_accepting_orders": sum(ck), "orders": len(od)}) + "\n")
        o.write(json.dumps({"summary": summary, "programs": n, "seed": seed}) + "\n")
    for k, v in sorted(summary.items()): print(f"{v:7}  {k}")

if __name__ == "__main__":
    main()
