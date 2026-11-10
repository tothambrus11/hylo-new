#!/usr/bin/env python3
"""Compares model.py with the type checker on the programs of tests/ that the model can parse.

usage: compare_model.py RESULTS.jsonl      (the file written by run-tests.sh)

For each program and each configuration in RESULTS.jsonl, prints the number of permutations the
binary accepts and the number the corresponding semantics of the model accepts over the same
permutations (base ~ ondemand, FULL ~ checked), then the verdict of the round semantics.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import model, orders

root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
print(f'{"program":52} {"config":5} {"perms":>5} {"binary":>6} {"model":>6}  rounds')
for l in open(sys.argv[1]):
    r = json.loads(l)
    if not r.get("split"): continue
    path = os.path.join(root, r["file"])
    header, chunks = orders.split(open(path).read())
    ps = model.permutations(path, len(chunks), r["fixed"], r["perms"])
    assert len(ps) == r["perms"]
    try:
        acc, verdicts, nr = 0, set(), set()
        for p in ps:
            text = "\n".join(chunks[i] for i in p)
            if model.ondemand(model.parse(text), r["config"] != "base")[0] == "accept": acc += 1
            v, _, k = model.rounds(model.parse(text))
            verdicts.add(v); nr.add(k)
    except (SyntaxError, KeyError, IndexError) as e:
        print(f'{os.path.basename(path):52} {r["config"]:5} {r["perms"]:5}  (outside the subset of the model)')
        continue
    binary = sum(o["n"] for o in r["outcomes"] if o["outcome"] == "accept")
    mark = "" if binary == acc else "   <-- differs"
    print(f'{os.path.basename(path):52} {r["config"]:5} {r["perms"]:5} {binary:6} {acc:6}  {"/".join(sorted(verdicts))} in {max(nr)} round(s){mark}')
