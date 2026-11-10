#!/usr/bin/env python3
"""Prints the table of section 5 of DESIGN.md from tests/current.jsonl and tests/observed.jsonl."""
import json, os
H = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cur, obs = {}, {}
for l in open(os.path.join(H, "tests", "current.jsonl")):
    j = json.loads(l); cur[(os.path.basename(j["program"])[:-5], j["config"])] = j["verdict"]
for l in open(os.path.join(H, "tests", "observed.jsonl")):
    j = json.loads(l); obs[(os.path.basename(j["program"])[:-5], j["config"])] = j["verdict"]
# name: (step, expected with the design as revised)
E = [
 ("s1-gain-conformance-generic", "2", "accepted"),
 ("s1-gain-conformance-two", "2", "accepted"),
 ("s1-gain-chain", "2", "accepted"),
 ("s1-gain-middle", "2", "accepted"),
 ("s1-gain-extension", "2", "accepted"),
 ("s1-gain-given", "2", "accepted"),
 ("s1-gain-static-method", "2", "accepted"),
 ("s1-gain-equal-parameters", "2", "accepted"),
 ("s1-gain-extension-concrete", "3", "accepted"),
 ("s1-gain-conformance-concrete", "3", "accepted"),
 ("s1-gain-equality-concrete", "3", "accepted"),
 ("s1-gain-given-concrete", "3", "accepted"),
 ("s1-gain-open-variable-a", "3", "accepted"),
 ("s1-gain-open-variable-b", "3", "accepted"),
 ("s1-gain-nested-dependent-given", "3", "accepted with `assocsubst`, `premsubst.stuck=0`; rejected without"),
 ("s1-keep-equality-generic", "2", "accepted, `eqsolve.premises=0`"),
 ("s1-keep-extension-generic", "2", "accepted, `eqsolve.premises=0`"),
 ("s1-keep-recursion", "2, 5", "accepted, same witness"),
 ("s1-keep-extension-sibling", "2, 5", "accepted, same witness"),
 ("s1-keep-result-type", "2", "accepted, same witness"),
 ("s1-keep-hypothesis", "2", "accepted, trace identical"),
 ("s1-reject-missing-requirement", "2", "rejected"),
 ("s1-reject-concrete-mismatch", "3", "rejected"),
 ("s1-reject-given-concrete", "3", "rejected"),
 ("s1-reject-ambiguous-both", "3", "rejected (two results)"),
 ("s1-reject-duplicate-requirement", "–", "rejected where the clause is declared"),
 ("s1-reject-cyclic-definition", "3", "rejected at the conformance, terminates"),
 ("s1-reject-capture-control", "–", "rejected"),
 ("s1-attack-capture-recursion", "5", "**rejected**"),
 ("s1-attack-capture-recursion-generic", "5", "**rejected**, also with `assocsubst`"),
 ("s1-attack-method", "6", "**accepted**"),
 ("s1-attack-initializer", "6", "**accepted**"),
 ("s1-attack-trait-requirement", "6", "**accepted**"),
 ("s1-attack-coerced-witness", "7", "**accepted**"),
 ("s1-attack-coerced-witness-own-projection", "7", "**accepted**"),
 ("s1-reject-other-conformance", "7, 8", "rejected with `premcommit`; accepted with step 7 alone"),
 ("s1-attack-other-conformance-equality", "7, 8", "rejected with `premcommit`; accepted with step 7 alone"),
 ("s1-attack-shadowed-requirement", "8", "rejected with `premcommit`; accepted without"),
 ("s1-attack-shadowed-local-given", "8", "rejected with `premcommit`; accepted without"),
 ("s1-attack-nonminimal-witness", "8", "rejected with `premcommit`; accepted without, given `assocsubst`"),
 ("s1-open-ambiguous-dependency", "8", "rejected with `premcommit`; accepted without; question 4"),
 ("s1-attack-shadowed-result-type", "8", "rejected with `premcommit`; accepted without, given `headsubst`"),
 ("s1-attack-shadowed-result-type-own", "–", "rejected"),
 ("s1-attack-where-order-a", "2", "accepted"),
 ("s1-attack-where-order-b", "2", "rejected by the bound (`summon.depthExhausted=1`); accepted under a height bound"),
 ("s1-open-parameter-type", "–", "rejected by `premsubst`; accepted with `headsubst`"),
]
names = {n for n, _, _ in E}
missing = sorted({k[0] for k in cur if k[0].startswith("s1-")} - names)
assert not missing, missing
print("| Program | Step | Expected, design as revised | Observed: first version (FULL + `premsubst` / NEW) | Currently (base / FULL) |")
print("|---|---|---|---|---|")
for n, step, e in E:
    print("| `%s` | %s | %s | %s / %s | %s / %s |" % (
        n, step, e, obs[(n, "FULL+premsubst")], obs[(n, "NEW")], cur[(n, "base")], cur[(n, "FULL")]))
