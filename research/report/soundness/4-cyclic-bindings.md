# 4. A type variable bound to a type containing itself crashes the compiler

**Status:** fixed by `occurs` and `arrowenv` (see `techniques/occurs.md`).

## Symptom

```hylo
given <U> => U is P<U> {}
given <T where T is P<S<T>>> => T is R {}
fun needR<T where T is R>() {}
public fun main() { needR() }
```

The compiler overflows its stack, with exit code 139. Closures and method references whose environment mentions the unification variable, and method bundles, crash the same way. Small programs can also hit the same cycle through ordinary expression inference.

## Cause

Unification has no occurs check, so it can bind `?y := S<?y>`. Substituting that solution never terminates.

Two further omissions hid unification variables from the check:
- the "contains unification variables" property of a function type ignored its environment;
- the check did not look inside method bundles.

## Fix

- Refuse cyclic bindings, checking every kind of type in time linear in the size of the shared term.
- Count the function environment in the type's properties.
- Treat an occurs failure at the top of a match as a mismatch. Without that rule, such a failure would have been counted as a successful match.
