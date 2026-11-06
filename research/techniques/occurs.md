# `occurs` and `arrowenv`: occurs check in unification

**Status:** semantic fixes, part of the final configuration. `fixsubst` requires `occurs`.

## How it works

**`occurs`** checks a binding `?v := t` before it is made: unification refuses to bind a variable to a term that contains it once the current substitutions are applied (`TypeStore.occurs`).
- The walk covers every type kind with children: applications, tuples, metatypes, equalities, associated-type qualifications, arrows (including their environment), method bundles, implications, universal types, remote types, function pointers and aliases.
- Subterms already found free of `?v` are remembered. Substitutions are often DAGs, and walking them as trees cost 10.9 s on review2's `occurs-valid-24.hylo`; the walk is now linear (4 ms).
- In `match`, an occurs failure at the root records no coercion. It is now treated as a mismatch. Before, it was treated as a successful match, which let a `Void` value be passed as a proof of `Box<Void>` (review2 `o4-toplevel-occurs-full.hylo`, critical).

**`arrowenv`** makes an arrow's environment contribute to its type properties. Before, `[E](...) -> R` reported `hasVariable == false` even when `E` was a variable. That hid variables from the occurs check (a SIGSEGV through a method or closure environment: `b1d`, `a1`), from reification (free variables left in elaborations), from the summon memo, and from `eqsolve`'s closed-goal test (a valid program was refuted: `a4-env-var-goal.hylo`).

## Why it is sound

- A cyclic substitution has no finite solution, so refusing it removes no valid solution.
- The properties of an arrow must cover all its children. Leaving the environment out was a bug, not a choice.
- The corpus oracle is identical.

## What it speeds up

Nothing directly: it turns crashes (stack overflow in reification) into diagnostics.

## Costs

- A linear occurs check per variable binding.
- A one-time property union per arrow.
