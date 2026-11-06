# `eqmgu`: solve `?v ~ X` by its most general unifier

**Status:** semantic fix, part of the final configuration. Meant to be used with `eqsolve`.

## How it works

Premises are discharged last-in-first-out, so an equality premise such as `T == U` in `<T, U where U is Q, T == U>` is often posed while `?U` is still open: `A0 ~ ?u`.
- `eqsolve` does not apply, because the goal is open.
- Search then offers reflexivity, symmetry, transitivity with a fresh middle variable, and every visible equality fact.
- Each of these binds `?u` differently, and each transitivity step opens new goals of the same form.

With `eqmgu`, a goal `?v ~ X` or `X ~ ?v` (where `?v` is a unification variable that does not occur in `X`) gets exactly one thread: reflexivity, binding `?v := X`, with the penalty of the built-in group.

## Why it is sound

- Binding `?v := X` is the most general solution. Every other solution binds `?v` to some `Y` with `X = Y` in the theory.
- The goals that remain mention `?v`. They are now closed under that equality, because coercions transport them along proved equalities (`match` plus `eqsolve`).
- So the other solutions add only duplicate derivations, which used to surface as *ambiguity*. Review2 `o2b-call-infer.hylo` (`pick(x)` with `A0 == A1, A1 == A2, A2 is Q`) was rejected as ambiguous; with `eqmgu` it is accepted, as by the baseline.
- Nothing new is accepted: the single thread is one of the threads search would have formed.
- The corpus oracle is identical.

## What it speeds up

Open equality premises:

| program | baseline | FIX | FULL |
|---|---|---|---|
| open-wide-4 (3 lines, valid) | out of memory | 496 ms | 202 ms |
| open-neg-0 (ill-typed) | out of memory | 10 ms | 2.7 ms |

`open-neg-0` previously took 24 s and 1.6 GB under FULL.

## Costs

An occurs check per open equality goal (linear, see `occurs`).
