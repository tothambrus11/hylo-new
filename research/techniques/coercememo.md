# `coercememo`: memoize coercion queries made under assumptions (negative result)

## How it works

`canDeriveCoercions(a, b, in: s, where: env)` is memoized by the baseline only when two conditions hold:
- the thread assumes nothing (`env.givens` is empty);
- the pair is closed.

Inside equality-heavy resolutions, threads carry assumed equalities, so every query is recomputed. With `coercememo`, those queries are memoized as well. The key is (scope, pair, the *types* of the assumed givens). This is done only when:
- no implicit declaration is on the stack, so `givens(visibleFrom:)` filters nothing;
- every given visible from the scope is settled (its type is memoized), so the computation only reads memos.

## Why it is sound

Under these two conditions `canDeriveCoercions` is a pure function of its key:
- assumed givens contribute only their types;
- type variables in the pair are compared structurally, by identity, and never through substitutions;
- every given's declared type is already memoized.

So a memoized answer equals what the baseline would recompute, and skipping the recomputation removes no side effect.

## Result: no gain

| Workload | Baseline | `coercememo` | Hits |
|---|---:|---:|---:|
| orig coercion-derivability-cache | 3952 ms | 3900 ms | 7461 |
| trans-8 | 1907 ms | 2262 ms | 6410 |
| assoceq-8 | 5480 ms | 5130 ms | 15111 |

The queries hit the memo but were already cheap. Profiles of these workloads put the cost in other places:
- `formThread`: opening the built-in symmetry and transitivity givens with fresh variables, and substituting;
- generic-metadata instantiation;
- type-store lookups.

It does not attack the real problem (see `research/round3/README.md`, "Equality reasoning"). Not recommended; kept only as a documented negative result.

## Costs

A dictionary keyed by arrays of types. It grows with the number of distinct assumption sets.
