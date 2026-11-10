#!/usr/bin/env python3
"""Measures what the rounds cost, in work counters, on generated programs (binary eq17, FULL with
and without sigrounds), one process at a time (through tcb.sh).

usage: review_cost.py > results/review-cost.txt

- member(n): n givens whose where clause selects a member through an earlier requirement
  (`C.Element`); expected: 2 rounds.
- chain(n): n givens, each of which needs the previous one through an alias; expected: n + 2 rounds
  (there are n + 1 nodes).
"""
import os, re, subprocess, tempfile
here = os.path.dirname(os.path.abspath(__file__))
FIX = "occurs,fixsubst,eqsolve,extorder,arrowenv,eqmgu,givencheck,budget"
FULL = FIX + ",symindex,coesrc,traitindex,memberskip,unify,index,absmodel,absquotient,typevec,reifymemo"

def member(n):
    L = ["trait Collection { type Element }", "trait Equatable {}", "given Int is Equatable {}"]
    for i in range(n):
        L += [f"struct S{i} {{}}", f"struct W{i}<C> {{}}", f"given S{i} is Collection {{ type Element = Int }}",
              f"given <C where C is Collection, C.Element is Equatable> => W{i}<C> is Equatable {{}}"]
    return "\n".join(L) + "\n"

def chain(n):
    L = ["trait P { type E }", "struct A {}", "struct Foo<T> {}", "given A is P { type E = A }",
         "type X0 = A.E", "type F0 = Foo<X0>"]
    for i in range(n):
        L += [f"given F{i} is P {{ type E = F{i} }}", f"type X{i+1} = F{i}.E", f"type F{i+1} = Foo<X{i+1}>"]
    L.append(f"fun f(x: X{n}) {{}}")
    return "\n".join(L) + "\n"

def run(text, flags):
    with tempfile.NamedTemporaryFile("w", suffix=".hylo", delete=False) as f:
        f.write(text); path = f.name
    try:
        p = subprocess.run([os.path.join(here, "tcb.sh"), "eq17-4c2982653305", flags, "--count", path],
                           capture_output=True, text=True, timeout=600)
    finally:
        os.unlink(path)
    u = re.search(r"counters.user:(.*)", p.stdout)
    c = dict(x.split("=") for x in (u.group(1).split() if u else []))
    d = re.search(r"diagnostics: (\d+)", p.stdout)
    keys = ["sigrounds.nodes", "sigrounds.rounds", "sigrounds.restores", "summon.calls", "summon.matches"]
    return f"diagnostics={d.group(1) if d else '?'} " + " ".join(f"{k}={c.get(k, 0)}" for k in keys)

for name, text in [("member(10)", member(10)), ("member(40)", member(40)),
                   ("chain(4)", chain(4)), ("chain(8)", chain(8)), ("chain(16)", chain(16))]:
    print(f"{name:11} FULL            {run(text, FULL)}")
    print(f"{name:11} FULL,sigrounds  {run(text, FULL + ',sigrounds')}")
