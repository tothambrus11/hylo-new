# Scaling curves of the type checker

## What was asked

The claims of the form "an exponential behaviour becomes polynomial" rest on single measurements (trans-8, breadth40, one divergent query). This study measures how the cost of type checking grows with problem size, for the existing checker (**base**) and for the configurations **FIX**, **MIN5** and **FULL** of the brief, on parametric program families, and fits a growth law to each curve.

## Results in brief

Counters are exact; times are single measurements on a loaded machine and are indicative only.

1. **Most claims hold, with curves.** Under FULL the work counter is constant or linear where the existing checker is quadratic, cubic or exponential:
   - equality chains: cubic → linear (`eqchain`, `open-chain`);
   - independent equality requirements: exponential → linear (`req-eq`);
   - underivable goals with growing or cyclic givens: `2^d` in the depth bound `d`, about `b^10` in the branching `b` → constant (`div-depth`, `div-branch`, `cyc-clique`);
   - `n × n` conformances with `n` lookups: cubic → quadratic (`breadth-square`);
   - member lookups through `n` extensions: quadratic → linear (`members-both`).
2. **The existing checker is not exponential on equality chains.** It is cubic, because it accepts short, invalid proofs (soundness problem 1): it accepts the ill-typed variants `eqchain-neg` and `assocneg` from three links on. The exponential that `eqsolve` removes is that of the *sound* search: FULL without `eqsolve` grows by a factor of about 11 per link and gives up from five links on.
3. **MIN5 gives the gains that come from indexing, and none on equalities or divergence.** Its counts equal those of base on every equality and divergence family (including the wrong acceptances), and those of FULL on the breadth, member-lookup, refinement and where-clause families.
4. **Exponential behaviours that remain under FULL:**
   - overloads distinguished by their return type: exactly `m + m^2 + … + m^n` solver forks for `n` arguments and `m` overloads (`ovr-args`, `ovr-width`);
   - nested overloaded calls in one expression: a factor of about 2.1 to 2.2 per additional call (`ovl-calls`);
   - several inferred arguments constrained by equalities: a factor of about 14 to 20 per inferred argument, until the resource bound rejects the (valid) program at five (`open-wide`);
   - a derivable goal next to growing givens: `2^d` in the depth `d` of the derivation (`div-valid`);
   - an underivable goal that the abstract model cannot refute: `2^d` in the depth bound (`div-trunc-depth`); with 32 branching givens the checker runs out of memory instead of reporting an error (`div-trunc`);
   - diamond-shaped conditional givens: `2^d` (`nest-diamond`), reachable only if the depth bound is raised.
5. **Super-linear polynomial behaviours that remain under FULL:**
   - `n` equalities between associated types: `3n² + 145n + 145` candidate matches, and a time that grows about as `n³` (15 s at 128, timeout at 256) (`assoceq`, `assocneg`);
   - `n` equality goals over a chain of `n` links: `2n` matches, but a time that grows about as `n^2.5` (23 s at 1024) (`eqchain-goals`);
   - a call with `n` requirements from a function with `n` requirements: `0.5n²` to `1.5n²` matches, time about `n^2.6` to `n^2.8` (`req-traits-deep`, `req-params-deep`);
   - `n` lookups among `n` givens with the same trait or the same nesting: `n²` (`breadth-square`, `nestwide`).
6. **The depth bound of 10 counts resolution steps, not nesting.** It hides most scaling behaviours of valid programs, because it rejects them first: under all four configurations a call with ten or more requirements is rejected (`req-traits`, `req-params`, `req-eq`), as is a conditional conformance nested nine deep, a diamond nested three deep, and five inferred arguments. The curves of these families beyond those sizes were measured with the bound raised to 1000.

## What was done

**Programs.** `gen.py` defines FAMILIES, each a function of one size parameter `n`. The shapes are those of the existing generators (`research/scripts/gen.py`, `research/workloads/round3/gen3.py`) and of the review's performance programs (`research/round3/soundness/review2/perf`). `python3 gen.py --list` lists them; `python3 gen.py FAMILY N` prints one program. Every program run is kept in `progs/`.

| Group | Families | Size parameter |
|---|---|---|
| Equality chain | `eqchain` (conformance and associated type through the chain), `eqchain-conf` (conformance only), `eqchain-neg` (ill-typed: middle link missing), `eqchain-goals` (`n` goals) | number of links |
| Associated types | `assoceq`, `assocneg` (ill-typed: middle equality missing) | number of equalities `T{i}.X == T{i+1}.X` |
| Breadth | `breadth-traits`, `breadth-types` (one lookup), `breadth-square` (`n×n` givens, `n` lookups; breadth40 is `n = 40`) | number of conformances (or its square root) |
| Divergence | `div-branch`, `div-branch-eq` (with an equality in scope), `div-trunc` (with facts deeper than the abstract model looks), `cyc-ring`, `cyc-clique` (cyclic givens); `div-depth`, `div-trunc-depth` (two branches, size = depth bound); `div-valid`, `div-valid-deep` (the goal is derivable at depth `n`) | branching, cycle length, or depth |
| Member lookup | `members-ext`, `members-use`, `members-both`, `condext` (conditional extensions) | extensions, lookups |
| Overloads | `ovl-calls` (`n` calls, 4 overloads), `ovl-width` (4 calls, `n` overloads), `ovl-stmts` (`n` statements), `ovr-args` (`n` arguments, 3 overloads on the return type), `ovr-width` (4 arguments, `n` overloads) | calls or overloads |
| Nested givens | `nest`, `nest-deep`, `nest-neg`, `nest-diamond`, `nest-diamond-default`, `nest-diamond-neg`, `refine`, `refine-deep`, `nestwide` | nesting depth, or number of nested givens |
| Open equalities | `open-chain`, `open-neg` (ill-typed), `open-wide`, `open-wide-nobudget` | chain length, or number of inferred arguments |
| Where clauses | `req-traits`, `req-params`, `req-eq`, `req-neg` (ill-typed), and the `-deep` variants | number of requirements |
| Controls | `ctrl-goals` (eqchain-goals without equalities), `ctrl-assoc` (assoceq without equalities) | as the family they control |

The families whose name ends in `-deep`, and the diamond families, run with `HYLO_TC_MAXDEPTH=1000`, because the default bound rejects them at small sizes (result 6). `div-depth` and `div-trunc-depth` vary `HYLO_TC_MAXDEPTH` itself, from 5 (below which the standard library no longer type-checks). `open-wide-nobudget` sets `HYLO_TC_BUDGET` to 10^9.

**Intended verdicts.** Each family states whether its programs should be accepted. At the smallest size every configuration gives the intended verdict, with a diagnostic of the intended kind (no syntax error), except `open-neg`, where base and MIN5 exhaust memory. Where a configuration departs from the intended verdict at a larger size, the tables mark it: `✗` a valid program is rejected (`(depth)`: the depth bound was reached; `[B]`: the resource bound of `budget` stopped a resolution), `(accepted!)` an ill-typed program is accepted.

**Runs.** `run.py` runs `tc-bench --count` (binary `eq9-723cc0e6b0f8`) once per (family, size, configuration), one process at a time, under `timeout 120`, and appends a record to `results.jsonl`: verdict, diagnostics, every counter of the user module, `type.user` time, exit code, wall time and peak memory. Within a series, sizes are run in increasing order; the series stops after a timeout, after two consecutive crashes, or when a run slower than 2 s predicts, by power-law extrapolation from the last two sizes (a lower bound for an exponential), more than 240 s for the next size. The sizes not run are recorded as `skipped` with the reason.

Besides the four configurations, three leave-one-out configurations were run on the families they concern: FULL without `eqsolve`, FULL without `absmodel` and `absquotient`, and FULL without `absquotient`.

**Fits.** `analyze.py` produces this file from `results.jsonl` and `README.head.md`. For each (family, configuration):
- If the counter values lie *exactly* on a polynomial of degree at most 5 (relative error below 10⁻⁶, with at least two more points than coefficients), that polynomial is reported, possibly from some size on. Counters are deterministic, so this is a much sharper test than a regression: for example the existing checker's count on `eqchain` is `2n³ + 206n² + 3915n + 16148` for every `n ≥ 3`, which a log-log regression on `n ≤ 32` reports as `n^1.3`.
- Otherwise two models with a constant term are fitted in log space, `a + c·n^p` and `a + c·r^n`, to the whole series and to its suffixes. A model is retained if its root-mean-square error is small (`rms`, in units of log: 0.05 is about 5%) and clearly below the other's, the sizes span at least a factor of 4 for a polynomial, and the values grow at least 8-fold for an exponential. An exponent above 5 is retained only on a close fit. Otherwise the verdict is "undecided" or "too few points".
- The detailed tables also give the plain log-log and semi-log regressions over the upper half of the sizes (exponent and base, with R²), the local exponents and the growth factors per unit of size over the last three intervals. A constant factor indicates an exponential; a factor falling towards 1 indicates a polynomial.
- When the verdict changes along a series, only the longest run of sizes with one verdict is fitted (stated under "Ends with").
- Times are fitted the same way with looser thresholds. Times that stay below 50 ms are not fitted.

## What remains uncertain

- **Times.** Each time is one measurement, taken while four to six other type-checking jobs ran on the same four cores. Small times vary by a factor of two or more between runs. Exponents fitted on times are reliable to about ±0.5, and only where the times exceed a few hundred milliseconds. The counters do not have this problem.
- **Work that no counter sees.** In several families the time grows faster than every counter (`assoceq`, `eqchain-goals`, `req-*-deep`, `breadth-types`, `members-both`). The time exponents there are the only evidence, and they carry the uncertainty above. The controls show that part of this growth does not come from resolution at all (see below).
- **Short series.** Families that grow like `b^10` give two or three points before the timeout (`div-branch`, `div-trunc`, `cyc-clique` and `open-wide` under base). Their growth in `b` is reported as "too few points"; the growth in the depth bound is measured instead by `div-depth` and `div-trunc-depth`.
- **Overloads.** `ovl-calls` reaches 16 calls. The growth factor per call is 2.0 to 2.2 over the last sizes and is not falling, which indicates an exponential, but a polynomial of high degree is not excluded by a formal test.
- **Leave-one-out configurations** hit the resource bound after three or four sizes, so their exponential growth rests on four points each.

