# 1. Unrelated equalities make types interchangeable

**Status:** fixed by `fixsubst`, which must be used together with `occurs` and `eqsolve`.

## Symptom

The checker accepts calls whose equality requirements do not hold, as soon as *some* equality is in scope:

```hylo
fun g<T, U where T == U>() {}
fun f<V, W, D where V == W>() { g<D, V>() }   // accepted; nothing says D == V
```

The same happens with associated types and with nested positions. For example, `Box<D.X>` is accepted where `Box<A.X>` is expected, given only an unrelated `A.X == B.X`. Two unrelated equalities are enough to make any two types mentioned in equalities interchangeable (`test-programs/equalities/bug-assoc-eq-two-links.hylo`).

## Cause

To prove the requirement `D == V`, the checker tries the fact `V == W`. The fact does not match syntactically, so the checker *assumes* the equalities between the mismatching parts, and has to prove them afterwards. While matching, it had bound some unification variables, for example the type arguments of a built-in rule. When it assumes the part equalities, it throws those bindings away. A later step can then bind the same unification variables to different types, so the assumed equalities end up proved for *other* types than the ones that were compared. The chain of steps looks valid, but it proves `D == V` from `V == W`.

## Fix

Keep the bindings made during the match when the part equalities are assumed (`fixsubst`).

## Why it needs the other fixes

- **`occurs`.** Keeping bindings exposes cyclic bindings that used to be thrown away, and those crash the checker unless the occurs check refuses them.
- **`eqsolve`.** Correct equality proofs are longer than the bogus ones. Without a decision procedure, chains of more than about four equalities hit the 10-step cap, and some ill-typed programs exhaust memory before they are rejected.

## Tests

`test-programs/equalities/` holds the rejected variants: single equalities at call sites, given premises, associated types, nested positions and struct parameters. It also holds the valid chains, which are accepted.
