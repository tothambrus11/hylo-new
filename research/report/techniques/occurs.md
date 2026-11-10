# Occurs check in unification (`occurs`, `arrowenv`)

**Kind:** correctness fix: crashes become errors. `fixsubst` requires it.

## Problem

Unification binds an unknown to a type without checking whether that type contains the unknown. The binding `?y := S<?y>` creates a cyclic solution, and substituting it overflows the stack:

```hylo
trait P<B> {}
trait R {}
struct S<T> {}
given <U> => U is P<U> {}
given <T where T is P<S<T>>> => T is R {}
fun needR<T where T is R>() {}
public fun main() { needR() }   // crashes the compiler
```

The same crash is reachable from ordinary expression inference.

## How it works

**`occurs`.** Unification refuses to bind an unknown to a type that contains it, once the current solution is applied.
- The check visits every kind of type that has parts: applications, tuples, metatypes, equalities, the qualification of associated types, functions, method bundles, implications, generic types, remote types, function pointers and aliases.
- Subterms already found free of the unknown are remembered, so the check is linear even when the solution shares structure.
- A failure at the top of a match is treated as a mismatch. Unification reports it without recording a coercion, so without this rule the match would have counted as a success. A `Void` value could then stand in for a proof of `Box<Void>`.

**`arrowenv`.** The environment of a function type (what a closure or bound method captures) now counts when computing whether a type contains unknowns. Before, `[E](...) -> R` claimed to have no unknowns even when `E` was one. That had three consequences:
- the occurs check was skipped, which crashed through method references;
- unknowns survived into the final types;
- a goal with an unknown was taken to be closed.

## Why it is correct

A cyclic solution describes no finite type, so refusing it removes no real solution. A type's properties must cover all its parts; leaving out the environment was simply an omission.

## Effect

Crashes become diagnostics. No test changes.

## Cost

A linear check per binding.
