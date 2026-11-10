# Keep the abstract model working when equalities are in scope (`absquotient`)

**Kind:** speed-up; results are unchanged. Extends `absmodel`.

## Problem

An equality requirement like `where A == B` lets a proof of `P<A>` serve as a proof of `P<B>`, through a coercion. The abstract model compares types syntactically, so it cannot see this. It therefore switched itself off in any scope with an equality given, and with it went the protection against looping and branching givens. A 9-line generic function with one `where A == B` and divergent givens ran out of memory; without the where clause it took 3 ms.

## How it works

When every equality given in scope is *ground* (no generic parameters of its own, no conditions, no unknowns):

1. Compute the congruence closure of those equalities over their subterms: which types are equal to which.
2. Mark as *opaque* every type constructor used to build a member of a class with more than one member. The constructors are nominal types, generic parameters, tuples and trait applications:
   - for `A == B`, the opaque constructors are just `A` and `B`;
   - for `Box<X> == Opt<Y>`, they are `Box` and `Opt` (and `X`, `Y` if they are equal to something).
3. Build the model of that scope from scratch, writing every application of an opaque constructor as `⊤`, in rules, facts and queries alike. The equality givens themselves are dropped.

If an equality given is not ground, the model stays inconclusive, as before.

## Why it is correct

What must hold: if two types are equal under the scope's equalities, then their abstractions match.

**Equal types.** Let `X` and `Y` be equal under the equalities. Look at the topmost position where they differ. There, both subterms belong to one non-trivial class: each is either a member of that class or congruent to one, and then built with the same constructor. Either way the constructor is opaque, so both sides are `⊤` at that position, and the abstractions agree everywhere above it.

**Generic givens.** The abstraction depends only on the constructor found at each position, so it commutes with substitution: abstracting an instance gives an instance of the abstraction. Every instance of a generic given is therefore covered, including instances that create terms equal to class members.

**Why per constructor and not per type.** Erasing only the *types* that appear in the equalities is not enough. With `Z == X` and `Box<X> == Opt<Y>`, the type `Box<Z>` appears nowhere, yet it equals `Opt<Y>`. Likewise, the instance `Opt<T>` of a generic given equals `Box<X>` when `T := Y`. A per-type erasure would leave `Box(⊤)` and `Opt(⊤)`, which do not match, and the model would wrongly refute a provable goal. Today's search happens never to exploit an equality between two different constructors when matching conformances, so this case cannot be observed. Correctness should not depend on that.

**Temporary assumptions** are covered by the argument of `absmodel`: they must themselves be proved from the scope, so the scope's equalities are the only ones that matter.

**Nested scopes.** A scope never reuses the file-level model. That model lacks the scope's local givens, so reusing it could refute a provable goal.

## What it speeds up

Divergent or branching givens in code with equality requirements:

| Program | Without | With |
|---|---:|---:|
| looping givens + `where A == B`, 2 branches | 1.1 s | 5 ms |
| looping givens + `where A == B`, 3 branches | out of memory | 3 ms |

## Cost

- A scope with equalities builds its model from scratch instead of extending its parent's.
- Equalities between compound types erase whole constructors, which weakens the model in that scope. Equalities between generic parameters, the common case, erase only those parameters.
