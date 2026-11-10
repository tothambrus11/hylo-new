#!/usr/bin/env python3
"""Writes the header comment of each program of tests/: the verdict expected after the change,
the reason, and the current verdicts taken from results/tests-orders.jsonl.

usage: annotate_tests.py        (idempotent: replaces the header it wrote before)
"""
import json, os, re
root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
REASON = {
"01": "No cycle. `X` needs `A is P`; `Foo<X> is P` needs `X` and can never match `P<A>`.",
"02": "`X` is `B`, so `extension X` extends `B` and cannot affect the lookup of `Me` in `A` that defines `X`. Same shape as al1, al2 and al3.",
"03": "One consistent reading: `A.Inner` is the struct, `A.Inner.Foo` is `Int`, the given is `Int is P`, which does not make `A` a `P`. Same shape as n11, n12 and v6.",
"04": "`X` is `Int`, so `extension X` extends `Int` and cannot affect the lookup of `Foo` in `A`. Same shape as v01.",
"05": "One consistent reading: the first extension extends `Int`, the second `A.Inner`. This is the example under \"Limitation\" in soundness/5-declaration-order.md.",
"06": "No cycle: `X` needs `A is P`, `Foo<X> is Q` needs `X`, `Y` needs `Foo<X> is Q`, `Bar<Y> is P` needs `Y`.",
"07": "No consistent reading (first example of soundness/5-declaration-order.md): the signatures never become stable.",
"08": "No consistent reading: if `extension X` applies to `A`, `A.Me` is ambiguous; if it does not, `X` is `A` and it applies. The signatures never become stable.",
"09": "Two consistent readings (each local given can shadow the top-level one that the other needs); neither is reached from the empty table, so the signatures never become stable.",
"09b": "Same program as 09 with the two local givens swapped; the verdict must be the same.",
"10": "A cycle of aliases; the diagnostic must stay \"definition of 'X' refers to itself\" for this order.",
"11": "A requirement of a where clause cannot use the requirements after it. This rule is deliberate and must not change.",
"12": "The same requirements as 11 in the order that the rule allows.",
"13": "Both givens with subject `A.E` are givens for `Int`; neither can match `P<A>`.",
"14": "`A.E` needs `A is P`, which nothing provides: the given itself is `A.E is P`, whose subject is not known. The table is stable without it and the lookup of `E` fails.",
"15": "A given declared in the body of a generic function uses the function's requirement. Checks that the signature of the enclosing function is computed before its usings are read.",
"16": "Copy of Tests/CompilerTests/positive/typealiases.hylo.",
"17": "Copy of Tests/CompilerTests/positive/self-where-clause.hylo (`Self` in the extension's own where clause).",
"18": "Copy of Tests/CompilerTests/positive/local-given.hylo.",
"19": "Copy of Tests/CompilerTests/positive/generic-extension.hylo.",
"20": "Copy of Tests/CompilerTests/negative/trait-refinement.hylo; the two diagnostics must not change.",
"21": "A given in a function body shadows a top-level one. Must not change.",
"22": "A real ambiguity without any cycle: `X` is `A`, so `A` has two members `Me`.",
}
results = {}
for l in open(os.path.join(root, "results", "tests-orders.jsonl")):
    r = json.loads(l)
    acc = sum(o["n"] for o in r["outcomes"] if o["outcome"] == "accept")
    results.setdefault(os.path.basename(r["file"]), {})[r["config"]] = (acc, r["perms"])
def now(name, config):
    acc, n = results[name][config]
    if n == 1: return f"{config} {'accepts' if acc else 'rejects'} it"
    if acc == n: return f"{config} accepts it in all {n} orders tried"
    if acc == 0: return f"{config} rejects it in all {n} orders tried"
    return f"{config} accepts it in {acc} of {n} orders"
for line in open(os.path.join(root, "tests", "MANIFEST.tsv")):
    if line.startswith("#"): continue
    name, fix, expected = line.rstrip("\n").split("\t")
    path = os.path.join(root, "tests", name)
    lines = open(path).read().split("\n")
    head = []
    while lines and lines[0].startswith("//!"): head.append(lines.pop(0))
    while lines and (lines[0].startswith("// ") or not lines[0].strip()): lines.pop(0)
    key = re.match(r"\d+b?", name).group(0)
    # The headers of 06 and of the programs added by the review (06b, 23 and later) were written by
    # hand and say more than this script knows: leave them alone.
    if key == "06" or key not in REASON: continue
    comment = [f"// Expected after the change: {'accepted' if expected == 'accept' else 'rejected'}" +
               (", in every order of the top-level declarations." if results[name]["FULL"][1] > 1 else "."),
               f"// Reason: {REASON[key]}",
               f"// Currently: {now(name, 'base')}; {now(name, 'FULL')}."]
    open(path, "w").write("\n".join(head + comment + lines))
