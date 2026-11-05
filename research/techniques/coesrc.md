# `coesrc`: remember the givens that can never derive a coercion

## How it works

When unification needs a non-syntactic equality between two parts (`a ~ b`), `match` asks `canDeriveCoercions(a, b)`. That call scans every visible given (plus the assumed ones) and, through `canDeriveCoercion(p, g)`, classifies each given's head:
- `<T> T` may derive anything (0b11);
- `T ~ U` may derive pairs that unify with its sides;
- anything else can never derive a coercion (0b00).

The baseline memoizes per (given, pair). Each new pair therefore repeats the `declaredType` → `contextAndHead` → cast sequence for every given. Profiles attributed 9.6% of stdlib typing to `canDeriveCoercion`.

With the flag, the first time a given is classified "never" (0b00), it goes into a set `notCoercionSources`, provided its type has no error and no implicit declaration is on the stack. Later scans skip the members of that set.

## Why it is sound

- The classification depends only on the given's declared type `t`, never on the pair.
- `canDeriveCoercions` ORs the 2-bit answers and stops early at 0b11. A skipped given contributes 0b00, so the accumulator and the early-exit point are unchanged.
- An early exit can only happen at a source.
- The skipped work is pure:
  - the given's declared type was already computed when it was classified;
  - the per-pair memo write it would have done is only read by `canDeriveCoercion` itself, which is no longer called for that given.
- **Guard 1.** Classification is recorded only when `t` has no error and no implicit is on the stack. A type computed under a cycle cut, which may be provisional, is therefore never cached.

Oracle: identical on all 216 corpus files, alone and together with `index`.

## What it speeds up

Any program whose resolution meets structural mismatches with many givens in scope:
- stdlib: 511k given visits skipped;
- generic-heavy user code: for example 2.2M skips on members-big.

Measured alone (`../round3/bench.md`):

| Workload | Baseline | `coesrc` |
|---|---:|---:|
| stdlib | 1007 ms | 814 ms (1.2×) |
| breadth40 | 7424 ms | 986 ms (**7.5×**) |
| refine-8 | 78 ms | 60 ms |
| nestwide-8 | 99 ms | 74 ms |
| wide-tuple-5 | 85 ms | 73 ms |

On equality-heavy workloads it gives nothing: there every given with an equality head is a source.

The gain is limited by what the `index` flag already removes, since `index` also keeps a list of coercion sources. `coesrc` still helps where `index` is unavailable: while a declaration is on the stack, which is most of the stdlib.

## Costs

- One `Set<Given>` per typer. A `contains` check per given visit replaces the two-level dictionary lookup.

## Relation to `givenfacts`

The judged idea `givenfacts` (`ideas/RESULTS-round2.md`) generalizes this:
- it also caches the source list per scope;
- it uses a "settled" test instead of "error-free and no implicit on the stack".

It would subsume `coesrc`.
