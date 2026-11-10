# Skip extensions that cannot matter (`memberskip`)

**Kind:** speed-up; results are unchanged.

## Problem

Looking up a member `x.m` through extensions checks, for every visible extension, whether it applies to the type of `x`. That check is a small resolution, so a program with 2,000 extensions and 1,000 lookups runs 4 million of them.

## How it works

An extension is skipped when **both** of these hold:
1. It declares no member named `m`, so it cannot contribute a candidate.
2. Checking it is known to have no side effect. That requires the extension's extended type to be already computed, and then one of:
   - the check fails at the root: the extended type and the type of `x` have different kinds of head (a struct and a tuple, say) or two different nominal heads;
   - every given visible from the scope already has its type computed, so the check would only read computed values.

## Why it is correct

Checking an extension is **not** a pure query:
- it forces the computation of the extension's extended type;
- it may force the types of givens.

The computed results are remembered, and other lookups read them. Results computed while a declaration is hidden from lookups are remembered too. Skipping a check that would have computed something can therefore change *which* lookup computes it first, and with that the result of programs whose extensions depend on each other. The unrestricted version of this idea did exactly that (see the rejected approaches).

`memberskip` skips a check only when everything the check could compute is already computed. The order of computations, and every result, are then exactly as before.

## What it speeds up

| Program | Without | With `memberskip` alone |
|---|---:|---:|
| 2,000 extensions, 1,000 lookups | 20 s | 1.4 s (15×) |
| standard library | 1.0 s | 0.6 s (1.7×) |
| applicability checks, 2,000 extensions | 4,008,000 | 1,000 |

Early in a module, while some givens are not yet typed, lookups through extensions of *every* type (`extension <T where T is P> T`) cannot be skipped.

## Cost

A cache of each extension's head shape, and one "all givens typed" flag per scope.
