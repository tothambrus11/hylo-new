#!/usr/bin/env python3
"""Assigns every violating variant found under FULL to one of the causes of the README (D1..D8,
L1..L3), by relation, kind of variant, verdicts and error messages, and prints the number of
variants and of programs per cause. A violation that matches no rule is printed as `?`."""
import collections, json, os
from common import HERE


def cause(r):
    errs = " | ".join(r.get("errors", []) + r.get("base_errors", []))
    rel, kind = r["rel"], r["kind"]
    if "implicit resolution is too complex" in errs: return "D6"
    if rel == "r1": return "D1"
    if rel == "r7": return "D2"
    if rel == "r2": return "D3"
    if rel == "r4":
        if kind == "unused-param": return "L1"
        if "expects 1 type argument" in errs: return "L2"
        if kind == "taut-assoc": return "D3"
        if r["base_verdict"] == "reject" and r["verdict"] == "accept": return "D4"
        if "chain" in r["file"]: return "D6"
        if kind == "taut-param": return "D5"
    if rel == "r5":
        if kind == "intro-generic": return "D7"
        if "generic-member" in r["file"]: return "D7"        # a non-generic alias of `A<Void>`
        if kind == "intro-all-top": return "D1"
        return "D8"
    if rel == "r8" and r["kind"].startswith(("conf", "gconf")): return "L3"
    return "?"


def main():
    rows = {}
    for l in open(os.path.join(HERE, "data", "rows-FULL.jsonl")):
        r = json.loads(l); rows[(r["file"], r["rel"], r["vid"])] = r
    by = collections.defaultdict(list)
    for r in rows.values():
        if r.get("violation") and not r.get("invalid"): by[cause(r)].append(r)
    for c in sorted(by):
        rs = by[c]
        rels = sorted({r["rel"] for r in rs})
        print("%-3s %4d variants %4d programs  relations %s" % (c, len(rs), len({r["file"] for r in rs}), ",".join(rels)))
        if c == "?":
            for r in rs: print("     ", r["file"], r["vid"], r["base_verdict"], "->", r["verdict"])
    for c in ("D1",):
        for rel in ("r1", "r5"):
            rs = [r for r in by[c] if r["rel"] == rel]
            print("  D1 from %s: %d variants, %d programs" % (rel, len(rs), len({r["file"] for r in rs})))
    print("total", sum(len(v) for v in by.values()), "variants in", len({r["file"] for v in by.values() for r in v}), "programs;",
          len(rows), "variants checked in", len({k[0] for k in rows}), "programs")


if __name__ == "__main__":
    main()
