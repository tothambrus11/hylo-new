# `reifymemo`: reify each subterm once

**Status:** sound performance flag, part of FULL.

## How it works

`TypeStore.reify(_:applying:withVariables:)` substitutes open variables, recursing into each child. Substitutions are often DAGs: `?a1 := P<?a2, ?a2>`, `?a2 := P<?a3, ?a3>`, … When such a DAG is walked as a tree, the cost is `2^k`. With `reifymemo`, one top-level call memoizes the result of each subterm by type identity.

## Why it is sound

Within a call, the substitution table and the policy are fixed, and reification is a pure function of the subterm's identity. The memo therefore returns exactly what the recursive call would compute, and the results are identical by construction. The corpus oracle is identical under FULL.

## What it speeds up

Resolutions with DAG-shaped bindings:

| program | baseline | FULL without | FULL with |
|---|---|---|---|
| occurs-dag-16 | 2860 ms | 2272 ms | 3.3 ms |
| occurs-dag-18 | ≈ 9 s | 8751 ms | 3.7 ms |

## Costs

One dictionary per top-level `reify` call that has variables.
