# `absquotient`: keep the abstract model conclusive under ground equalities

**Status:** sound performance flag, part of FULL. Extends `absmodel`.

## How it works

`absmodel` refutes goals that are not in a depth-k least model of the givens. A given whose head is an equality used to make the model **inconclusive** (it refutes nothing), because a coercion along `A == B` lets a given for `P<A>` satisfy `P<B>`, and the syntactic model cannot see that. So a single `where A == B` turned off the protection against divergent givens. Review2's `div-eq-ovl-b3-1.hylo` (9 lines) ran out of memory under FULL, but took 3 ms without the where clause.

With `absquotient`, when every equality given in scope is ground (no parameters, no usings, no variables):
1. Compute the congruence closure of those equalities over their subterms. For this over-approximation, abstract and concrete projections of the same associated type are merged freely.
2. Every type in a non-trivial class, and every side of an equality, is *opaque*: its abstraction is `⊤`.
3. Build the model from scratch for that scope, with every clause abstracted through the opaque set and the equality clauses dropped. Queries are abstracted the same way.

If some equality given is not ground, the model stays inconclusive, as before.

## Why it is sound

- If `X = Y` in the theory of the ground equalities (congruence closure), then the abstractions of `X` and `Y` unify. Every position where they differ is a subterm in a non-trivial class, which is abstracted as `⊤`, and `⊤` unifies with anything.
- So a derivation that uses coercions maps to an abstract derivation without them: every coerced match becomes a syntactic match of abstractions.
- The other `absmodel` arguments (truncation monotone, dropped premises only add facts) are unchanged.
- The corpus oracle is identical under FULL.

## What it speeds up

Divergent or branching givens in a scope that also has an equality requirement:

| program | FULL without | FULL with |
|---|---|---|
| div-eq-ovl-b2-1 | 1117 ms | 5.1 ms |
| div-eq-ovl-b3-1 | 45 s, or out of memory | 4.2 ms |

## Costs

- A scope with ground equalities builds its model from scratch instead of extending its parent's model.
- One small congruence closure per such scope.
- More opaque types give a weaker model, so fewer refutations.
