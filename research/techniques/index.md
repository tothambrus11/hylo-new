# `index`: head-constructor index of the visible givens

## How it works

Implicit resolution (`summon(_:in:where:…)`, Typer.swift) forms one thread per visible given for every subgoal, and runs `match` on each thread.

With the flag, each scope gets a `GivenIndex` that buckets the visible givens by the nominal head constructor of their conclusion:
- for `A is P` (i.e. `P<A>`) the bucket is `P`;
- for `S<T>` the bucket is `S`;
- givens whose head is not nominal (variables, ⊤-like heads) are "wildcards".

A subgoal with nominal head `k` only forms threads for `bucket[k]` plus the wildcards, merged in their original order. Each entry keeps its group offset, so penalties are unchanged. The index also records the list of coercion sources (`T ~ U` and `<T> T` heads), so that `canDeriveCoercions` iterates only over those.

## Why it is sound

**Skipped threads die anyway.** Suppose no coercion source is visible and no equality is assumed in the thread's environment. A given whose head constructor differs from the goal's fails at its first `match`:
- if the roots differ, unification reports only the root pair, which `match` rejects;
- if the mismatch is nested, `canDeriveCoercions` has no source to use and returns false.

Two facts make this hold:
- `canDeriveCoercion` compares a pair's components with the given's sides using `Typer.unifiable`, i.e. up to α-equivalence. So a given's own premise `T ~ U` cannot make it true for two distinct nominal heads.
- A dead thread produces no result and no child threads. Removing it changes neither the results nor the BFS layer in which they appear.

**Fallbacks.**
- Coercion sources visible: the full scan is used.
- Equality assumed in the thread's environment: the full scan is used.
- Declaration on the stack: the index is neither built nor used, which mirrors the `notOnStack` filtering of `givens(visibleFrom:)`.

**Penalties.** Every entry carries the offset of its group in `givens(visibleFrom:)`. Built-in givens are appended with the same offset as in the baseline.

Oracle: identical on all 216 corpus files. The review (`review/RESULTS-round2.md`, index) found no counterexample.

## What it speeds up

Resolution with many givens of different traits in scope, which is the common case. Measured: stdlib matches 41,452 → 15,051, and breadth80 49.9 s → 0.14 s.

It does **not** help, by construction, on:
- generic code with `where T == U` (any coercion source disables it; see review index-2 for a finer test);
- equality-heavy resolution (the round-3 `trans`/`assoceq` workloads).

## Costs

- One index per scope, built in O(#visible givens) when that scope first resolves something.
- `candidates()` re-sorts the merged bucket when wildcards exist (review index-4).
- The index is unavailable whenever a declaration is on the stack, which on the stdlib means most queries (index-3). `coesrc` and the `dtree` idea target that gap.
