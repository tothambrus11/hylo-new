# Scaling curves of the type checker

## What was asked

The claims of the form "an exponential behaviour becomes polynomial" rest on single measurements (trans-8, breadth40, one divergent query). This study measures how the cost of type checking grows with the size of the problem, for the existing checker (**base**) and for the configurations **FIX**, **MIN5** and **FULL** of the brief, on parametric families of programs, and fits a growth law to each curve.

## Results in brief

The work counters are exact and deterministic. The times are measurements taken on a heavily loaded machine and are indicative only.

1. **Most of the claims hold, now with curves.** Under FULL the growth of the work counter drops, in most families to linear or constant, where the existing checker is quadratic, cubic, quartic or exponential:

   | Family | base | FULL |
   |---|---|---|
   | equality chain of `n` links (`eqchain`) | `2n³ + 206n² + 3915n + 16148` | `3n + 218` |
   | `n` goals over a chain of `n` links (`eqchain-goals`) | `n⁴ + 100n³ + …` | `2n` |
   | inferred argument behind a chain (`open-chain`) | `2n³ + 195n² + …` | `n + 75` |
   | `n` independent equality requirements (`req-eq`) | 72, 296, 6818 for `n` = 1, 2, 4, then out of memory at 8 | `n + 1` |
   | underivable goal, 2 growing givens, depth bound `d` (`div-depth`) | `2^d` | 1 |
   | underivable goal, `b` growing givens (`div-branch`) | 1350, 110449, then out of memory | 1 |
   | `n × n` conformances, `n` lookups (`breadth-square`) | `n³ + 71n` | `n² + n` |
   | `n` extensions, `n` member lookups (`members-both`) | `2n² + 8n` | `n` |
   | chain of `n` refinements (`refine`) | `n² + 72n + 73` | `n + 3` |

2. **The existing checker is not exponential on equality chains: it is cubic, and unsound.** It finds short invalid proofs (soundness problem 1 of the report), and accordingly accepts the ill-typed variants `eqchain-neg` and `assocneg` from three links on, at every size measured. The exponential that `eqsolve` removes belongs to the *sound* search: FULL without `eqsolve` needs 363, 1260, 9655 and 120230 matches for 1 to 4 links, and rejects the valid program from 5 links on (resource bound). The statement "exponential becomes linear" is therefore true of `fixsubst` with and without `eqsolve`, not of base against FULL. It is true of base against FULL for independent equality requirements (`req-eq`).

3. **MIN5 has the gains of indexing and nothing else.** On every equality and divergence family it follows the same growth law as base (with the same or a smaller constant), including the wrong acceptances and the memory exhaustion on `open-neg`. On the breadth, member-lookup, refinement, nesting and where-clause families it follows the law of FULL, except where FULL's abstract model refutes the goal at once (`nest-diamond-neg`: `n² + 3n + 5` against a constant).

4. **Exponential behaviours that remain under FULL** (all but the last occur with the default settings):
   - **Overloads distinguished by their return type.** `g(h(), …, h())` with `n` arguments and `m` overloads of `h` costs exactly `m + m² + … + mⁿ` solver forks under every configuration (`ovr-args`: 3ⁿ; `ovr-width`: `m⁴ + m³ + m² + m`). Twelve arguments and three overloads take 34 s.
   - **Nested overloaded calls.** `g(f(A0()), …)` with `n` calls and 4 overloads of `f`: the number of forks grows by a factor of 2.0 to 2.2 per call from 10 to 16 calls, and the factor is not falling. Sixteen calls take 113 s (`ovl-calls`). The same calls in separate statements cost `4n` (`ovl-stmts`).
   - **Several inferred arguments constrained by equalities.** `pick<T, U1, …, Un where Ui is Q, T == Ui>(x)`: 3, 79, 1351 and 24281 matches for `n` = 1 to 4, a factor of 17 to 26 per argument. At `n` = 5 the valid program is rejected, by the resource bound, or by the depth bound if the resource bound is lifted (`open-wide`, `open-wide-nobudget`).
   - **A derivable goal next to growing givens.** The count doubles with each level of the derivation, `2^d`, up to the depth bound (`div-valid`), and beyond it when the bound is raised (`div-valid-deep`). The abstract model cannot help: the goal is true.
   - **An underivable goal that the abstract model does not refute.** With facts `S<S<Xi>> is P` in scope, the model (truncated at depth 2) no longer refutes `Yb is P`, and the count doubles with each unit of the depth bound, as in base (`div-trunc-depth`). With the default bound and three or more branching givens the resource bound of `budget` ends the search after 3 to 20 s; with 32 branching givens the checker runs out of memory instead (`div-trunc`).
   - **Diamond-shaped conditional givens.** `S<T> is P` and `S<T> is Q` each requiring `T is P` and `T is Q` cost `2^d` for nesting `d`: subgoals are not shared (`nest-diamond`). This needs a raised depth bound; with the default bound the program is rejected from `d = 3`.

5. **Super-linear polynomial behaviours that remain under FULL:**
   - **`n` equalities between associated types** (`assoceq`, `assocneg`): `3n² + 145n + 145` matches, and a time that grows faster than the count: 0.8 s at 32, 15 s at 128, 52 s at 192, no answer in 120 s at 256 (exponent about 2.5). The control without the equalities takes 13 ms at 256.
   - **`n` equality goals over `n` equalities** (`eqchain-goals`): `2n` matches, but 0.7 s at 256, 4.2 s at 512 and 23 s at 1024 (exponent about 2.4). The control without equalities takes 42 ms at 1024. The count of matches does not see this cost; presumably each goal runs the decision procedure over all the facts in scope again. `n` independent requirements `Ti == Ui` behave alike (`req-eq-deep`: `n + 1` matches, 0.4 s at 256). A single goal stays cheap: 67 ms for a chain of 1024 (`eqchain`).
   - **A call with `n` requirements from a function with `n` requirements** (`req-traits-deep`, `req-params-deep`): `0.5n² + 0.5n + 1` or `1.5n² − 0.5n + 1` matches, time exponent 2.6 to 2.8 (3.2 s for 256 type parameters with one requirement each). With the default depth bound this cannot be observed, because the call is rejected from 10 requirements (result 6).
   - **`n` lookups among `n` candidates that the index does not separate**: `n² + n` for conformances of `n` types to the same trait (`breadth-square`), `n² + 3n` for `n` nested givens (`nestwide`). One lookup among `n` conformances to one trait costs `n + 1` (`breadth-types`).
   - **Overload width**: `m² + 7m` forks for four nested calls with `m` overloads (`ovl-width`), `m⁴ + …` for four arguments overloaded on the return type (`ovr-width`).
   - Nothing super-linear was found in member lookup (`members-*`, `condext`), nesting (`nest-deep`, 128 levels) or refinement (`refine-deep`, 64 levels): the counters are linear or constant and the times stay below 0.12 s at the largest sizes (1280 extensions, 640 lookups).

6. **The depth bound of 10 counts resolution steps, not nesting depth, and it rejects valid programs of modest size under all four configurations.** A call whose callee has 10 or more requirements is rejected (`req-traits`, `req-params`: accepted up to 9), as are 10 independent equality requirements under FIX and FULL (`req-eq`), a conditional conformance nested 9 deep (`nest` is accepted up to 8), a diamond nested 3 deep, and 5 inferred arguments. Most scaling behaviours of valid programs are therefore cut off by a rejection before they become expensive. The curves beyond those sizes were measured with the bound raised to 1000 (families named `-deep`, and the diamonds).

7. **The resource bound turns explosions into rejections, not always.** Under FIX and FULL, `budget` stops the divergent families after a few seconds. It also rejects valid programs (`open-wide` at 5, `div-valid-deep` at depth 16 under FULL and 12 under FIX), and it does not prevent memory exhaustion on `div-trunc` with 32 branches under FULL.

## Leave-one-out configurations

These were run to tie each curve to the technique that produces it. The points are few, because the resource bound of `budget` cuts every explosion short.

- **FULL without `eqsolve`.** `eqchain`: 363, 1260, 9655, 120230 matches for 1 to 4 links (factors 3.5, 7.7, 12.5), then the resource bound rejects the valid program. `eqchain-goals`: 72, 586, 5324, 66171, then the same. `assoceq` is rejected from 4 equalities, `open-chain` from 4 links, `req-eq-deep` from 8 requirements. The ill-typed `eqchain-neg` and `assocneg` are still rejected, but from 3 links on only after the resource bound has stopped a search, which takes 1 to 11 s.
- **FULL without `absmodel` and `absquotient`.** `div-depth`: 93, 189, 765, 3069, 12285, 49149 for depth bounds 5 to 14, that is `2^d` again, with the counts of MIN5. `div-branch`, `div-trunc` and `cyc-clique` explode with the counts of MIN5 until the resource bound stops them (for example 20 and 3069 matches for `div-branch` with 1 and 2 branches, against 1 with the model), and `div-branch-eq` with those of FIX. `nest-diamond-neg` returns to `n² + 3n + 5`. `cyc-ring`, `nest-neg`, `req-neg` and `eqchain-neg` stay linear: there the model saves a constant factor only.
- **FULL without `absquotient`.** `div-branch-eq` (an equality in scope) gives exactly the counts of FULL without the whole model: 1369, 111983, then the resource bound. With an equality in scope, the benefit of the abstract model depends entirely on `absquotient`. `eqchain-neg` is unaffected.

## What was done

**Programs.** `gen.py` defines the families, each a function of one size parameter `n`. The shapes are those of the existing generators (`research/scripts/gen.py`, `research/workloads/round3/gen3.py`) and of the review's performance programs (`research/round3/soundness/review2/perf`). `python3 gen.py --list` lists them and `python3 gen.py FAMILY N` prints one program. Every program that was run is in `progs/`.

| Group | Families | Size parameter |
|---|---|---|
| Equality chain | `eqchain` (conformance and associated type through the chain), `eqchain-conf` (conformance only), `eqchain-neg` (ill-typed: the middle link is missing), `eqchain-goals` (`n` goals) | number of links |
| Associated types | `assoceq`, `assocneg` (ill-typed: the middle equality is missing) | number of equalities `T{i}.X == T{i+1}.X` |
| Breadth | `breadth-traits`, `breadth-types` (one lookup), `breadth-square` (`n × n` conformances and `n` lookups; breadth40 is `n = 40`) | number of conformances, or its square root |
| Divergence | `div-branch`, `div-branch-eq` (an unrelated equality is in scope), `div-trunc` (facts deeper than the abstract model looks), `cyc-ring`, `cyc-clique` (cyclic givens) | branching, or length of the cycle |
| | `div-depth`, `div-trunc-depth` (two branches) | the depth bound `HYLO_TC_MAXDEPTH` |
| | `div-valid`, `div-valid-deep` (the goal is derivable) | depth of the derivation |
| Member lookup | `members-ext`, `members-use`, `members-both`, `condext` (conditional extensions) | extensions, lookups |
| Overloads | `ovl-calls` (`n` calls, 4 overloads), `ovl-width` (4 calls, `n` overloads), `ovl-stmts` (`n` statements), `ovr-args` (`n` arguments, 3 overloads on the return type), `ovr-width` (4 arguments, `n` overloads) | calls or overloads |
| Nested givens | `nest`, `nest-deep`, `nest-neg`, `nest-diamond`, `nest-diamond-default`, `nest-diamond-neg`, `refine`, `refine-deep`, `nestwide` | nesting depth, or number of nested givens |
| Open equalities | `open-chain`, `open-neg` (ill-typed), `open-wide`, `open-wide-nobudget` | length of the chain, or number of inferred arguments |
| Where clauses | `req-traits`, `req-params`, `req-eq`, `req-neg` (ill-typed), and their `-deep` variants | number of requirements |
| Controls | `ctrl-goals` (`eqchain-goals` without the equalities), `ctrl-assoc` (`assoceq` without the equalities) | as the family they control |

The `-deep` families and the diamonds (except `nest-diamond-default`) run with `HYLO_TC_MAXDEPTH=1000`. `div-depth` and `div-trunc-depth` vary `HYLO_TC_MAXDEPTH` itself, from 5 upwards (below 5 the standard library no longer type-checks). `open-wide-nobudget` sets `HYLO_TC_BUDGET` to 10⁹.

**Intended verdicts.** Each family states whether its programs should be accepted. At the smallest size every configuration gives the intended verdict, and the rejections carry a diagnostic of the intended kind (no syntax error), with one exception: on `open-neg`, base and MIN5 exhaust memory at every size. Where a configuration departs from the intended verdict at a larger size, the tables mark the point, and the fit uses only the longest run of sizes with one verdict.

**Runs.** `run.py` runs `tc-bench --count` (binary `eq9-723cc0e6b0f8`) for each (family, size, configuration), one process at a time, under `timeout`, and appends a record to `results.jsonl`: verdict, diagnostics, every counter of the user module, the `type.user` time, exit code, wall time and peak memory. Within a series the sizes are run in increasing order. The series stops after a timeout, after two consecutive crashes, or when a run slower than 2 s predicts more than twice the timeout for the next size by power-law extrapolation from the last two sizes (which underestimates an exponential). Sizes that were not run are recorded as `skipped`, with the reason.

Every point was first run with a 20 s timeout, then every series cut short was continued with the 120 s timeout. COMPLETION_NOTE RUN_STATS

Three leave-one-out configurations were also run on the families they concern: FULL without `eqsolve`, FULL without `absmodel` and `absquotient`, and FULL without `absquotient`. A second pass repeated the PASS1_COUNT points of FULL that finish within 5 s: the counters and verdicts were identical in all of them, and the time reported for those points is the smaller of the two.

**Fits.** `analyze.py` produces this file from `results.jsonl` and `README.head.md`, and writes the fits to `fits.json`. For each (family, configuration):
- If the counter values lie *exactly* on a polynomial of degree at most 5 (relative error below 10⁻⁶, with at least two more points than coefficients), that polynomial is reported, possibly from some size on. Since the counters are deterministic, this test is much sharper than a regression. For example the count of base on `eqchain` is the cubic above for every `n` from 3 to 64, whereas a log-log regression on the same points gives an exponent of 1.3, because the cubic term is still small.
- Otherwise two models with a constant term, `a + c·n^p` and `a + c·r^n`, are fitted in log space to the series and to its suffixes (at least five points). A model is retained when its root-mean-square error (`rms`, in units of natural log, so 0.05 is about 5%) is small and clearly below the other's, when the sizes span at least a factor of 4 for a polynomial, and when the values grow at least 8-fold for an exponential. An exponent above 5 is retained only on a close fit. Otherwise the result is "undecided" or "too few points".
- The detailed tables also give the plain log-log and semi-log regressions over the upper half of the sizes (exponent and base, with R²), and the local exponents and the growth factors per unit of size over the last three intervals. A steady factor indicates an exponential; a factor that falls towards 1 indicates a polynomial.
- Times are fitted the same way with looser thresholds. A series whose times all stay below 200 ms is not fitted: at that scale the noise of this machine is as large as the signal.

**Reproducing.** `python3 run.py --timeout 20`, then `python3 run.py --timeout 120`, then `python3 analyze.py`. `run.py --configs FULL-eqsolve --only FAMILY,…` runs a leave-one-out configuration, and `run.py --pass 1` repeats the fast points. The runner skips the points already in `results.jsonl`.

**Files.**

| File | Content |
|---|---|
| `gen.py` | the program families: generators, sizes, intended verdicts, environment, primary counter |
| `run.py` | the restartable runner |
| `analyze.py` | the fits; writes `README.md`, `tables.md` (the generated part of this file alone) and `fits.json` |
| `README.head.md` | the hand-written part of this file |
| `results.jsonl` | one record per run (the last record of a point wins; `pass` 1 is the repeated timing pass) |
| `fits.json` | every fit, with the residuals of both models, the local exponents and the growth factors |
| `progs/` | the programs, named `FAMILY-N.hylo` |

## What remains uncertain

- **Times.** They were taken while four to eight other type-checking jobs ran on the same four cores (load average 6 to 9). The same point measured twice differs by up to a factor of two below 100 ms, and by tens of percent above. Exponents fitted on times are good to about ±0.5, and only where the times exceed a few hundred milliseconds. For example the time of FULL on `assoceq` gives local exponents between 1.6 and more than 3 over successive doublings; "about 2.5" summarizes them. The counters do not have this problem.
- **Work that no counter sees.** Where the time grows faster than every counter (`assoceq`, `eqchain-goals`, `req-traits-deep`, `req-params-deep`), the time is the only evidence of the true cost. The controls show that the growth comes from the equalities, not from the size of the program, but not which part of the checker spends it.
- **Short series.** Families that grow like `b^10` give two or three points before the timeout or the memory limit (`div-branch`, `div-trunc`, `cyc-clique`, `open-wide` under base and MIN5). Their growth in `b` is reported as "too few points"; the growth in the depth bound is measured instead by `div-depth` and `div-trunc-depth`. Likewise `open-wide` gives four points under FIX and FULL before the depth bound rejects the program, and the leave-one-out configurations give three or four points before the resource bound stops them.
- **Nested overloaded calls.** The local exponent of `ovl-calls` rises from 7 to 12 while the factor per call stays near 2, which is the signature of an exponential, but 16 calls do not exclude a polynomial of high degree by a formal test.
- **Programs.** The families are synthetic. They show how each behaviour scales, not how often it occurs in real code.

