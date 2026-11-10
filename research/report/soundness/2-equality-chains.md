# 2. Equality chains time out or are wrongly rejected

**Status:** fixed by `eqsolve` and `eqmgu` (see `techniques/eqsolve.md` and `techniques/eqmgu.md`).

## Symptom

```hylo
trait P { type X }
fun check<T>(x: T) {}
fun g<V where V is P>() {}
fun f<T0, T1, T2, T3 where T0 == T1, T1 == T2, T2 == T3, T0 is P>(x: T3.X) {
  g<T3>()
  check<T0.X>(x)
}
```

With three links this takes about 0.3 s, and with eight links 1.1 s. With five or more links, valid programs are rejected once `fixsubst` is enabled. Requirements of the form `T == U` with an inferred `U` can exhaust memory in three lines.

## Cause

Equalities are proved by search, through reflexivity, symmetry and transitivity:
- each transitivity step introduces a fresh unification variable as the middle type, so the number of alternatives grows exponentially with the length of the chain;
- each link costs about two of the ten allowed steps.

## Fix

- **`eqsolve`** decides equality goals without unification variables by congruence closure, in `O(n log n)`, and builds a proof with the penalty the search would have charged.
- **`eqmgu`** answers goals of the form `?u ~ X` by binding `?u := X`, which is the most general solution.

The cases that are undecidable or NP-hard in general still use the search: generic equalities and equalities with unification variables inside types.
