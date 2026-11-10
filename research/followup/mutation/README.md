# Error-path benchmark: how expensive is failing resolution in erroneous code, and does the abstract model help?

## What was asked

The abstract model (`absmodel` with `absquotient`, about 660 lines) makes failing implicit resolutions cheap. On valid code it gains nothing measurable. The plan (item 2.2) asks how expensive failing resolution is in realistic erroneous code, such as an editor type-checks continuously, and whether the model changes it. Its criterion: *adopt `absmodel` only if a meaningful share of mutants becomes much faster, say more than 1% of mutants by more than 10×; otherwise keep only a resource bound.*

The plan speaks of the time to report the error. The task restated the criterion as "more than 10× cheaper" and asked for ratios of `summon.matches`. The two readings give opposite answers here, so both are reported.

## Answer

**1. The abstract model does not make errors faster to report, although it often divides a small counter by more than 10.**

- *By time, or by work saved:* the criterion is not met. One ill-typed mutant out of 687 (0.15%, exact 95% interval 0.004% to 0.81%) is handled much faster with the model: a search that does not finish within 2.5 GB under MIN5 ends after one match. Among the 670 mutants that the existing checker rejects normally, no typing time improves by 10× (single runs), fifteen selected mutants timed five times each show no gain, and the model never saves more than 601 candidate matches.
- *By the ratio of `summon.matches` alone:* the threshold is exceeded. 113 of 670 rejected mutants (16.9%) need more than 10× fewer matches with the model. In 73 of them the unmutated program already has a ratio above 10 (66 are mutants of one file). In the other 40 (6.0%) the count drops from 12–295 matches to 0–2.
- *With the equality fixes in place* (FULL against FULL without the model, all 716 ill-typed mutants): the picture is the same. 116 have a ratio above 10 (16.2%), none of them costs 1,000 matches without the model, the largest saving is 600 matches, and no verdict or diagnostic changes. The one search that the model ends under MIN5 is also ended by `eqmgu`.

**2. In this sample, every error that the existing checker cannot handle is in a program with equality requirements (`where T == U`).** Of the 241 ill-typed mutants of such programs, 17 (7%) are not finished by base or MIN5 within the 2.5 GB memory cap or take 31 s and more, and 29 (12%) are wrongly accepted. Deleting one equality requirement is the typical case: of 66 such ill-typed mutants, 36 are rejected normally, 8 are not finished and 22 are accepted. All 475 ill-typed mutants of programs without equality requirements are rejected normally, at no more than 9.1× the cost of the unmutated program. These rates describe a sample in which almost all equality code comes from programs written to test the checker; they are not estimates for real code.

**3. FULL rejects all 46 mishandled mutants, in 1 to 234 ms at the default depth bound.** `eqsolve` and `eqmgu` are both needed for that; the search budget alone turns the 17 unfinished searches into rejections that take 0.8 to 6.7 s and leaves 27 of the 29 wrong acceptances accepted. Four of the 46 still reach the depth bound under FULL, and their cost grows by 2.6× for every two levels of depth (17,294 matches at depth 10, 118,552 at depth 14).

| Finding | Number |
|---|---|
| Mutants run | 1,050, from 294 source files (258 distinct contents); 999 distinct mutated programs |
| Still valid ("equivalent"), reported separately | 333 |
| Syntactically invalid, excluded | 1 |
| Ill-typed | 716 |
| – rejected normally by the existing checker | 670 |
| – not finished within 2.5 GB, or 31 s and more (base, MIN5) | 17 |
| – wrongly accepted by the existing checker | 29 |
| Rejected normally and costing more than 10× the unmutated program (`summon.matches`), base / MIN5 | 0 / 0 (maximum 9.1× / 7.5×) |
| Ill-typed mutants much faster with `absmodel` (time, or at least 1,000 matches saved, or a search ended) | 1 of 687 under MIN5; 0 of 716 under FULL (counters only; FULL was not timed with and without the model) |
| Rejected mutants with a `summon.matches` ratio above 10, MIN5 over MIN5 + model | 113 of 670 (40 where the source does not already have it) |
| Ill-typed mutants with a `summon.matches` ratio above 10, FULL without the model over FULL | 116 of 716 (43 where the source does not already have it) |
| Verdict or diagnostics differences, MIN5 versus base | 0 |
| Verdict or diagnostics differences, MIN5 + model versus MIN5 | 1 (the search it ends) |
| Verdict or diagnostics differences, FULL versus FULL without the model (all 1,050 mutants) | 0 |
| Verdict differences, FULL versus base | 46, all corrections (17 unfinished searches rejected, 29 wrong acceptances rejected) |

## What was done

**Sources.** Four groups of valid programs. Every source is accepted by all configurations.

| Group | Files with mutants | What it is |
|---|---:|---|
| `tests` | 85 | `Tests/CompilerTests/positive/*.hylo` |
| `workloads` | 35 | `research/workloads/*.hylo` and `round3/*.hylo`, the accepted ones (synthetic stress programs) |
| `stdlib` | 19 | the standard library, mutated in a private copy of the binary's directory (`bin/`); cost read from `counters.stdlib` |
| `corpus` | 155 | programs of `research/report/test-programs` that both the old and the new checker accept; added because the first three groups contain little code with equality requirements |

Left out: 20 workloads that are not accepted by every configuration (most are erroneous by design: `div-*`, `transneg-*`, `assocneg-*`) and 6 programs whose unmutated check takes more than 8 s under base. The list is in `sources-skipped.json`. The private copy of the standard library and of the binary is identical to the original, and gives the same counters.

The groups overlap. Thirty programs exist in two or three copies under different names (for example `trans-3.hylo` in `workloads` and twice in `corpus`), so the 275 user files have 239 distinct contents, and 51 mutants are byte-for-byte the same program as another mutant. Many of the remaining programs are size variants of one generator (`trans-N`, `transconf-N`, `assoceq-N`, `open-pos-chain-N`). Of the 131 files with an equality requirement, 4 are compiler tests and 127 are workloads or corpus programs; the standard library has none.

**Mutation operators** (`mutate.py`, syntactic, one mutation per mutant):

| Operator | Mutation |
|---|---|
| `del-given` | delete a conformance declaration: a `given`, one entry of `struct S is P & Q`, or a `refines` clause |
| `del-where-req` | delete one requirement of a generic clause (an equality, or a conformance requirement of a declaration without a body) |
| `del-bound` | delete a `T is P` requirement of a declaration that has a body |
| `repl-typearg` | replace a type argument (`f<A>()`, `Box<A>`) or a type of a function signature by another type in scope |
| `del-ext-member` | delete a member of an extension or of a conformance declaration |
| `del-type-member` | delete a member of a struct, enum or trait (added so that the standard library, which has few extensions, is covered) |
| `swap-args` | swap two arguments of a call (the operator does not know their types) |

**Sample.** `gen.py`, seed 20261110. Up to 50 mutants per group and operator (40 for `corpus`), files visited round-robin. Several cells have fewer sites than the quota (`analysis.md` section 1 gives every cell), and where few files offer sites one file fills the cell: `members.hylo` supplies 49 of the 50 `del-ext-member` mutants of `workloads` and 66 of the 670 rejected mutants.

**Runs.** Each mutant under base, MIN5, MIN5 + `absmodel,absquotient`, and FULL, with `--count`, a 120 s timeout, one process at a time (`run.py`, raw rows in `results.jsonl`). The reference for each mutant is its unmutated source under the same configuration (`baseline.jsonl`, `baseline-corpus.jsonl`). Afterwards every mutant and source was also run under FULL without `absmodel,absquotient` (`fullnoabs.py`). Thirty-five points behind the main claims were run a second time; all reproduce the recorded status, number of diagnostics and counters (`verify.md` section 1).

**Classification** is by the existing checker (base): rejected, still accepted ("equivalent"), syntax error, or abnormal end. The diagnostics of the 670 rejected mutants are all type errors (no coercion, missing member, argument type mismatch, missing implementation, no given instance, ambiguity). The 29 mutants that base accepts and FULL rejects were each read by hand: all 29 are ill-typed (a broken chain of equalities, or a wrong type in an equality requirement), so they are counted as ill-typed and reported separately.

## Results

### 1. Cost of an error relative to the unmutated program

Ratio of `summon.matches`, mutant over unmutated source, for the 670 mutants rejected normally:

| Group | Config | n | median | p90 | p99 | max | share above 2× | share above 10× |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| tests | base | 170 | 1.00 | 1.18 | 2.00 | 4.30 | 0.6% | 0% |
| tests | MIN5 | 170 | 1.00 | 1.12 | 2.34 | 3.78 | 2.4% | 0% |
| stdlib | base | 100 | 1.00 | 1.00 | 1.02 | 1.04 | 0% | 0% |
| stdlib | MIN5 | 100 | 1.00 | 1.01 | 1.05 | 1.09 | 0% | 0% |
| workloads | base | 242 | 0.99 | 1.90 | 4.64 | 9.05 | 4.1% | 0% |
| workloads | MIN5 | 242 | 1.00 | 1.38 | 5.00 | 7.46 | 2.9% | 0% |
| corpus | base | 158 | 0.78 | 1.00 | 1.97 | 2.00 | 0% | 0% |
| corpus | MIN5 | 158 | 0.50 | 1.00 | 1.45 | 2.00 | 0% | 0% |
| all | base | 670 | 1.00 | 1.18 | 2.42 | 9.05 | 1.6% | 0% |
| all | MIN5 | 670 | 1.00 | 1.08 | 2.46 | 7.46 | 1.6% | 0% |
| all | MIN5 + abs | 670 | 0.82 | 1.02 | 3.30 | 74.0 | 2.2% | 0.15% |
| all | FULL | 670 | 0.97 | 1.20 | 3.00 | 74.0 | 2.1% | 0.15% |

A normally rejected error costs about what the valid program costs. Many errors cost less, because checking stops early. Eleven mutants exceed 2× under base and eleven under MIN5. Ten of the eleven under base, and seven under MIN5, are in the overload-resolution workloads (`ovl-*`, `ovr-*`), where a wrong argument makes the solver explore more overloads; resolution of a failing conformance goal is not the cause. In absolute terms these are the costliest normal rejections under base: swapped arguments in `ovl-4-8.hylo` cost 2,455,274 matches and about 30 s, against 462,909 and about 4.5 s for the valid program (22,314 matches and about 1 s under MIN5). The others are small test programs where a few extra matches double a small count (`tests/del-type-member/001`, 3,974 matches against 1,455 under MIN5; `tests/del-given/004`, 1,566 against 364 under base). The single 74× under MIN5 + abs and FULL is 74 matches against 1.

In the standard library no error costs more than 1.11× the unmutated library. The largest extra cost is 1,602 matches under base and 376 under MIN5.

Typing times were recorded but the ratio of a mutant's time to its source's time is not usable: the sources were timed at another moment, under another load. Still-valid mutants of the standard library show the same apparent slowdown (median 1.75× to 2.09×) as rejected ones (1.80× to 2.11×). Run alternately with the unmutated library, five times each, two rejected library mutants take 0.85× to 1.07× its time (`verify.md` section 6).

### 2. The errors that are mishandled: equality requirements

Seventeen ill-typed mutants (16 distinct programs, from 14 distinct sources) are not handled in reasonable resources by base, MIN5 and MIN5 + abs, with one exception for the model. FULL rejects each of them with one or two diagnostics.

"abort" means the process was ended by the wrapper's cap of 2.5 GB of address space, after 30 to 110 s, with 1.5 to 2.1 GB resident. Times are single runs on a loaded machine.

| Mutant | Source | Mutation | base | MIN5 | MIN5 + abs | FULL: matches (ms) |
|---|---|---|---|---|---|---:|
| tests/repl-typearg/007 | `equality.hylo`:4 | `f1<T, T>()` → `f1<Void, T>()` | abort | abort | abort† | 5 (10) |
| tests/del-where-req/012 | `coercion-derivability-cache.hylo`:14 | delete `Box<U> == V` | abort | abort | abort | 153 (16) |
| tests/del-where-req/019 | same | delete `T == U` | abort | abort | abort† | 153 (10) |
| workloads/del-where-req/016 | `orig-coerc-cache.hylo`:14 (the same program) | delete `T == U` | abort | abort | abort† | 153 (10) |
| corpus/del-where-req/000 | `v-congr-5.hylo`:4 | delete `T.X == U.X` | abort | abort | abort† | 147 (3) |
| corpus/del-where-req/009 | `eq-regress-judge-x10b-ext-where-assoc.hylo`:9 | delete `T.Element == Flag` | 968,511 matches, 45 s | 968,216 matches, 31 s | 968,216 matches, 36 s | 217 (15) |
| corpus/del-where-req/013 | `a04-cond-given.hylo`:5 | delete `where T == U` | 2,037,755 matches, 61 s | abort; 2,037,475 matches, about 60 s, 1.9 GB resident with a 5 GB cap | abort† | 10 (9) |
| corpus/del-where-req/025 | `t4-generic-caller.hylo`:4 | delete `U.X == B` | abort | abort | abort† | 10,315 (72) |
| corpus/del-where-req/026 | `eq-regress-judge-o2-open-chain.hylo`:7 | delete `A0 == A1` | abort | abort | abort† | 295 (19) |
| corpus/del-bound/011 | `v5-generic.hylo`:6 | delete `U is P` | abort | abort | abort† | 17,294 (123) |
| corpus/del-bound/014 | `open-pos-chain-3.hylo`:3 | delete `A3 is Q` | abort | abort | abort | 2 (4) |
| corpus/del-bound/015 | `o4-open-chain.hylo`:7 | delete `A4 is Q` | abort | abort | **rejected, 1 match (8 ms)** | 1 (8) |
| corpus/del-bound/027 | `open-wide-1.hylo`:3 | delete `where A0 is Q` | abort | abort | abort† | 2 (11) |
| corpus/del-bound/028 | `open-pos-chain-2.hylo`:3 | delete `A2 is Q` | abort | abort | abort† | 2 (11) |
| corpus/del-given/031 | `v6-refl.hylo`:4 | delete `given A is P { type X = B }` | abort | abort | abort† | 145 (18) |
| corpus/repl-typearg/005 | `eq-regress-judge-o2b-call-infer.hylo`:4 | `A0` → `Int` | abort | abort | abort† | 75 (13) |
| corpus/repl-typearg/018 | `open-wide-1.hylo`:3 | `A0` → `Bool` | abort | abort | abort† | 2 (4) |

† Run in the main run only, where the cap was 1 GB for most mutants and 2.5 GB for some (not recorded per row). Where MIN5 + abs was compared with MIN5 at lower depth bounds, its counters are identical (section 6).

So at the 2.5 GB cap base aborts on 15 and finishes 2 (45 s and 61 s); MIN5 aborts on 16 and finishes 1 (31 s).

**These searches are bounded by the depth bound, and exponential in it.** With a lower bound they finish; the cost is multiplied by 3.3 to 4.4 for each level (`verify.md` section 3; base and MIN5 agree to within 300 matches):

| Mutant, under base | depth 6 | 7 | 8 | 9 | 10 (default) |
|---|---:|---:|---:|---:|---:|
| tests/repl-typearg/007 | 23,218 | 79,691 | 297,608 (6 s) | 1,177,775 (39 s, 1.2 GB) | abort at 2.0 GB resident |
| corpus/del-where-req/013 | 11,281 | 37,441 | 134,412 (3 s) | 510,653 (15 s, 0.4 GB) | 2,037,755 (61 s, 1.6 GB) |
| corpus/del-bound/015 | 28,585 | 122,212 | 541,289 (20 s, 0.7 GB) | abort at 2.0 GB resident | abort |

Each rejection at depths 6 to 9 comes with `summon.depthExhausted` > 0: the search was cut by the bound, it did not run out of candidates. At the default bound the one search that was run to the end needs 2.0 million matches, about a minute and 1.9 GB; the others need more.

All seventeen sources have equality requirements. Two of the errors are ordinary slips:

```hylo
fun f0<T>() { f1<Void, T>() }                 // examples/blowup-unsatisfied-equality.hylo
fun f1<T, U where T == U>() { f1<U, T>() }    // a call whose equality requirement does not hold
```

```hylo
// examples/blowup-extension-missing-equality.hylo (declarations of Collection, Box and Flag omitted here)
extension <T where T is Collection, T.Element == Flag> Box<T> {
  type Element = Flag
  fun first() -> Element { Flag() }
}
fun g<T where T is Collection>(b: Box<T>) {   // the caller forgot `T.Element == Flag`
  let f: Flag = b.first()                      // base: 968,511 matches, 45 s, then "no member 'first'"
}
```

The 29 wrongly accepted mutants (29 distinct programs, from 22 distinct sources) are the same kind of error: 22 deletions of one equality requirement that the body needs, and 7 type arguments replaced in a call with an equality requirement. Five of them cost base 20× to 97× the unmutated program before being accepted (0.6 to 2.2 s). The abstract model changes none of the 29. Example (`examples/wrongly-accepted-broken-chain.hylo`):

```hylo
fun f1<T, U where T == U>() { f1<U, T>() }
fun f2<T, U, V where T == U>() { f1<T, V>() }   // `U == V` deleted: base accepts after 69,302 matches; FULL rejects after 5
```

Outcome under base by kind of source:

| Source has an equality requirement | Ill-typed mutants | Rejected normally | Not finished within 2.5 GB, or 31 s and more | Wrongly accepted |
|---|---:|---:|---:|---:|
| yes | 241 | 195 (81%) | 17 (7%) | 29 (12%) |
| no | 475 | 475 (100%) | 0 | 0 |

In the sources with an equality requirement, by operator (`verify.md` section 2): deleting an equality requirement gives 66 ill-typed mutants, of which 36 are rejected normally, 8 are not finished and 22 are accepted; replacing a type argument gives 45, of which 3 are not finished and 7 are accepted; deleting a `T is P` requirement of a body gives 68, of which 5 are not finished; deleting a `given` gives 21, of which 1 is not finished; deleting a member gives 40, all rejected normally.

**Which technique handles the seventeen unfinished searches** (`attrib.py`, 600 MB cap; the cells that aborted at 600 MB were run again at 2.5 GB, `verify.md` section 5):

| Configuration | Rejected | Abort at 2.5 GB | Cost when rejected (`summon.matches`) |
|---|---:|---:|---|
| MIN5 + `budget` | 17 | 0 | 44,000 to 211,000 (0.8 to 6.7 s), with one diagnostic more than FULL |
| MIN5 + `eqmgu` | 17 | 0 | 2 to 234,000 (eight above 16,000) |
| MIN5 + `eqsolve` (4 mutants tried) | 1 | 3 | 1,205,345 (31 s) |
| FIX | 17 | 0 | 5 to 303, except two (10,455 and 27,374) |
| FIX without `eqmgu` | 17 | 0 | nine between 37,000 and 194,000, rejected by the budget |
| FIX without `eqsolve` | 17 | 0 | ten between 6,600 and 172,000 |
| FIX without `budget` | 17 | 0 | same as FIX |
| FULL without `absmodel,absquotient` | 17 | 0 | 2 to 303, except two (10,315 and 17,294) |

**Which technique rejects the 29 wrong acceptances** (`verify.py attribwrong`, 2.5 GB cap, 60 s; `verify.md` section 5b):

| Configuration | Rejected | Still accepted | Abort at 2.5 GB | Cost when rejected (`summon.matches`) |
|---|---:|---:|---:|---|
| MIN5 + `budget` | 2 (by exhausting the budget) | 27 | 0 | 31,279 |
| MIN5 + `eqmgu` | 27 | 0 | 2 | 74 to 1,160,121 (26 at 10,000 or more; up to 15 s) |
| MIN5 + `eqsolve` | 25 | 4 | 0 | 1 to 3,674 |
| MIN5 + `occurs,fixsubst,eqsolve` | 25 | 0 | 4 | 1 to 3,674 |
| FIX | 29 | 0 | 0 | 1 to 1,322, except two (10,742 and 11,030) |
| FIX without `eqmgu` | 29 (4 by exhausting the budget) | 0 | 0 | 1 to 1,322, except four between 66,000 and 106,000 (1.9 to 3.4 s) |
| FIX without `eqsolve` | 29 (17 with an extra diagnostic) | 0 | 0 | 74 to 148,321 (28 at 10,000 or more) |

`eqsolve` alone rejects 25 of the 29 wrong acceptances cheaply, and of the four unfinished searches tried it ends one, after 31 s. `eqmgu` alone ends all 17 unfinished searches and rejects 27 of the 29, but at up to a million matches. Together (FIX) they reject all 46, at 1 to 1,322 matches except four programs (10,455 to 27,374). The search budget alone turns the 17 unfinished searches into slow rejections and leaves 27 wrong acceptances in place. The abstract model is not needed: FULL without it rejects all 46 with the same diagnostics, and with it saves 1 to 302 matches on four of the seventeen.

**What remains expensive under FULL.** Over all 716 ill-typed mutants FULL has no abort and no timeout. Five cost more than 10× their unmutated source. Four of the five reach the depth bound (`summon.depthExhausted` > 0): `corpus/del-bound/011`, `corpus/del-where-req/025`, `corpus/repl-typearg/004` and `corpus/repl-typearg/011` (`v5-generic`, `t4-generic-caller`, `pending-var-2`, `pending-var-4`). Their cost depends on the bound, with or without the model (`verify.md` section 4):

| Mutant, under FULL | depth 10 | 12 | 14 |
|---|---:|---:|---:|
| corpus/del-bound/011 | 17,294 (0.13 s) | 45,281 (0.34 s) | 118,552 (0.89 s) |
| corpus/del-where-req/025 | 10,315 | 27,002 | 70,689 |
| corpus/repl-typearg/004 | 10,742 | 28,128 | 73,645 |
| corpus/repl-typearg/011 | 11,030 | 28,882 | 75,619 |

That is a factor of 2.6 for two levels; the unfinished searches under base and MIN5 grow by 11× to 19× for two levels. The fifth is 74 matches against 1.

### 3. What the abstract model changes

MIN5 against MIN5 + `absmodel,absquotient`, and FULL without the model against FULL:

| Measure of "more than 10× cheaper with the model" | Mutants | Of | Share | Exact 95% interval | Interval resampling source files |
|---|---:|---:|---:|---|---|
| *On MIN5* | | | | | |
| Unfinished search ended | 1 | 17 | – | – | – |
| Normally rejected: typing time ratio above 10 (single run, indicative) | 0 | 670 | 0% | 0% – 0.55% | – |
| Normally rejected: `summon.matches` ratio above 10 **and** at least 1,000 matches at stake | 0 | 670 | 0% | 0% – 0.55% | – |
| Normally rejected: `summon.subgoals` ratio above 10 | 0 | 670 | 0% | 0% – 0.55% | – |
| **All ill-typed mutants not wrongly accepted: much faster, or 1,000 matches saved, or search ended** | **1** | **687** | **0.15%** | **0.004% – 0.81%** | – |
| **Normally rejected: `summon.matches` ratio above 10, no floor** | **113** | **670** | **16.9%** | **14.1% – 19.9%** | **6.0% – 33.0%** |
| – of which the unmutated source has the same ratio | 73 | | | | |
| – of which the ratio appears with the error | 40 | 670 | 6.0% | 4.3% – 8.0% | 4.0% – 8.5% |
| – same count on distinct mutated programs | 99 | 627 | 15.8% | | |
| – same count on the plan's own sources (standard library and tests) | 8 (2 where the ratio appears with the error) | 270 | 3.0% (0.7%) | 1.3% – 5.8% (0.1% – 2.7%) | 1.0% – 5.6% (0% – 2.0%) |
| *On FULL (equality fixes in place)* | | | | | |
| Ill-typed: `summon.matches` ratio above 10, no floor | 116 | 716 | 16.2% | 13.6% – 19.1% | 6.0% – 31.2% |
| – of which the ratio appears with the error | 43 | 716 | 6.0% | 4.4% – 8.0% | 4.0% – 8.5% |
| Ill-typed: ratio above 10 **and** at least 1,000 matches without the model | 0 | 716 | 0% | 0% – 0.51% | – |
| Ill-typed: `summon.subgoals` ratio above 10 | 0 | 716 | 0% | 0% – 0.51% | – |
| Verdict, number or text of diagnostics changed by the model (all 1,050 mutants) | 0 | 1,050 | | | |

The one real gain on MIN5 is `corpus/del-bound/015` (`examples/blowup-rescued-by-absmodel.hylo`): the failing goal needs `Q<U>` for an unknown `U`, no conformance to `Q` exists, and the model refutes the goal before the equality search starts. Under FULL the same mutant costs 303 matches without the model and 1 with it.

The 40 mutants where the ratio appears with the error are of one kind: 35 are in a scope with equality requirements, where a conformance goal cannot hold because the only `T is P` requirement or the only matching `given` was deleted. MIN5 tries the equality rules (140 to 300 matches) and fails; the model answers after 0 or 1 match. They come mostly from the generator families `trans-N`, `transconf-N` and `*-open-chain`. The other 5 go from 12–21 matches to 0–2.

### 4. Why a ratio of `summon.matches` above 10 is not a time saving here

- **The saving is small in absolute terms.** Over all 670 rejected mutants the model never saves more than 601 candidate matches under MIN5 (median 14); over all 716 ill-typed mutants it never saves more than 600 under FULL (median 8). Outside `members.hylo` the largest savings under FULL are 525 to 579 matches, on standard-library mutants that cost about 4,000 with or without the error.
- **Time does not improve.** Fifteen mutants with the largest ratios or savings were timed five times each under MIN5 and MIN5 + abs, minimum kept (`timing.jsonl`): the ratios range from 0.34 to 2.2 in both directions, none near 10 (2.7 ms against 4.2 ms, 386 ms against 414 ms, and so on). In the single runs of the main experiment, 29 of the 670 rejected mutants are more than 2× faster with the model and 109 more than 2× slower; for programs typed in less than 20 ms the median time is about 1.3× higher with the model. This is noisy, but it is the direction expected from the cost of building the model, about 1 ms per program (3 ms for the standard library, `absmodel.micros`). FULL and FULL without the model were not timed against each other.
- **73 of the 113 are not about the error.** In `members.hylo` the valid program already shows 600 matches against 0; each of its 66 rejected mutants inherits the ratio. Its typing time is about 400 ms with or without the model.
- The model never increases `summon.matches`, in any mutant, on MIN5 or on FULL.

Two valid sources of the sample do gain much from the model, under MIN5 and under FULL: `div-eq-ovl-b2-1.hylo` (112,129 matches against 1; 1.6 s against 5 ms) and `div-eq-ovl-b2-0.hylo` (3,081 against 1). Both were written to exhibit that behaviour.

### 5. Differences in verdict or diagnostics (correctness)

Compared over the 1,049 syntactically valid mutants (`analysis.md` section 5 lists every one). The text comparison covers the first 12 diagnostics of each run.

- **MIN5 against base:** no difference in verdict, in number of diagnostics, or in the text of the diagnostics.
- **MIN5 + abs against MIN5:** one difference, `corpus/del-bound/015`: an abort becomes a rejection with the diagnostic that FULL also gives. No other difference in verdict, number or text.
- **FULL against FULL without the model:** no difference in verdict, number or text, on any of the 1,050 mutants.
- **FULL against base:** 54 differences, none of them a regression.
  - 17 unfinished searches rejected (section 2).
  - 29 mutants accepted by base and rejected by FULL. All 29 are ill-typed: base is unsound on them. Ids: `corpus/del-where-req/{002,006,014,015,022,027,031}`, `corpus/repl-typearg/{004,011,019,024,025,030,033}`, `tests/del-where-req/{001,016}`, `workloads/del-where-req/{000,004,007,015,021,033,036,037,038,040,045,047,048}`.
  - 8 mutants rejected by both with 2 diagnostics under base and 3 under FULL: `corpus/del-bound/002`, `workloads/del-bound/{031,033,035,036,039,040,041}` (all `assoceq-*`, a `Ti is P` requirement deleted). The third diagnostic is correct: deleting `Ti is P` makes `Ti.X` undefined, which breaks the chain of equalities, so the argument (of type `T8.X` in `assoceq-8`) no longer has type `T0.X`. Base misses it.
  - Where base and FULL give the same number of diagnostics, the text is the same.

Exact reproduction of any of them: `python3 repro.py <id> base full --diff`.

### 6. Dependence on the depth bound

`depth.py`, eight normally rejected mutants at `HYLO_TC_MAXDEPTH` 10, 12 and 14; `summon.matches`:

| Mutant | base 10 / 12 / 14 | MIN5 10 / 12 / 14 | MIN5 + abs 10 / 12 / 14 |
|---|---|---|---|
| workloads/swap-args/000 (`ovl-4-6`, 9.1× under base) | 594,929 at each | 5,169 at each | 5,121 at each |
| workloads/repl-typearg/041 (`ovr-3-8`, largest extra cost under MIN5) | 34,155 at each | 33,339 at each | 33,303 at each |
| tests/del-given/004 (`nullary-conformance`) | 1,566 / 1,850 / 2,134 | 32 / 36 / 40 | 11 / 11 / 11 |
| tests/del-given/020 (`refinement`) | 1,111 at each | 189 at each | 185 at each |
| workloads/del-bound/002 (`trans-8`) | 555 at each | 235 at each | 1 at each |
| corpus/del-given/011 (`o5-open-chain`) | 153 at each | 153 at each | 1 at each |
| workloads/del-given/023 (`chain8`) | 1,279 at each | 19 at each | 1 at each |
| stdlib/del-given/002 | 41,766 at each | 4,459 at each | 3,939 at each |

Among the 670 normally rejected mutants only `tests/del-given/004` reaches the bound at depth 10 (`summon.depthExhausted` > 0); the others cannot depend on a higher bound. Its cost grows linearly with the bound, and the model removes that growth (32 matches become 11).

The unfinished searches of section 2 are the opposite case. Three were run at depths 6 to 10 under base, MIN5 and MIN5 + abs (table in section 2): they finish at depths 6 to 8 or 9, their cost is multiplied by 3.3 to 4.4 per level, and MIN5 + abs has exactly the counters of MIN5 except on `corpus/del-bound/015`, which the model rejects after 1 match at every depth. The depth bound is what ends these searches; at its default value it ends them too late. The frontier budget ends them earlier (44,000 to 211,000 matches).

Under FULL, four ill-typed mutants reach the depth bound and grow by 2.6× per two levels (section 2); the model does not change them.

### 7. Which errors are expensive

- **Not expensive relative to the valid program:** a missing conformance, a missing member, a wrong type, swapped arguments, in code without equality requirements. 475 mutants, maximum 9.1× (an overload workload under base, where the valid program is already slow), nothing above 1.11× in the standard library.
- **Mishandled by base and MIN5, with or without the model:** an equality that cannot be proved, in a scope that has equality requirements. Deleting one equality of a `where` clause, deleting a conformance that an equality refers to, or passing the wrong type to a function or extension constrained by an equality. The checker then runs into the memory cap (15 or 16 mutants), takes 31 to 61 s (1 or 2), or finds a wrong proof and accepts (29).
- **Library-shaped code with a trait hierarchy** (`shapes.py`, a supplementary probe; `analysis.md` section 11). The sample has little code where a wrapper type conforms to each trait of a refinement chain when its argument does, which is how a generic library looks. Eighteen such programs were generated (chain of 1, 2 or 4 refinements; type nested 2, 4 or 8 deep), each with one wrong type argument so that the innermost conformance is missing. Under MIN5 the erroneous program costs 0.6× to 1.65× the valid one (at most 12,665 matches). Under base it costs up to 9.1× (at most 99,488 matches, a few seconds). The model reduces the failing case by 1% to 24% at depth 10 and by at most 37% at depth 14. The deepest erroneous programs do depend on the bound: the largest costs 12,665 matches at depth 10 and 43,967 at depth 14 under MIN5 (27,797 with the model). No search fails to finish.

## Decision input

1. **The abstract model and the error path.** Measured by time, which is how the plan words its criterion, the model is not justified by the error path: one mutant in 687 on MIN5 (upper bound 0.81%), none in 716 once the equality fixes are in. Measured by the ratio of `summon.matches` alone, 16% to 17% of rejected mutants pass the 10× mark (6% if the mutants that inherit the ratio from their source are left out, 3% on the standard library and the tests), with at most 601 matches saved each. A decision to keep the model has to rest on something other than this benchmark, for instance on valid programs such as `div-eq-ovl-b2-*`.
2. **The equality fixes.** `eqsolve` and `eqmgu` together are what makes the error path of equality code end quickly and what makes its verdicts correct on this sample: 46 of 241 ill-typed mutants of equality code (19%) are mishandled without them, and each of the two alone leaves some of the 46 expensive, unfinished or accepted.
3. **A resource bound alone** (`budget`) is a weak substitute: it turns the 17 unfinished searches into rejections that take 0.8 to 6.7 s, with an extra diagnostic, and it leaves 27 of the 29 wrong acceptances accepted.
4. **A residue under FULL.** Four ill-typed mutants still reach the depth bound under FULL, at 10,000 to 17,000 matches (0.1 to 0.2 s) for the default bound and 2.6× more for every two levels. Neither the model nor the default budget changes them. This matters if the depth bound is raised.

## Limits

- **The sources do not represent real code.** No large body of generic Hylo code exists. The standard library is small and uses no equality requirement; the tests are small; the workloads are synthetic; the corpus was written to probe the checker, much of it to probe equalities. The rates of 7%, 12% and "30 of 66 deleted equalities" describe this sample. They show that single ordinary edits to equality-constrained declarations reach the defects; they do not say how often real code would.
- **The mutants are not independent.** 258 distinct sources, many of them size variants of one generator; 51 duplicate mutants; one file (`members.hylo`) supplies a tenth of the rejected mutants. The exact intervals assume independence. The intervals that resample whole files are given where the count is not zero; for a count of zero they are degenerate, and the supportable statement is "none in 237 source files with rejected mutants".
- **The operators are syntactic and apply one error at a time.** 32% of the mutants are still valid (mostly swapped arguments of the same type and deleted declarations that nothing uses). Misspelled names, missing imports, errors inside expressions, incomplete code as an editor sees it while the user types, and several errors at once are not covered. "Still valid" means accepted by the type checker under base and FULL; of the 333, only the 61 deleted requirements were read by hand, and later compiler phases were not run.
- **`summon.matches` is not the whole cost.** It does not count the model's own work (`absmodel.work`, `absmodel.micros`; the time spent building the model is not recorded on the `absquotient` path) or the work of `eqsolve`. Time is the real cost and is noisy on this machine. The statements about time rest on fifteen mutants timed five times under MIN5 with and without the model, five mutant-and-source pairs timed alternately, and single runs elsewhere. No statement here establishes a time difference smaller than about 2×.
- **"Abort" is relative to the cap.** The cap is 2.5 GB of address space; aborts happen at 1.5 to 2.1 GB resident. One such search was run with a 5 GB cap and finishes (2.04 million matches, about 60 s, 1.9 GB). The others presumably finish with more memory; how long they take is not measured. In the main run most mutants had a 1 GB cap; every abort was run again at 2.5 GB under MIN5 and under base, and only three under MIN5 + abs.
- **Depth sweeps and attributions cover few mutants.** Eight normally rejected mutants, three unfinished searches, four mutants under FULL. The attribution of section 2 covers the 46 mishandled mutants only, with a handful of flag combinations; MIN5 + `eqsolve` was tried on 4 of the 17.
- **One cold run per mutant.** The benchmark does not simulate an editor, which re-checks after each keystroke with caches. Standard-library mutants measure a full re-check of the library with an empty user program, which is not what an editor does when the user's own code is wrong.
- **Correctness was judged narrowly.** The 29 programs that FULL rejects and base accepts were read by hand. Elsewhere FULL's diagnostics were only compared with base's (number, and text of the first 12).
- **The probe of section 7** covers one shape. Its valid programs with a list of 8 elements are rejected by every configuration because of the depth bound of 10; those three rows have no valid reference.

## Files

| File | Content |
|---|---|
| `mutate.py` | the mutation operators |
| `sources.py`, `baseline.jsonl`, `baseline-corpus.jsonl` | the sources and their unmutated results |
| `gen.py`, `mutants.jsonl`, `sources-skipped.json` | the sample (regenerated identically by `python3 gen.py`) |
| `run.py`, `results.jsonl` | the main run; restartable; the last row for a (mutant, configuration) pair is the valid one |
| `analyse.py`, `analysis.md`, `classified.jsonl` | the tables of the main run, and one row per mutant with its class and ratios |
| `repro.py` | `python3 repro.py <mutant-id> [config ...] [--diff] [--keep FILE] [HYLO_TC_MAXDEPTH=12]` |
| `attrib.py`, `attrib.jsonl` | the unfinished searches under MIN5 plus individual fixes (600 MB cap) |
| `recheck.py`, `recheck.jsonl` | the aborts of the main run at the default 2.5 GB cap, under MIN5 |
| `depth.py`, `depth.jsonl` | the depth sweep of the main experiment (depths 10, 12, 14; 6, 10, 14 for three unfinished searches) |
| `timing.py`, `timing.jsonl` | repeated timing of MIN5 against MIN5 + abs |
| `shapes.py`, `shapes/`, `shapes.jsonl` | the library-shaped probe |
| `fullnoabs.py`, `fullnoabs.jsonl` | every mutant and source under FULL without `absmodel,absquotient` |
| `verify.py`, `verify.jsonl` | second runs of 35 points; aborts at the 2.5 GB cap under base; depths 6 to 9; FULL at depths 10 to 14; the 29 wrong acceptances under individual fixes; mutant and source timed alternately. Each row has the peak resident memory. The sets `basecap2` and `bigcap` were run twice, so each of their points has two rows; the two agree. |
| `verify_report.py`, `verify.md` | the tables of `fullnoabs.jsonl` and `verify.jsonl` |
| `examples/` | four mutated programs quoted above |
| `post.sh`, `post2.sh` | the order in which the secondary scripts of the main experiment were run |
| `bin/` | private copy of the type-checker binary and of the standard library (restored to the original after every run) |

Configurations: base = empty; MIN5 = `index,memberskip,typevec,symindex,traitindex`; MIN5 + abs adds `absmodel,absquotient`; FIX and FULL as in `BRIEF.md`. Most of the main run used a 1 GB memory cap (`TCX_MEM_LIMIT_KB=1000000`) so that unfinished searches end quickly; the wrapper's default is 2.5 GB.
