# Validation

All figures are for the final implementation (`patches/`, 31 patches). The configurations are those of `report.html`, section "Using the implementation":

- **result-preserving**: the techniques that leave the results of the existing implementation unchanged;
- **recommended**: those, every fix, and the techniques that depend on the fixes;
- **all**: the recommended configuration with the techniques that the report advises against (among them the abstract model);
- **fixes 1–4**: the techniques with the fixes for soundness problems 1 to 4 only, without the mechanisms for problems 5 to 9 and for dependent requirements.

## Identical results on the test suite

A semantic dump records every expression type, name binding with the site of its declaration, conformance table and diagnostic, together with the witness selected at each elaborated site (coercions and implicit arguments). It is compared with that of the existing implementation on the compiler's 192 tests and 24 workloads. "Identical" means identical up to the terms of equality proofs, which the decision procedure constructs differently in two files.

| Configuration | Identical files |
|---|---|
| result-preserving | 216 / 216 |
| recommended | 216 / 216 |
| all | 216 / 216 |

The fixes change results only on programs that exercise the defects, and the test suite contains none. Data: `../follow-up/data/oracle-final.txt`.

## Verdicts on 1,651 programs

The corpus is the compiler's tests (204 files), the test programs of this archive (538) and the programs of the designs, attacks and independent tests in `../follow-up` (909).

**Recommended against all.** No program has a different verdict. Two rejected programs have a different message: without the abstract model, an underivable goal under divergent givens is reported by the resource bound.

**Fixes 1–4 against all.** 300 programs change verdict:

| Program set | Programs | Rejected → accepted | Accepted → rejected |
|---|---:|---:|---:|
| compiler tests | 204 | 0 | 0 |
| `test-programs/declaration-order` | 129 | 23 | 0 |
| `test-programs/unsimplified-projections` | 24 | 8 | 0 |
| `test-programs/equalities` | 223 | 2 | 6 |
| `test-programs/performance` | 76 | 3 | 0 |
| `test-programs/cycles-and-crashes` | 80 | 0 | 1 |
| `test-programs/abstract-model` | 6 | 0 | 0 |
| designs (`design-*`, `headsubst`, `sigrounds`) | 211 | 51 | 3 |
| attacks (`attack-*`) | 553 | 155 | 24 |
| independent tests (`reference`, `metamorphic`) | 115 | 5 | 15 |
| translated library patterns (`usage`) | 30 | 4 | 0 |

- *Rejected → accepted*: programs made independent of declaration order (problem 5), requirements and signatures that mention an associated type of another requirement, and one program that no longer times out.
- *Accepted → rejected*: ill-typed programs accepted through the associated types of generic conformances (problem 6), through `Self.X` (problem 7), through a refinement that satisfies itself (problem 8) or through an alias (problem 9), and the controls of the attacks.

Each folder of `../test-programs/` has an `INDEX.md` with the verdict of every program under the existing implementation, fixes 1–4 and the recommended configuration. Data: `../follow-up/data/compare-final.jsonl` (fixes 1–4 against all) and `compare-rec.jsonl` (all against recommended).

## Self-checking mode

With the flag `selfcheck`, the checker re-does the work that each technique avoids and compares the results (see the report, "Validation"). Over the same 1,651 programs under the recommended configuration:

- no violation;
- six programs exceed the time limit in this mode only (constructed divergent givens and one return-type overload chain), because the mode replays searches that the techniques avoid.

`../follow-up/scripts/regress.py` holds the expected verdicts of 152 programs, most of them former defects; all 152 are met under the recommended configuration and under all techniques, with the self-check on.

## Declaration-order fuzzing

Every order of the top-level declarations of each program, up to 24 orders, is type-checked with all techniques and the self-check on.

| Program set | Programs | Orders | Verdict depends on order: existing implementation | Final |
|---|---:|---:|---:|---:|
| `test-programs/declaration-order` | 129 | 2,876 | 52 | 0 |
| `follow-up/attack-sigrounds/p` | 104 | 2,316 | not measured | 1 |
| `follow-up/design-order/tests` | 42 | 900 | not measured | 0 |

The remaining program is a top-level given with an inferred type, which the existing implementation treats in the same way (`../soundness/5-declaration-order.md`, Limits). In five rejected programs a message differs with the order; four of them have a cycle, of which the message names a different declaration. Data: `../follow-up/data/order-final.jsonl`.

## Timings

Type-checking time in ms: minimum over three processes of the best of three in-process runs, on one core of an otherwise idle four-core virtual machine, with a memory limit of 2.4 GB and a time limit of 90 s. Differences under about 10% are noise.

| Program | Existing | Result-preserving | Recommended | All |
|---|---:|---:|---:|---:|
| standard library: representative code; no equality constraint | 605 | 126 | 134 | 118 |
| members-big: 2,000 extensions, 1,000 member lookups | 13,423 | 921 | 380 | 350 |
| breadth40: 40 unrelated conformances in scope | 4,985 | 38 | 43 | 47 |
| operator chain: `a + a + … + a`, 14 operators | 1,436 | 2.1 | 2.5 | 2.4 |
| overloads: 8 calls, 4 overloads each | 3,880 | 120 | 2.5 | 3.3 |
| return-type overloads: 8 nested calls, 3 overloads differing in their result type | 233 | 182 | 1.7 | 2.1 |
| div-branch: underivable goal, branching givens | 1,471 (rejected) | 153 (rejected) | 171 (rejected) | 1.8 (rejected) |
| div-loop-20: 20 cyclic goals (`P<T>` requires `P<T>`) | 115 (rejected) | 6.5 (rejected) | 7.6 (rejected) | 3.2 (rejected) |
| trans-8: chain of 8 equalities | 1,211 | 990 | 1.3 | 2.5 |
| assoceq-8: 8 equalities between associated types | 3,286 | 2,296 | 7.9 | 7.8 |
| assoceq-64: 64 equalities between associated types | memory exhausted | memory exhausted | 96 | 85 |
| coercion-cache: coercions derived through equalities | 2,526 | 1,905 | 3.2 | 4.2 |
| assocneg-8: ill-typed equality chain | 2,711 | 1,844 | 5.7 (rejected) | 6.8 (rejected) |
| conditional extension: `extension <T where T.Element == Flag> Box<T>` | 1,650 | 1,101 | 6.5 | 8.3 |
| open-equalities: equality requirements with an inferred argument | memory exhausted | memory exhausted | 202 | 196 |
| tuple-equalities: 31 equalities between 32-element tuples | memory exhausted | memory exhausted | 47 | 51 |
| divergence with equality: cyclic givens under `where A == B` | memory exhausted | memory exhausted | 2,205 | 4.3 |
| shared bindings: solution whose terms share subterms | 2,299 | 1,639 | 1.6 | 2.5 |
| Swift `Collection`: its signature translated: 7 traits, 14 equalities | 21,719 | 16,291 | 44 | 36 |
| Swift `StringProtocol`: translated | timeout (90 s) | timeout (90 s) | 44 | 38 |
| Swift initializers: `RangeSet.init`, `AnyCollection.init`, `Chain2Sequence`, translated | memory exhausted | memory exhausted | 16 | 16 |
| Rust `Flatten`: translated; conformance conditioned on an associated type | crash | crash | 691 | 586 |
| collection example: the program of the section on rejected valid programs | 36 (rejected) | 3.8 (rejected) | 3.6 | 4.7 |

Data: `../follow-up/data/final-timing.jsonl`, produced by `../follow-up/scripts/final_timing.py`.

## Contribution of each technique on the standard library

Techniques added greedily, each time the one that reduces the time most (minimum of 12 runs, on an earlier binary and in another session, hence the different base time):

| Technique added | Time (ms) |
|---|---:|
| none | 517 |
| `index` | 233 |
| skipping extensions that do not declare the name | 177 |
| `typevec` | 158 |
| `symindex` | 138 |
| `traitindex` | 126 |
| all techniques | 130 |

The other techniques have no measurable effect on the standard library; each matters on stress workloads or is a fix.

## Earlier data

`benchmarks.jsonl` and `test-programs.jsonl` are the raw rows of the timings and verdicts measured for fixes 1–4, kept for comparison.
