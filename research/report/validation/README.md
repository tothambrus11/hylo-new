# Validation

## Identical results on the test suite

A semantic dump records every expression type, name binding (including implicit and witness arguments), conformance table and diagnostic. It is compared with that of the existing implementation on the compiler's 192 tests and 24 workloads:

| Configuration | Identical files |
|---|---|
| fixes only | 216 / 216 |
| all techniques | 216 / 216 |

## Adversarial test programs

The 520 adversarial programs in `../test-programs/` (which also holds a few minimal reproducers) were written to break each technique: unsound acceptance, crashes, order dependence, slow cases. Each runs with a 30 s limit.

| Outcome | Existing implementation | Fixes only | All techniques |
|---|---|---|---|
| accepted | 233 | 246 | 248 |
| rejected | 224 | 273 | 271 |
| timeout | 42 | 1 | 1 |
| crash | 21 | 0 | 0 |

The only timeout of the revised implementation is a return-type overload, a known limitation. Every changed verdict falls into one of these groups:
- an ill-typed program that is now rejected;
- a crash or timeout that now gets an answer;
- the mutually recursive extensions discussed in `../soundness/5-declaration-order.md`.

Each folder of `../test-programs/` has an `INDEX.md` with the verdict of every program. Raw rows are in `test-programs.jsonl`.

## Timings

Typing time in ms, best of three runs, one core of a 4-core machine. Differences under about 10% are noise.

| Program | Existing implementation | Fixes only | All techniques |
|---|---:|---:|---:|
| standard library | 616.0 | 388.7 | 151.4 |
| 2,000 extensions, 1,000 lookups | 13,171.6 | 543.9 | 355.7 |
| 40 unrelated conformances | 4,617.4 | 4,936.7 | 38.2 |
| 20 looping goals | 131.2 (rejected) | 91.4 (rejected) | 2.6 (rejected) |
| unprovable goal, branching givens | 1,350.2 (rejected) | 1,333.2 (rejected) | 1.8 (rejected) |
| tuple conformances | 50.7 (rejected) | 53.1 (rejected) | 3.0 (rejected) |
| chain of 8 equalities | 1,076.4 | 7.5 | 3.5 |
| associated-type equalities (5) | 1,442.0 | 51.3 | 46.9 |
| associated-type equalities (8) | 2,749.8 | 92.3 | 74.5 |
| many coercions | 2,165.1 | 12.2 | 3.9 |
| ill-typed equality chain | 2,486.5 | 78.6 (rejected) | 65.8 (rejected) |
| trait refinement | 43.9 | 23.6 | 4.0 |
| nested givens | 60.2 | 39.9 | 5.0 |
| 8 calls × 4 overloads | 3,880.4 | 157.7 | 117.8 |
| return-type overloads | 236.4 | 226.4 | 141.4 |
| conditional extension with T.Element == Flag | 1,405.8 | 16.6 | 14.5 |
| open equality requirements | out of memory | 344.2 | 189.0 |
| looping givens + where A == B | out of memory | 3,096.1 (rejected) | 3.1 |
| shared bindings | 2,323.8 | 2,163.8 | 2.3 |
| 31 tuple equalities | out of memory | 63.8 | 62.7 |
| deeply nested generic aliases | 23.2 (rejected) | 9.2 | 4.1 |

Raw rows are in `benchmarks.jsonl`.
