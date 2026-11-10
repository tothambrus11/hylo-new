# `absquotient`: keep the abstract model conclusive under ground equalities

**Status:** sound performance flag, part of FULL. Extends `absmodel`.

## How it works

`absmodel` refutes goals that are not in a depth-k least model of the givens. A given whose head is an equality used to make the model **inconclusive** (it refutes nothing), because a coercion along `A == B` lets a given for `P<A>` satisfy `P<B>`, and the syntactic model cannot see that. So a single `where A == B` turned off the protection against divergent givens. Review2's `div-eq-ovl-b3-1.hylo` (9 lines) ran out of memory under FULL, but took 3 ms without the where clause.

With `absquotient`, when every equality given in scope is ground (no parameters, no usings, no variables):
1. Compute the congruence closure of those equalities over their subterms. For this over-approximation, abstract and concrete projections of the same associated type are merged freely.
2. A **constructor** is *opaque* if some member of a non-trivial class is built with it: a nominal type, a generic parameter, a tuple cons, the empty tuple, a trait application.
3. Build the model from scratch for that scope. Every application of an opaque constructor is abstracted as `⊤`, in clauses, in facts and in queries, and the equality clauses are dropped.

If some equality given is not ground, the model stays inconclusive, as before. A nested scope never reuses the file-level model.

## Why it is sound

See `../round3/soundness/recheck3/README.md` §1 for the full argument and for the defects of the first version.
- **Equal types have unifiable abstractions.** If `X ≡ Y` in the congruence closure, then at the topmost position where they differ, both subterms belong to one non-trivial class. Each is either a member of that class or congruent to one, so it is built with an opaque constructor, and both abstract to `⊤` there.
- **Instances are covered.** The abstraction depends only on the constructor at each node, so it commutes with substitution. Every instance of a clause, including instances that create terms equal to class members, maps to an instance of the abstract clause.
- **Assumed givens are covered.** A refuted goal posed under assumed givens is not derivable from the scope, and the assumptions must themselves be derived from the scope before a thread completes, so pruning removes only threads that fail (a cut argument).
- **The first version was wrong.** Opacity was per *type* instead of per constructor, which missed `Box<Z>` when `Z == X` and `Box<X> == Opt<Y>`, and it missed clause instances. It also let a nested scope fall back to the file-level model. The current search cannot exploit equalities between different constructors, so no program showed the first defect, but the argument relied on that incompleteness.
- **Oracle.** The corpus oracle is identical under FULL.

## What it speeds up

Divergent or branching givens in a scope that also has an equality requirement:

| program | FULL without | FULL with |
|---|---|---|
| div-eq-ovl-b2-1 | 1117 ms | 5.1 ms |
| div-eq-ovl-b3-1 | 45 s, or out of memory | 4.7 ms |

## Costs

- A scope with ground equalities builds its model from scratch instead of extending its parent's model.
- One small congruence closure per such scope.
- Per-constructor opacity is coarser: `Box<X> == Opt<Y>` erases every `Box` and `Opt` term in the scope. Equalities between generic parameters, the common case, only erase those parameters.
