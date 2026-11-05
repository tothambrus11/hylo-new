# `unify`: tag-first dispatch in unification

## How it works

`TypeStore.unifiable(_:_:extending:handlingCoercionsWith:)` used to dispatch with `switch (self[a], self[b])` over about 20 `(let t as X, let u as X)` patterns. Each attempt builds a tuple of existentials and runs dynamic casts. That cost showed up as `TupleCache`, `tryCast` and generic-metadata entries in the profiles.

With the flag, after the shared prefix (substitution walk, `a == b`, the variable cases and the alias cases), `unifiableSameShape` does three things:
1. compares the operands' dynamic types once;
2. returns false on a mismatch;
3. otherwise casts each operand once and calls the same per-kind function.

## Why it is sound

- The set of `TypeTree` conformers is closed: 24 value types in `Sources/FrontEnd/Types`, with no classes and no conformers elsewhere. `self[n]` always returns one of these concrete types.
- So `x as X` succeeds iff `type(of: x) == X.self`.
- The original switch reaches a per-kind function iff both operands have the same dynamic type and that kind is structural. Every other case yields false, and the new code yields exactly the same.
- The per-kind functions, the coercion-handler call and the order of substitution side effects are unchanged.

**Caveat (debug builds only).** The baseline's `default:` branch asserts `tag(a) != tag(b)`. That assertion fires when two distinct `LiteralType`s are unified, which is reachable from user code (review unify-1). The flagged path returns false instead. Here the baseline is the broken side, and release builds behave identically.

Oracle: identical on all 216 corpus files and on 32 review programs.

## What it speeds up

Every unification. It is a constant factor that grows with the number of unifications: about −10% on the stdlib alone, less once `index`/`memberskip` have removed most unifications.

## Costs

None measurable. Same-kind nominal mismatches (Struct vs Struct) still go through a short chain of casts (review unify-2), and each operand is still projected twice (unify-3). The judged `typevec` idea (dense tag array next to the type store) would remove both.
