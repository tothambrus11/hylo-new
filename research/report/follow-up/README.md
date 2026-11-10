# Supporting studies

This folder holds the studies behind the second half of the report: measurements of the problem space, independent tests of the type checker, the designs of the larger mechanisms with their adversarial reviews, and the attacks on the implementations. `report.html` summarizes all of it; read these documents for the evidence and the details.

## Measurements of the problem space

| Question | Answer | Document |
|---|---|---|
| How does each cost grow with the size of a program? | 62 families of generated programs, with exact growth laws of the work counters. With the fixes and optimizations most families become linear or constant; the remaining exponential shapes are listed. The bound of ten steps counts the givens used in a whole derivation, and rejects valid programs. | `scaling/README.md` |
| What do errors cost, and does refuting goals in advance pay? | 1,050 single-mutation variants of valid programs. Errors are cheap without equality requirements; with them the existing implementation accepts 29 ill-typed variants and exhausts memory on 16. The abstract model makes one of 687 errors more than ten times cheaper. | `mutation/README.md` |
| Do real programs use equality constraints? | Yes: 6% to 24% of the functions of the Swift standard library, swift-collections and Rust's iterator library have one in scope, mostly through traits. The reasoning needed is shallow (chains of at most two). Four of their patterns were translated to Hylo. | `usage/README.md` |

## Independent tests

| Method | Result | Document |
|---|---|---|
| A specification of implicit resolution written from the compiler's tests, a reference resolver that follows it, and 21,500 generated queries | Found the unsoundness of generic conformances (problem 6 of the report) and of `Self.X` (problem 7), and six classes of valid goals that are rejected. No other wrong acceptance. | `reference/README.md`, `reference/JUDGEMENT.md`, `reference/spec.md` |
| Eight transformations that must not change a verdict, applied to 760 programs (15,206 variants) | 370 verdict changes, from declaration order, aliases of generic types (problem 9), the ranking of derivations and the bound. None is specific to the optimizations. | `metamorphic/README.md`, `metamorphic/JUDGEMENT.md` |

Each campaign was judged by a second reviewer who reproduced the findings; the judgements say which were confirmed, corrected or rejected.

## Designs

Each design states the problem with programs, compares options, gives the algorithm with its place in the code, an argument for its correctness with the assumptions it rests on, and a test plan. Each ends with the review of an adversarial reader who ran the first implementation.

| Design | Flags | Document |
|---|---|---|
| Order independence by computing signatures in rounds | `sigrounds` | `designs/order.md` |
| Requirements that mention another requirement; the bound on derivations; tabling | `premsubst`, `premcommit`, `heightbound` | `designs/engine.md` |
| Equalities without rewriting types | `eqindex`, `eqeager`; experiments `eqfilter`, `eqouter`, `eqclass` | `designs/eqnorm.md` |
| Overload resolution that returns the existing solution | `twins`, `cleanfirst`, `lookahead` | `designs/overload.md` |

The mechanism for associated types in signatures (`headsubst`) has no separate design; it is described in `../completeness/2-projections-in-signatures.md`.

The designs describe some corrections as "not built". They were built afterwards; the report and the documents in `../soundness`, `../completeness` and `../techniques` describe the implementation as it is.

## Attacks on the implementations

| Target | Programs | Document |
|---|---:|---|
| `assocsubst`, `abstractstrict` | 144 | `attack-assoc/README.md` |
| `sigrounds` | 104 | `attack-sigrounds/README.md` |
| `premsubst` | 141 | `attack-premsubst/README.md` |
| `headsubst` | 164 | `attack-headsubst/README.md` |

The attacks ran on earlier binaries. Their findings that were defects are fixed, and the programs serve as regression tests; `scripts/regress.py` lists the expected verdicts of the most important ones. Findings that remain are listed under Limitations in the report. One statement of the attack on `sigrounds` is superseded: `p/f04`, a top-level given with an inferred type, does depend on the order of declarations, under every configuration (`../soundness/5-declaration-order.md`, Limits).

## Test programs

- `design-order/tests`, `design-engine/tests`, `design-eqnorm/tests`, `design-overload/tests`: the programs of each design and its review, each with a comment stating the expected verdict and the reason.
- `headsubst/tests`, `sigrounds/tests`, `overload/`: programs written with the implementations.
- `reference/hand`, `reference/minimized`, `reference/judge/p`, `metamorphic/judge/progs`, `metamorphic/violations`: programs of the independent tests.
- `usage/benchmarks`: the translated library patterns and one reproducer per missing feature.
- `attack-*/p`: the attack programs.

## Scripts and data

`scripts/tcrun.py` runs programs under named configurations and is used by the others: `base` (the existing implementation), `MINR` (result-preserving techniques), `REC` (recommended), `NEW` (all techniques), and `FIX` and `FULL` (the fixes for problems 1 to 4, alone and with the techniques that preceded the other mechanisms). `regress.py` checks expected verdicts; `compare2.py` compares two configurations program by program, with the self-checking mode; `orders.py` type-checks a program in every order of its declarations; `final_timing.py` produces the timings of the report. `data/` holds their results for the final implementation; `../validation/README.md` summarizes them. `scripts/REVIEW-AND-PLAN.md` is the review of the first half of the work, from which these studies were planned.
