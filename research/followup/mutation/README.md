# Error-path benchmark: how expensive is failing resolution in erroneous code, and does the abstract model help?

## What was asked

The abstract model (`absmodel` with `absquotient`, about 660 lines) makes failing implicit resolutions cheap. On valid code it gains nothing measurable. The plan (item 2.2) asks whether failing resolution is expensive in realistic erroneous code, such as an editor type-checks continuously, and sets the criterion: *adopt `absmodel` only if more than about 1% of rejected mutants become more than 10× cheaper with it.*

## Answer

**The criterion is not met.** One erroneous mutant out of 687 (0.15%, exact 95% interval 0.004% to 0.81%) becomes more than 10× cheaper with the abstract model in any sense that corresponds to work saved. Among the 670 mutants that the existing checker rejects normally, none does (0%, interval 0% to 0.55%).

The same data give a second, stronger result that was not asked for. **Erroneous code is expensive only when the program uses equality requirements (`where T == U`), and there the existing checker fails outright**: of 241 ill-typed mutants of such programs it exhausts memory on 16, takes 45 s on one (together 7%), and wrongly accepts 29 (12%). The abstract model changes one of these 46. The equality fixes of FULL (`eqsolve` with `eqmgu`) handle all 46 correctly, the worst one in about 0.15 s.

| Finding | Number |
|---|---|
| Mutants run (4 configurations each) | 1,050, from 294 source files |
| Still valid ("equivalent"), reported separately | 333 |
| Syntactically invalid, excluded | 1 |
| Ill-typed | 716 |
| – rejected normally by the existing checker | 670 |
| – memory exhausted by the existing checker (16) or 45 s for one error (1) | 17 |
| – wrongly accepted by the existing checker | 29 |
| Rejected normally and costing more than 10× the unmutated program (`summon.matches`), base / MIN5 | 0 / 0 (maximum 9.1× / 7.5×) |
| Ill-typed mutants more than 10× cheaper with `absmodel`, by work saved | 1 of 687 |
| Verdict or diagnostics differences, MIN5 versus base | 0 |
| Verdict or diagnostics differences, MIN5 + abstract model versus MIN5 | 1 (the blow-up it removes) |
| Verdict differences, FULL versus base | 46, all corrections (17 blow-ups rejected, 29 wrong acceptances rejected) |

The criterion as literally worded, a ratio of `summon.matches`, gives a different number: 113 of 670 (16.9%). Section 4 explains why this number does not measure cost: the model saves at most 601 candidate matches in any mutant, and repeated timing shows no time difference.

## What was done

**Sources.** Four groups of valid programs. Every source is accepted by all four configurations.

| Group | Files with mutants | What it is |
|---|---:|---|
| `tests` | 85 | `Tests/CompilerTests/positive/*.hylo` |
| `workloads` | 35 | `research/workloads/*.hylo` and `round3/*.hylo`, the accepted ones (synthetic stress programs) |
| `stdlib` | 19 | the standard library, mutated in a private copy of the binary's directory (`bin/`); cost read from `counters.stdlib` |
| `corpus` | 155 | programs of `research/report/test-programs` that both the old and the new checker accept; added because the first three groups contain little code with equality requirements |

Left out: 20 workloads that are not accepted by every configuration (most are erroneous by design: `div-*`, `transneg-*`, `assocneg-*`) and 6 programs whose unmutated check takes more than 8 s under base. The list is in `sources-skipped.json`. The unmodified copy of the standard library gives the same counters as the original.

**Mutation operators** (`mutate.py`, syntactic, one mutation per mutant):

| Operator | Mutation |
|---|---|
| `del-given` | delete a conformance declaration: a `given`, one entry of `struct S is P & Q`, or a `refines` clause |
| `del-where-req` | delete one requirement of a generic clause (an equality, or a conformance requirement of a declaration without a body) |
| `del-bound` | delete a `T is P` requirement of a declaration that has a body |
| `repl-typearg` | replace a type argument (`f<A>()`, `Box<A>`) or a type of a function signature by another type in scope |
| `del-ext-member` | delete a member of an extension or of a conformance declaration |
| `del-type-member` | delete a member of a struct, enum or trait (added so that the standard library, which has few extensions, is covered) |
| `swap-args` | swap two arguments of a call |

**Sample.** `gen.py`, seed 20261110. Up to 50 mutants per group and operator (40 for `corpus`), files visited round-robin so that no large file dominates. Several cells have fewer sites than the quota; the table in `analysis.md` section 1 gives every cell.

**Runs.** Each mutant under base, MIN5, MIN5 + `absmodel,absquotient`, and FULL, with `--count`, a 120 s timeout, one process at a time (`run.py`, raw rows in `results.jsonl`). The reference for each mutant is its unmutated source under the same configuration (`baseline.jsonl`, `baseline-corpus.jsonl`).

**Classification** is by the existing checker (base): rejected, still accepted ("equivalent"), syntax error, or abnormal end. The 29 mutants that base accepts and FULL rejects were each read by hand: all 29 are ill-typed (a broken chain of equalities, or a wrong type in an equality requirement), so they are counted as ill-typed and reported separately.

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

A normally rejected error costs about what the valid program costs. Many errors cost less, because checking stops early. Eleven mutants exceed 2× under base and eleven under MIN5. Most are in the overload-resolution workloads (`ovl-*`, `ovr-*`), where a wrong argument makes the solver explore more overloads; resolution of a failing conformance goal is not the cause. The others are small test programs where a few extra matches double a small count (the largest: `tests/del-type-member/001`, 3,974 matches against 1,455 under MIN5; `tests/del-given/004`, 1,566 against 364 under base). The single 74× under MIN5 + abs and FULL is 74 matches against 1.

Typing times agree within noise (`analysis.md` section 2). They are indicative only: other jobs ran on the machine.

In the standard library no error costs more than 1.11× the unmutated library. The largest extra cost is 376 matches under MIN5, for deleting `given Int is AdditiveArithmetic`.

### 2. The expensive errors: equality requirements

Seventeen ill-typed mutants do not finish normally under base, MIN5 and MIN5 + abs (one exception, below). FULL rejects each of them with one or two diagnostics.

| Mutant | Source | Mutation | base, MIN5 | MIN5 + abs | FULL: matches (ms) |
|---|---|---|---|---|---:|
| tests/repl-typearg/007 | `equality.hylo`:4 | `f1<T, T>()` → `f1<Void, T>()` | memory | memory | 5 (10) |
| tests/del-where-req/012 | `coercion-derivability-cache.hylo`:14 | delete `Box<U> == V` | memory | memory | 153 (16) |
| tests/del-where-req/019 | same | delete `T == U` | memory | memory | 153 (10) |
| workloads/del-where-req/016 | `orig-coerc-cache.hylo`:14 | delete `T == U` | memory | memory | 153 (10) |
| corpus/del-where-req/000 | `v-congr-5.hylo`:4 | delete `T.X == U.X` | memory | memory | 147 (3) |
| corpus/del-where-req/009 | `eq-regress-judge-x10b-ext-where-assoc.hylo`:9 | delete `T.Element == Flag` | 968,511 matches, 45 s (base); 968,216, 31 s (MIN5) | 968,216, 36 s | 217 (15) |
| corpus/del-where-req/013 | `a04-cond-given.hylo`:5 | delete `where T == U` | memory | memory | 10 (9) |
| corpus/del-where-req/025 | `t4-generic-caller.hylo`:4 | delete `U.X == B` | memory | memory | 10,315 (72) |
| corpus/del-where-req/026 | `eq-regress-judge-o2-open-chain.hylo`:7 | delete `A0 == A1` | memory | memory | 295 (19) |
| corpus/del-bound/011 | `v5-generic.hylo`:6 | delete `U is P` | memory | memory | 17,294 (123) |
| corpus/del-bound/014 | `open-pos-chain-3.hylo`:3 | delete `A3 is Q` | memory | memory | 2 (4) |
| corpus/del-bound/015 | `o4-open-chain.hylo`:7 | delete `A4 is Q` | memory | **rejected, 1 match (8 ms)** | 1 (8) |
| corpus/del-bound/027 | `open-wide-1.hylo`:3 | delete `where A0 is Q` | memory | memory | 2 (11) |
| corpus/del-bound/028 | `open-pos-chain-2.hylo`:3 | delete `A2 is Q` | memory | memory | 2 (11) |
| corpus/del-given/031 | `v6-refl.hylo`:4 | delete `given A is P { type X = B }` | memory | memory | 145 (18) |
| corpus/repl-typearg/005 | `eq-regress-judge-o2b-call-infer.hylo`:4 | `A0` → `Int` | memory | memory | 75 (13) |
| corpus/repl-typearg/018 | `open-wide-1.hylo`:3 | `A0` → `Bool` | memory | memory | 2 (4) |

"memory" means the process aborted at the memory cap after 8 to 110 s. Under MIN5 all seventeen were run with the default 2.5 GB cap: sixteen abort and one finishes after 31 s. Under base and MIN5 + abs, five were run with the 2.5 GB cap and twelve with a 1 GB cap; the one that finishes under MIN5 was re-run at 2.5 GB under all three (`recheck.jsonl`).

All seventeen sources have equality requirements. Two of the errors are ones a programmer makes daily:

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

The 29 wrongly accepted mutants are the same kind of error: 22 deletions of one equality requirement that the body needs, and 7 type arguments replaced in a call with an equality requirement. Five of them cost base 20× to 97× the unmutated program before being accepted (0.6 to 2.2 s). The abstract model changes none of the 29. Example (`examples/wrongly-accepted-broken-chain.hylo`):

```hylo
fun f1<T, U where T == U>() { f1<U, T>() }
fun f2<T, U, V where T == U>() { f1<T, V>() }   // `U == V` deleted: base accepts after 69,302 matches; FULL rejects after 5
```

Outcome under base by kind of source:

| Source has an equality requirement | Ill-typed mutants | Rejected normally | Memory exhausted or 45 s | Wrongly accepted |
|---|---:|---:|---:|---:|
| yes | 241 | 195 (81%) | 17 (7%) | 29 (12%) |
| no | 475 | 475 (100%) | 0 | 0 |

**Which technique removes the blow-ups** (`attrib.py`, all seventeen, 600 MB cap; `analysis.md` section 9):

| Configuration | Rejected normally | Memory exhausted | Cost when rejected (`summon.matches`) |
|---|---:|---:|---|
| MIN5 + `budget` | 15 | 2 | 44,000 to 211,000 (0.8 to 6.7 s), with one extra diagnostic |
| MIN5 + `eqmgu` | 17 | 0 | 2 to 234,000 (eight above 16,000) |
| MIN5 + `eqsolve` (4 mutants tried) | 0 | 4 | – |
| FIX | 17 | 0 | 5 to 303, except two (10,455 and 27,374) |
| FIX without `eqmgu` | 17 | 0 | nine between 37,000 and 194,000 |
| FIX without `eqsolve` | 16 | 1 | nine between 6,600 and 172,000 |
| FIX without `budget` | 17 | 0 | same as FIX |
| FULL without `absmodel,absquotient` | 17 | 0 | 2 to 303, except two (10,315 and 17,294) |

The blow-ups come from the equality part of resolution. `eqmgu` and `eqsolve` together remove them cheaply; either alone leaves expensive cases; the search budget alone turns most of them into a slow rejection. The abstract model is not needed: FULL without it rejects all seventeen, and with it saves between 1 and 302 matches on four of them.

Under FULL, over all 716 ill-typed mutants there is no blow-up and no timeout. Five cost more than 10× their unmutated source; the largest in equality code is 17,294 matches (about 0.12 s).

### 3. What the abstract model changes

Comparison of MIN5 with MIN5 + `absmodel,absquotient`:

| Measure of "more than 10× cheaper with the model" | Mutants | Of | Share | Exact 95% interval | Interval resampling source files |
|---|---:|---:|---:|---|---|
| Blow-up removed | 1 | 17 | – | – | – |
| Normally rejected: `summon.matches` ratio above 10 **and** at least 1,000 matches at stake | 0 | 670 | 0% | 0% – 0.55% | – |
| Normally rejected: typing time ratio above 10 (single run, indicative) | 0 | 670 | 0% | 0% – 0.55% | – |
| Normally rejected: `summon.subgoals` ratio above 10 | 0 | 670 | 0% | 0% – 0.55% | – |
| **All ill-typed mutants not wrongly accepted, by work saved** | **1** | **687** | **0.15%** | **0.004% – 0.81%** | – |
| Literal: `summon.matches` ratio above 10, no floor | 113 | 670 | 16.9% | 14.1% – 19.9% | 6.0% – 33.0% |
| – of which the unmutated source has the same ratio | 73 | | | | |
| – of which the ratio appears with the error | 40 | 670 | 6.0% | 4.3% – 8.0% | 4.0% – 8.5% |

The one real gain is `corpus/del-bound/015` (`examples/blowup-rescued-by-absmodel.hylo`): the failing goal needs `Q<U>` for an unknown `U`, no conformance to `Q` exists, and the model refutes the goal before the equality search starts.

### 4. Why the literal ratio of 16.9% is not a cost

- **The saving is tiny.** Over all 670 mutants the model never saves more than 601 candidate matches (median 14). The typical case is a deleted `T is P` requirement: MIN5 scans the list of givens once (140 to 300 matches) and fails; the model answers after 1 match. The ratio is 150 to 300, the saving is one scan.
- **Time does not change.** Fifteen such mutants were timed five times each, minimum kept (`timing.jsonl`): MIN5 and MIN5 + abs differ by less than the noise (2.7 ms against 4.2 ms, 386 ms against 414 ms, and so on; ratios from 0.34 to 2.2 in both directions, none near 10). Building the model costs about 1 ms per program (3 ms for the standard library), which is as much as it saves.
- **73 of the 113 are not about the error.** In `members.hylo` the valid program already shows 600 matches against 0; every mutant of that file inherits the ratio. Its typing time is about 400 ms with or without the model.
- The model never increases `summon.matches` in any mutant.

Two valid sources of the sample do gain much from the model: `div-eq-ovl-b2-1.hylo` (112,129 matches against 1; 1.6 s against 5 ms) and `div-eq-ovl-b2-0.hylo`. Both were written to exhibit that behaviour.

### 5. Differences in verdict or diagnostics (correctness)

Compared over the 1,049 syntactically valid mutants (`analysis.md` section 5 lists every one).

- **MIN5 against base:** no difference in verdict, in number of diagnostics, or in the text of the diagnostics.
- **MIN5 + abs against MIN5:** one difference, `corpus/del-bound/015`: memory exhaustion becomes a rejection with the diagnostic that FULL also gives. No other difference in verdict, number or text.
- **FULL against base:** 54 differences, none of them a regression.
  - 17 blow-ups rejected (section 2).
  - 29 mutants accepted by base and rejected by FULL. All 29 are ill-typed: base is unsound on them. Ids: `corpus/del-where-req/{002,006,014,015,022,027,031}`, `corpus/repl-typearg/{004,011,019,024,025,030,033}`, `tests/del-where-req/{001,016}`, `workloads/del-where-req/{000,004,007,015,021,033,036,037,038,040,045,047,048}`.
  - 8 mutants rejected by both with 2 diagnostics under base and 3 under FULL: `corpus/del-bound/002`, `workloads/del-bound/{031,033,035,036,039,040,041}` (all `assoceq-*`, a `Ti is P` requirement deleted). The third diagnostic is correct: deleting `Ti is P` makes `Ti.X` undefined, which breaks the chain of equalities, so the argument of type `T5.X` no longer has type `T0.X`. Base misses it.

Exact reproduction of any of them: `python3 repro.py <id> base full --diff`.

### 6. Dependence on the depth bound

`depth.py`, eleven mutants, `HYLO_TC_MAXDEPTH` 10, 12 and 14 (6, 10, 14 for the blow-ups); `summon.matches`:

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
| tests/repl-typearg/007 (blow-up), depth 6 / 10 / 14 | memory at each | memory at each | memory at each |
| corpus/del-where-req/013 (blow-up), depth 6 / 10 / 14 | memory at each | memory at each | memory at each |
| corpus/del-bound/015 (blow-up), depth 6 / 10 / 14 | memory at each | memory at each | 1 at each |

The cost of an error does not depend on the depth bound, with one exception among 670: `tests/del-given/004` is the only rejected mutant that reaches the bound (`summon.depthExhausted` > 0), and its cost grows linearly with the bound; the model removes that growth (32 matches become 11). The blow-ups are not bounded by depth: they exhaust memory at depth 6 as well. They grow in breadth, which is why the frontier budget stops most of them and the depth bound does not.

### 7. Which errors are expensive

- **Not expensive:** a missing conformance, a missing member, a wrong type, swapped arguments, in code without equality requirements. 475 mutants, maximum 9.1× (an overload workload), nothing above 1.1× in the standard library.
- **Expensive under base and MIN5, with or without the model:** an equality that cannot be proved, in a scope that has equality requirements. Deleting one equality of a `where` clause, deleting a conformance that an equality refers to, or passing the wrong type to a function or extension constrained by an equality. The checker then exhausts memory (16 mutants), takes most of a minute (1), or finds a wrong proof and accepts (29).
- **Library-shaped code with a trait hierarchy** (`shapes.py`, a supplementary probe; `analysis.md` section 11). The sample has little code where a wrapper type conforms to each trait of a refinement chain when its argument does, which is how a generic library looks. Eighteen such programs were generated (chain of 1, 2 or 4 refinements; type nested 2, 4 or 8 deep), each with one wrong type argument so that the innermost conformance is missing. Under MIN5 the erroneous program costs 0.6× to 1.65× the valid one (at most 12,665 matches). Under base it costs up to 9.1× (at most 99,488 matches, a few seconds). The model reduces the failing case by 1% to 24% at depth 10 and by at most 37% at depth 14. No blow-up.

## Decision input

1. On the plan's criterion the abstract model is not justified by the error path: 0.15% of ill-typed mutants (upper bound 0.81%) against the 1% threshold. In code without equality requirements failing resolution is already cheap, so the model has nothing to remove. In code with equality requirements the expensive failures are in the equality procedure, which the model does not reach.
2. The measurement supports adopting `eqsolve` and `eqmgu` together. They are what makes the error path of equality code terminate and what makes its verdicts correct: 46 of 241 ill-typed mutants of equality code (19%) are mishandled without them.
3. A resource bound alone (`budget`) is a weak substitute: it turns 15 of 17 blow-ups into rejections that take 0.8 to 6.7 s and it does nothing for the 29 wrong acceptances.

## What remains uncertain

- **How representative the sources are.** No large body of generic Hylo code exists. The standard library is small and uses no equality requirement; the tests are small; the workloads are synthetic; the corpus was written to probe the checker. The rates of 7% and 12% describe this sample. What transfers is the dichotomy (cheap without equalities, broken with them), which held in every group.
- **The mutants are not independent.** They cluster by file and several files are size variants of one generator. The exact intervals assume independence. The intervals that resample whole files are given where the count is not zero; for a count of zero they are degenerate, and the honest statement is "none in 237 source files with rejected mutants".
- **`summon.matches` does not count the model's own work.** `absmodel.work` and `absmodel.micros` are in the raw rows; the time spent building the model is not recorded on the `absquotient` path. Time is the real cost and is noisy here; the timing claims rest on fifteen mutants timed five times.
- **Memory caps.** Twelve of the seventeen blow-ups were run under base and MIN5 + abs with a 1 GB cap only. Under MIN5 all were confirmed at 2.5 GB. Whether the sixteen would finish with more memory or time is not known; one finishes at 2.5 GB after 31 to 45 s.
- **Operators.** They are syntactic. 32% of the mutants are still valid (mostly swapped arguments of the same type and deleted declarations that nothing uses). Misspelled names, missing imports and errors inside expressions are not covered.
- **The probe of section 7** covers one shape. Its valid programs with a list of 8 elements are rejected by every configuration because of the depth bound of 10; those three rows have no valid reference.

## Files

| File | Content |
|---|---|
| `mutate.py` | the mutation operators |
| `sources.py`, `baseline.jsonl`, `baseline-corpus.jsonl` | the sources and their unmutated results |
| `gen.py`, `mutants.jsonl`, `sources-skipped.json` | the sample (regenerated identically by `python3 gen.py`) |
| `run.py`, `results.jsonl` | the main run; restartable; the last row for a (mutant, configuration) pair is the valid one |
| `analyse.py`, `analysis.md`, `classified.jsonl` | every table, and one row per mutant with its class and ratios |
| `repro.py` | `python3 repro.py <mutant-id> [config ...] [--diff] [--keep FILE] [HYLO_TC_MAXDEPTH=12]` |
| `attrib.py`, `attrib.jsonl` | the blow-ups under MIN5 plus individual fixes |
| `recheck.py`, `recheck.jsonl` | the blow-ups at the default 2.5 GB cap |
| `depth.py`, `depth.jsonl` | the depth sweep |
| `timing.py`, `timing.jsonl` | repeated timing of MIN5 against MIN5 + abs |
| `shapes.py`, `shapes/`, `shapes.jsonl` | the library-shaped probe |
| `examples/` | four mutated programs quoted above |
| `post.sh`, `post2.sh` | the order in which the secondary scripts were run |
| `bin/` | private copy of the type-checker binary and of the standard library (restored to the original after every run) |

Configurations: base = empty; MIN5 = `index,memberskip,typevec,symindex,traitindex`; MIN5 + abs adds `absmodel,absquotient`; FULL as in `BRIEF.md`. Most of the main run used a 1 GB memory cap (`TCX_MEM_LIMIT_KB=1000000`) so that blow-ups end quickly. Seventeen mutants abort at a cap; all of them were re-run under MIN5 with the default 2.5 GB cap, where one finishes (section 2).
