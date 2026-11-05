# `memberskip`: skip extensions that cannot matter, without changing evaluation order

## How it works

A member lookup `q.n` through extensions (`resolve(_:declaredIn:applyingTo:)`, Typer.swift) visits every visible extension `e`. For each one it calls `applies(e, to: q)`, a unification-based resolution thread that decides whether `e` extends `q`. Only after that does it look for members named `n` in `e`. With many extensions this is O(#extensions) resolution threads per lookup. On members-big that is 4 million `applies` calls for 1000 lookups.

`memberskip` skips `e` when **both** of these hold:
1. `e` declares no member with the identifier of `n`, so it can contribute no candidate.
2. `applies(e, q, s)` provably has no observable effect.

Condition 2 requires that the extendee type of `e` is **already memoized** (it is read, never computed), and then either:
- **(a) Root failure.** The heads of the extendee and of `q` are of different kinds (e.g. struct vs tuple), or are two distinct nominal or machine types. Variables, aliases and generic parameters are excluded, because unification can see through them. Same-kind structural types (applications, tuples, arrows, …) are excluded, because they are unified component-wise. Under these conditions `unifiable` reports exactly one coercion, the root pair, and `match` returns `.next([])` without consulting any given. The heads' classification is cached per extension.
- **(b) Settled givens.** The type of every given visible from the scope is memoized, including givens currently on the stack. Implicit resolution inside `applies` then only reads memoized types, allocates fresh variables and fills caches with values any later computation reproduces. "All settled" is monotone, so it is cached per scope once true.

## Why it is sound (and why `names` was not)

The retired `names` flag skipped on condition 1 alone. The review showed that `applies` is **not** a pure query:
- it forces and memoizes `extendeeType(e)`;
- on its slow path, it forces the declared types of givens;
- it does both under `declarationsOnStack`, where results computed while a cycle is cut (including cycle errors) are memoized permanently.

Skipping the call therefore changed which lookup first evaluated an extendee or a given, and with it the result on programs with mutually dependent extensions (`review/names/n04`, `n11`, `n12` were rejected; `n01`, `n05` and `n17` changed).

`memberskip` only skips a call when everything that call could force is already memoized. So the order of first evaluations, and every cycle cut, is exactly the baseline's. The only differences are:
- fresh type-variable numbering;
- type-store insertion order, which the oracle normalizes and which no output depends on;
- fewer cache entries in `scopeToExtensionApplies`, which are recomputed to the same value if ever needed.

Oracle:
- identical on all 216 corpus files;
- identical on all 47 programs of `review/names/**`, where `names` differs on 12.

## What it speeds up

Member lookups in programs with many extensions, where the extensions are typed before the lookups or extend unrelated types.

| Workload | Baseline | `names` (unsound) | `memberskip` |
|---|---:|---:|---:|
| members-big (2000 extensions, 1000 lookups) | 23.8 s | 1.6 s | 2.0 s |
| stdlib typing | ≈950 ms | ≈630 ms | ≈650 ms |
| `applies` calls, stdlib | 7332 | 32 | 36 |
| `applies` calls, members-big | 4,008,000 | 1000 | 1000 |

Measured alone (`../round3/bench.md`): stdlib 1007 → 599 ms (1.7×), members-big 20.1 s → 1.37 s (14.7×), refine-8 78 → 48 and nestwide-8 99 → 67.

Early in a module, while some givens are still unsettled, lookups through universal extensions (`extension<T where T is P> T`) cannot be skipped, so `memberskip` does slightly more work than `names`.

## Costs

- A per-extension cache of the extendee head shape.
- A per-scope "all givens settled" bit. Checking it is O(#visible givens) until it becomes true; afterwards it is O(1).
- The per-lookup loop is still O(#visible extensions), but each iteration is a dictionary probe. A per-identifier extension index on top of `memberskip` would make it O(hits) and is the obvious next step.
