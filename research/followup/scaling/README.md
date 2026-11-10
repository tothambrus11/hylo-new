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

## Summary: growth of the primary counter / of the time

| Family | base | FIX | MIN5 | FULL |
|---|---|---|---|---|
| eqchain | n^3 exact / n^2.5 † | n^1 exact / n^1.5 | n^3 exact / n^1.5 † | n^1 exact / n^1.4 |
| eqchain-conf | n^3 exact / n^2.6 † | n^1 exact / n^0.6 | n^3 exact / n^1.7 † | n^1 exact / n^0.5 |
| eqchain-neg | n^3 exact / undecided † ✗ | n^1 exact / n^1.0 | n^3 exact / undecided † ✗ | n^1 exact / n^1.1 |
| eqchain-goals | n^4 exact / n^2.8 † | n^1 exact / n^2.1 † | n^2.4 / n^2.4 † | n^1 exact / n^2.2 |
| assoceq | n^3 exact / n^2.5 ‡ | n^2 exact / undecided † | n^3 exact / undecided † | n^2 exact / n^2.0 † |
| assocneg | n^3 exact / undecided ‡ ✗ | n^2 exact / n^2.2 † | n^1.7 / n^1.8 † ✗ | n^2 exact / n^2.3 † |
| breadth-traits | n^1 exact / n^1.9 | n^1 exact / n^1.8 | flat / n^1.2 | flat / <50 ms |
| breadth-types | n^1 exact / n^2.3 | n^1 exact / n^2.6 | n^1 exact / <50 ms | n^1 exact / n^1.3 |
| breadth-square | n^3 exact / undecided | n^3 exact / n^3.6 | n^2 exact / undecided | n^2 exact / n^1.7 |
| div-branch | too few / too few † | undecided / undecided † [B] | too few / too few † | flat / <50 ms |
| div-branch-eq | too few / too few † | undecided / undecided † [B] | too few / too few † | flat / <50 ms |
| div-trunc | too few / too few † | undecided / undecided † [B] | too few / too few † | undecided / undecided ‡ [B] |
| div-depth | 2.0^n / undecided † | 2.0^n / undecided [B] | 2.0^n / undecided † | flat / <50 ms |
| div-trunc-depth | 2.0^n / undecided † | 2.0^n / 2.8^n [B] | 2.0^n / undecided † | 2.0^n / too few [B] |
| div-valid | 2.0^n / undecided | 2.0^n / undecided | 2.0^n / undecided | 2.0^n / undecided |
| div-valid-deep | 2.0^n / undecided † | 2.0^n / undecided ✗ [B] | 2.0^n / 2.2^n † | 2.0^n / 2.2^n † ✗ [B] |
| cyc-ring | n^1 exact / undecided | n^1 exact / undecided | n^1 exact / <50 ms | flat / <50 ms |
| cyc-clique | too few / too few † | too few / too few † | too few / too few † | flat / <50 ms |
| members-ext | n^1 exact / n^0.5 | flat / undecided | flat / n^0.6 | flat / n^0.9 |
| members-use | n^1 exact / n^1.3 | n^1 exact / undecided | n^1 exact / n^0.9 | n^1 exact / n^0.8 |
| members-both | n^2 exact / n^1.4 | n^1 exact / n^1.5 | n^1 exact / n^2.0 | n^1 exact / n^1.8 |
| condext | n^1 exact / n^2.2 | flat / n^1.1 | flat / <50 ms | flat / <50 ms |
| ovl-calls | undecided / undecided † | undecided / undecided † | undecided / undecided † | undecided / undecided † |
| ovl-width | n^2 exact / undecided | n^2 exact / undecided | n^2 exact / <50 ms | n^2 exact / <50 ms |
| ovl-stmts | n^1 exact / n^0.6 | n^1 exact / undecided | n^1 exact / <50 ms | n^1 exact / <50 ms |
| ovr-args | 3.0^n / undecided † | 3.0^n / undecided † | 3.0^n / undecided † | 3.0^n / 2.8^n |
| ovr-width | n^4 exact / n^4.3 | n^4 exact / undecided | n^4 exact / n^3.9 | n^4 exact / n^4.1 |
| nest | n^1 exact / <50 ms | n^1 exact / <50 ms | n^1 exact / <50 ms | n^1 exact / <50 ms |
| nest-deep | n^1 exact / undecided | n^1 exact / n^0.9 | n^1 exact / <50 ms | n^1 exact / <50 ms |
| nest-neg | n^1 exact / n^0.8 | n^1 exact / n^1.3 | n^1 exact / <50 ms | n^1 exact / <50 ms |
| nest-diamond | 2.1^n / undecided ✗ | 2.1^n / undecided ✗ | 2.3^n / undecided ✗ | 2.3^n / undecided ✗ |
| nest-diamond-default | flat / flat ✗ | flat / flat ✗ | undecided / <50 ms ✗ | undecided / <50 ms ✗ |
| nest-diamond-neg | n^2 exact / undecided | n^2 exact / undecided | n^2 exact / <50 ms | flat / <50 ms |
| refine | n^2 exact / flat | n^2 exact / undecided | n^1 exact / <50 ms | n^1 exact / <50 ms |
| refine-deep | n^2 exact / undecided | n^2 exact / n^2.1 | n^1 exact / <50 ms | n^1 exact / <50 ms |
| nestwide | n^2 exact / n^2.2 | n^2 exact / n^2.0 | n^2 exact / undecided | n^2 exact / n^1.8 |
| open-chain | n^3 exact / n^1.8 † | n^1 exact / undecided | n^3 exact / n^1.8 † | n^1 exact / <50 ms |
| open-neg | – / – † | n^1 exact / undecided | – / – † | flat / <50 ms |
| open-wide | too few / too few † | 13.8^n / 11.8^n ✗ [B] | too few / too few † | 19.8^n / undecided ✗ [B] |
| open-wide-nobudget | too few / too few † | 13.8^n / undecided † ✗ | too few / too few † | 19.8^n / n^8.8 ‡ ✗ |
| req-traits | n^2 exact / flat ✗ | n^2 exact / <50 ms ✗ | n^2 exact / <50 ms ✗ | n^2 exact / <50 ms ✗ |
| req-params | n^2 exact / undecided ✗ | n^2 exact / <50 ms ✗ | n^2 exact / <50 ms ✗ | n^2 exact / <50 ms ✗ |
| req-eq | too few / too few † | n^1 exact / <50 ms ✗ | too few / too few † | n^1 exact / <50 ms ✗ |
| req-traits-deep | n^2 exact / n^2.4 † | n^2 exact / n^2.8 † | n^2 exact / n^3.3 | n^2 exact / n^2.8 |
| req-params-deep | n^2 exact / undecided † | n^2 exact / n^3.2 † | n^2 exact / n^3.3 | n^2 exact / n^2.6 |
| req-eq-deep | too few / too few † | n^1 exact / n^2.2 | too few / too few † | n^1 exact / undecided |
| req-neg | n^2 exact / n^1.7 | n^2 exact / n^2.4 | n^1 exact / <50 ms | n^1 exact / <50 ms |

† the series ends with a timeout (or was stopped because a timeout was predicted); ‡ it ends with a crash; ✗ at some size the verdict differs from the intended one; [B] the resource bound of `budget` stopped a resolution, so the count is capped.

## Summary: leave-one-out configurations

| Family | Configuration | Growth (counter / time) | Ends with |
|---|---|---|---|
| eqchain | FULL-eqsolve | 11.3^n / n^9.4 † ✗ [B] | timeout (>20 s) at n=128; fitted on n=1..4 (accepted); resource bound (`budget`) hit from n=5; verdict differs from the intended one at n=5..64 |
| eqchain-neg | FULL-eqsolve | undecided / undecided † [B] | timeout (>20 s) at n=128; fitted on n=3..64 (rejected, resource bound hit); resource bound (`budget`) hit from n=3 |
| eqchain-neg | FULL-absmodel | n^1 exact / undecided | completed |
| eqchain-neg | FULL-absquotient | n^1 exact / n^1.6 | completed |
| eqchain-goals | FULL-eqsolve | 10.9^n / undecided † ✗ [B] | stopped before n=8: predicted timeout: 17 s at n=6, power-law extrapolation gives 74 s at n=8; fitted on n=1..4 (accepted); resource bound (`budget`) hit from n=5; verdict differs from the intended one at n=5..6 |
| assoceq | FULL-eqsolve | undecided / undecided † ✗ [B] | timeout (>20 s) at n=128; fitted on n=4..64 (rejected, resource bound hit); resource bound (`budget`) hit from n=4; verdict differs from the intended one at n=4..64 |
| assocneg | FULL-eqsolve | undecided / undecided † [B] | stopped before n=128: predicted timeout: 11 s at n=64, power-law extrapolation gives 44 s at n=128; fitted on n=3..64 (rejected, resource bound hit); resource bound (`budget`) hit from n=3 |
| div-branch | FULL-absmodel | too few / too few † | timeout (>20 s) at n=3 |
| div-branch-eq | FULL-absmodel | undecided / undecided † [B] | stopped before n=8: predicted timeout: 15 s at n=6, power-law extrapolation gives 72 s at n=8; fitted on n=3..6 (rejected, resource bound hit); resource bound (`budget`) hit from n=3 |
| div-branch-eq | FULL-absquotient | undecided / undecided † [B] | stopped before n=8: predicted timeout: 15 s at n=6, power-law extrapolation gives 79 s at n=8; fitted on n=3..6 (rejected, resource bound hit); resource bound (`budget`) hit from n=3 |
| div-trunc | FULL-absmodel | too few / too few † [B] | stopped before n=4: predicted timeout: 13 s at n=3, power-law extrapolation gives 154 s at n=4; fitted on n=1..2 (rejected); resource bound (`budget`) hit from n=3 |
| div-depth | FULL-absmodel | 2.0^n / too few † | timeout (>20 s) at n=16 |
| cyc-ring | FULL-absmodel | n^1 exact / <50 ms | completed |
| cyc-clique | FULL-absmodel | too few / too few † [B] | stopped before n=5: predicted timeout: 3 s at n=4, power-law extrapolation gives 51 s at n=5; fitted on n=2..3 (rejected); resource bound (`budget`) hit from n=4 |
| nest-neg | FULL-absmodel | n^1 exact / <50 ms | completed |
| nest-diamond-neg | FULL-absmodel | n^2 exact / <50 ms | completed |
| open-chain | FULL-eqsolve | undecided / undecided † ✗ [B] | timeout (>20 s) at n=128; fitted on n=8..64 (rejected, resource bound hit); resource bound (`budget`) hit from n=8; verdict differs from the intended one at n=4..64 |
| req-eq-deep | FULL-eqsolve | too few / too few † ✗ [B] | timeout (>20 s) at n=64; fitted on n=8..32 (rejected, resource bound hit); resource bound (`budget`) hit from n=8; verdict differs from the intended one at n=8..32 |
| req-neg | FULL-absmodel | n^1 exact / <50 ms | completed |

## Tables per family

In the tables, *count* is the family's primary counter in the user module and *ms* is the `type.user` time (one measurement, indicative). `timeout`: no answer within the stated time; `not run`: a smaller size of the series already timed out, crashed twice, or predicted a timeout; `✗`: a valid program was rejected (`(depth)`: the depth bound was reached); `[B]`: the resource bound of `budget` stopped a resolution; `(accepted!)`: an ill-typed program was accepted.

### eqchain

Valid: conformance and associated type transported along n equality links. Intended verdict: accepted. Primary counter: `summon.matches`.

| n | base count | base ms | FIX count | FIX ms | MIN5 count | MIN5 ms | FULL count | FULL ms |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 659 | 43.3 | 221 | 8.6 | 363 | 3.0 | 221 | 2.3 |
| 2 | 2,300 | 55.1 | 224 | 7.0 | 2,000 | 17.7 | 224 | 4.0 |
| 3 | 29,801 | 528 | 227 | 8.5 | 29,497 | 449 | 227 | 3.2 |
| 4 | 35,232 | 678 | 230 | 13.1 | 34,924 | 583 | 230 | 2.5 |
| 5 | 41,123 | 897 | 233 | 10.3 | 40,811 | 834 | 233 | 2.5 |
| 6 | 47,486 | 996 | 236 | 7.0 | 47,170 | 771 | 236 | 4.0 |
| 8 | 61,676 | 1,426 | 242 | 7.1 | 61,352 | 1,252 | 242 | 4.1 |
| 12 | 96,248 | 2,415 | 254 | 22.9 | 95,908 | 1,962 | 254 | 8.5 |
| 16 | 139,716 | 3,857 | 266 | 10.1 | 139,360 | 2,681 | 266 | 4.4 |
| 24 | 256,412 | 7,512 | 290 | 12.3 | 256,024 | 5,267 | 290 | 3.8 |
| 32 | 417,908 | 13,492 | 314 | 15.0 | 417,488 | 8,094 | 314 | 5.3 |
| 64 | 1,634,772 | 103,169 | 410 | 13.9 | timeout | >20 s | 410 | 17.1 |
| 128 | not run |  | 602 | 21.1 | not run |  | 602 | 22.5 |
| 256 | not run |  | 986 | 41.8 | not run |  | 986 | 26.9 |
| 512 | not run |  | 1,754 | 54.1 | not run |  | 1,754 | 34.6 |
| 1024 | not run |  | 3,290 | 198 | not run |  | 3,290 | 74.3 |

| Configuration | Counter growth | Time growth | Counter: log-log fit / semi-log fit (upper half of the sizes), local exponents, per-step factors | Fastest other counter | Ends with |
|---|---|---|---|---|---|
| base | 2n^3 + 206n^2 + 3,915n + 16,148 (exact, n ≥ 3) | n^2.52 for n ≥ 5 (rms 0.12) | n^1.58 (R² 0.986) / 1.06^n (R² 0.964); last local exponents 1.5, 1.7, 2.0; last per-step factors 1.08, 1.06, 1.04 | – | stopped before n=128: predicted timeout: 103 s at n=64, power-law extrapolation gives 789 s at n=128 |
| FIX | 3n + 218 (exact) | n^1.47 for n ≥ 24 (rms 0.16) | n^0.60 (R² 0.966) / 1.00^n (R² 0.898); last local exponents 0.7, 0.8, 0.9; last per-step factors 1.00, 1.00, 1.00 | – | completed |
| MIN5 | 2n^3 + 206n^2 + 3,911n + 15,856 (exact, n ≥ 3) | n^1.51 for n ≥ 3 (rms 0.07) | n^1.30 (R² 0.989) / 1.09^n (R² 0.984); last local exponents 1.3, 1.5, 1.7; last per-step factors 1.10, 1.08, 1.06 | – | timeout (>20 s) at n=64 |
| FULL | 3n + 218 (exact) | n^1.37 for n ≥ 64 (rms 0.08) | n^0.60 (R² 0.966) / 1.00^n (R² 0.898); last local exponents 0.7, 0.8, 0.9; last per-step factors 1.00, 1.00, 1.00 | – | completed |
| FULL-eqsolve | 11.34^n (rms 0.05) | n^9.39 (rms 0.02) | n^6.47 (R² 0.975) / 9.77^n (R² 0.996); last local exponents 1.8, 5.0, 8.8; last per-step factors 3.47, 7.66, 12.45 | – | timeout (>20 s) at n=128; fitted on n=1..4 (accepted); resource bound (`budget`) hit from n=5; verdict differs from the intended one at n=5..64 |

Leave-one-out configurations (same counter):

| n | FULL-eqsolve count | FULL-eqsolve ms |
|---:|---:|---:|
| 1 | 363 | 8.1 |
| 2 | 1,260 | 11.6 |
| 3 | 9,655 | 134 |
| 4 | 120,230 | 1,945 |
| 5 | 172,326 ✗ [B] | 3,675 |
| 6 | 236,905 ✗ [B] | 4,412 |
| 8 | 93,319 ✗ [B] | 2,274 |
| 12 | 178,851 ✗ [B] | 5,133 |
| 16 | 82,365 ✗ [B] | 2,005 |
| 24 | 170,789 ✗ [B] | 3,759 |
| 32 | 25,113 ✗ [B] | 1,367 |
| 64 | 64,825 ✗ [B] | 5,996 |
| 128 | timeout | >20 s |

### eqchain-conf

Valid: conformance transported along n equality links (no associated type). Intended verdict: accepted. Primary counter: `summon.matches`.

| n | base count | base ms | FIX count | FIX ms | MIN5 count | MIN5 ms | FULL count | FULL ms |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 146 | 38.7 | 75 | 13.3 | 146 | 2.8 | 75 | 8.5 |
| 2 | 964 | 45.2 | 76 | 13.1 | 964 | 10.7 | 76 | 4.2 |
| 3 | 14,712 | 412 | 77 | 12.4 | 14,712 | 217 | 77 | 8.8 |
| 4 | 17,425 | 356 | 78 | 35.7 | 17,425 | 237 | 78 | 5.2 |
| 5 | 20,368 | 655 | 79 | 17.7 | 20,368 | 267 | 79 | 5.0 |
| 6 | 23,547 | 670 | 80 | 10.7 | 23,547 | 453 | 80 | 4.3 |
| 8 | 30,637 | 808 | 82 | 12.5 | 30,637 | 505 | 82 | 4.4 |
| 12 | 47,913 | 1,345 | 86 | 28.7 | 47,913 | 930 | 86 | 6.0 |
| 16 | 69,637 | 1,815 | 90 | 16.3 | 69,637 | 1,239 | 90 | 8.2 |
| 24 | 127,965 | 3,681 | 98 | 18.4 | 127,965 | 2,591 | 98 | 9.4 |
| 32 | 208,693 | 6,481 | 106 | 22.3 | 208,693 | 4,418 | 106 | 8.9 |
| 64 | 817,045 | 45,665 | 138 | 13.3 | timeout | >20 s | 138 | 10.1 |
| 128 | not run |  | 202 | 25.0 | not run |  | 202 | 30.3 |
| 256 | not run |  | 330 | 42.9 | not run |  | 330 | 39.8 |
| 512 | not run |  | 586 | 51.9 | not run |  | 586 | 36.4 |
| 1024 | not run |  | 1,098 | 68.7 | not run |  | 1,098 | 57.0 |

| Configuration | Counter growth | Time growth | Counter: log-log fit / semi-log fit (upper half of the sizes), local exponents, per-step factors | Fastest other counter | Ends with |
|---|---|---|---|---|---|
| base | n^3 + 103n^2 + 1,955n + 7,893 (exact, n ≥ 3) | n^2.60 for n ≥ 5 (rms 0.09) | n^1.58 (R² 0.986) / 1.06^n (R² 0.964); last local exponents 1.5, 1.7, 2.0; last per-step factors 1.08, 1.06, 1.04 | – | stopped before n=128: predicted timeout: 46 s at n=64, power-law extrapolation gives 322 s at n=128 |
| FIX | n + 74 (exact) | n^0.58 for n ≥ 64 (rms 0.14) | n^0.60 (R² 0.965) / 1.00^n (R² 0.899); last local exponents 0.7, 0.8, 0.9; last per-step factors 1.00, 1.00, 1.00 | – | completed |
| MIN5 | n^3 + 103n^2 + 1,955n + 7,893 (exact, n ≥ 3) | n^1.73 for n ≥ 3 (rms 0.10) | n^1.30 (R² 0.989) / 1.09^n (R² 0.984); last local exponents 1.3, 1.5, 1.7; last per-step factors 1.10, 1.08, 1.06 | – | timeout (>20 s) at n=64 |
| FULL | n + 74 (exact) | n^0.51 for n ≥ 6 (rms 0.21) | n^0.60 (R² 0.965) / 1.00^n (R² 0.899); last local exponents 0.7, 0.8, 0.9; last per-step factors 1.00, 1.00, 1.00 | – | completed |

### eqchain-neg

Ill-typed: the chain of n links has its middle link missing, so T{n} is not P. Intended verdict: rejected. Primary counter: `summon.matches`.

| n | base count | base ms | FIX count | FIX ms | MIN5 count | MIN5 ms | FULL count | FULL ms |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 143 | 29.8 | 143 | 10.1 | 3 | 3.1 | 1 | 4.3 |
| 2 | 145 | 56.6 | 145 | 11.9 | 145 | 3.0 | 145 | 5.3 |
| 3 | 45,728 (accepted!) | 993 | 149 | 12.7 | 45,728 (accepted!) | 620 | 149 | 4.8 |
| 4 | 57,443 (accepted!) | 976 | 151 | 12.8 | 57,443 (accepted!) | 822 | 151 | 4.5 |
| 5 | 17,426 (accepted!) | 340 | 153 | 17.8 | 17,426 (accepted!) | 237 | 153 | 4.7 |
| 6 | 20,369 (accepted!) | 365 | 155 | 10.6 | 20,369 (accepted!) | 234 | 155 | 4.5 |
| 8 | 26,969 (accepted!) | 712 | 159 | 17.4 | 26,969 (accepted!) | 493 | 159 | 6.1 |
| 12 | 43,193 (accepted!) | 1,228 | 167 | 14.0 | 43,193 (accepted!) | 621 | 167 | 4.5 |
| 16 | 63,769 (accepted!) | 1,649 | 175 | 14.7 | 63,769 (accepted!) | 998 | 175 | 5.7 |
| 24 | 119,513 (accepted!) | 2,722 | 191 | 17.4 | 119,513 (accepted!) | 2,334 | 191 | 6.3 |
| 32 | 197,273 (accepted!) | 5,482 | 207 | 16.2 | 197,273 (accepted!) | 4,121 | 207 | 5.0 |
| 64 | 789,913 (accepted!) | 39,541 | 271 | 18.3 | timeout | >20 s | 271 | 7.6 |
| 128 | not run |  | 399 | 21.8 | not run |  | 399 | 11.2 |
| 256 | not run |  | 655 | 33.1 | not run |  | 655 | 14.8 |
| 512 | not run |  | 1,167 | 82.6 | not run |  | 1,167 | 43.6 |
| 1024 | not run |  | 2,191 | 90.7 | not run |  | 2,191 | 53.1 |

| Configuration | Counter growth | Time growth | Counter: log-log fit / semi-log fit (upper half of the sizes), local exponents, per-step factors | Fastest other counter | Ends with |
|---|---|---|---|---|---|
| base | n^3 + 100n^2 + 1,752n + 6,041 (exact, n ≥ 5) | undecided: n^2.8 (rms 0.12) or 1.07^n (rms 0.12) | n^1.74 (R² 0.993) / 1.06^n (R² 0.974); last local exponents 1.5, 1.7, 2.0; last per-step factors 1.08, 1.06, 1.04 | – | stopped before n=128: predicted timeout: 40 s at n=64, power-law extrapolation gives 285 s at n=128; fitted on n=3..64 (accepted); verdict differs from the intended one at n=3..64 |
| FIX | 2n + 143 (exact, n ≥ 3) | n^1.01 for n ≥ 12 (rms 0.14) | n^0.61 (R² 0.966) / 1.00^n (R² 0.897); last local exponents 0.7, 0.8, 0.9; last per-step factors 1.00, 1.00, 1.00 | – | completed |
| MIN5 | n^3 + 100n^2 + 1,752n + 6,041 (exact, n ≥ 5) | undecided: n^2.7 (rms 0.05) or 1.10^n (rms 0.08) | n^1.44 (R² 0.994) / 1.09^n (R² 0.986); last local exponents 1.4, 1.5, 1.7; last per-step factors 1.10, 1.08, 1.06 | – | timeout (>20 s) at n=64; fitted on n=3..32 (accepted); verdict differs from the intended one at n=3..32 |
| FULL | 2n + 143 (exact, n ≥ 3) | n^1.07 (rms 0.14) | n^0.61 (R² 0.966) / 1.00^n (R² 0.897); last local exponents 0.7, 0.8, 0.9; last per-step factors 1.00, 1.00, 1.00 | – | completed |
| FULL-eqsolve | undecided: n^3.2 (rms 1.04) or 1.07^n (rms 1.04) | undecided: no polynomial or 3.07^n (rms 0.61) | n^-0.92 (R² 0.401) / 0.98^n (R² 0.296); last local exponents -1.3, -6.5, 1.4; last per-step factors 0.94, 0.79, 1.03 | – | timeout (>20 s) at n=128; fitted on n=3..64 (rejected, resource bound hit); resource bound (`budget`) hit from n=3 |
| FULL-absmodel | 2n + 143 (exact, n ≥ 3) | undecided: n^5.6 (rms 0.37) or 1.01^n (rms 0.37) | n^0.61 (R² 0.966) / 1.00^n (R² 0.897); last local exponents 0.7, 0.8, 0.9; last per-step factors 1.00, 1.00, 1.00 | – | completed |
| FULL-absquotient | 2n + 143 (exact, n ≥ 3) | n^1.56 for n ≥ 32 (rms 0.34) | n^0.61 (R² 0.966) / 1.00^n (R² 0.897); last local exponents 0.7, 0.8, 0.9; last per-step factors 1.00, 1.00, 1.00 | – | completed |

Leave-one-out configurations (same counter):

| n | FULL-eqsolve count | FULL-eqsolve ms | FULL-absmodel count | FULL-absmodel ms | FULL-absquotient count | FULL-absquotient ms |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1 | 8.1 | 3 | 2.6 | 1 | 10.3 |
| 2 | 145 | 15.3 | 145 | 7.9 | 145 | 12.7 |
| 3 | 83,495 [B] | 1,789 | 149 | 9.6 | 149 | 9.1 |
| 4 | 148,246 [B] | 3,142 | 151 | 7.9 | 151 | 9.1 |
| 5 | 119,923 [B] | 2,551 | 153 | 7.9 | 153 | 13.5 |
| 6 | 172,017 [B] | 3,931 | 155 | 4.1 | 155 | 13.8 |
| 8 | 76,605 [B] | 2,190 | 159 | 7.8 | 159 | 16.6 |
| 12 | 154,429 [B] | 4,511 | 167 | 13.2 | 167 | 5.3 |
| 16 | 264,509 [B] | 11,150 | 175 | 12.4 | 175 | 9.5 |
| 24 | 157,543 [B] | 4,506 | 191 | 8.7 | 191 | 4.8 |
| 32 | 24,033 [B] | 1,633 | 207 | 12.4 | 207 | 13.7 |
| 64 | 63,201 [B] | 6,952 | 271 | 16.1 | 271 | 11.7 |
| 128 | timeout | >20 s | 399 | 16.2 | 399 | 19.9 |
| 256 | not run |  | 655 | 41.0 | 655 | 12.7 |
| 512 | not run |  | 1,167 | 22.9 | 1,167 | 57.5 |
| 1024 | not run |  | 2,191 | 134 | 2,191 | 67.3 |

### eqchain-goals

Valid: a chain of n links and n equality goals T0 == Ti, one per link. Intended verdict: accepted. Primary counter: `summon.matches`.

| n | base count | base ms | FIX count | FIX ms | MIN5 count | MIN5 ms | FULL count | FULL ms |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 72 | 13.7 | 2 | 5.6 | 72 | 1.1 | 2 | 0.8 |
| 2 | 951 | 67.0 | 4 | 4.6 | 951 | 11.7 | 4 | 1.6 |
| 3 | 15,485 | 196 | 6 | 6.2 | 15,485 | 442 | 6 | 1.1 |
| 4 | 35,677 | 682 | 8 | 8.0 | 35,677 | 868 | 8 | 1.4 |
| 5 | 61,925 | 1,376 | 10 | 7.1 | 61,925 | 2,110 | 10 | 2.0 |
| 6 | 94,937 | 2,486 | 12 | 24.2 | 94,937 | 2,427 | 12 | 1.7 |
| 8 | 184,205 | 7,361 | 16 | 17.6 | 184,205 | 4,434 | 16 | 2.3 |
| 12 | 477,725 | 16,491 | 24 | 10.5 | 477,725 | 12,831 | 24 | 11.8 |
| 16 | 969,997 | 35,814 | 32 | 28.2 | timeout | >20 s | 32 | 17.2 |
| 24 | timeout | >120 s | 48 | 39.8 | not run |  | 48 | 9.7 |
| 32 | not run |  | 64 | 33.5 | not run |  | 64 | 14.3 |
| 64 | not run |  | 128 | 64.7 | not run |  | 128 | 41.6 |
| 128 | not run |  | 256 | 413 | not run |  | 256 | 356 |
| 256 | not run |  | 512 | 1,591 | not run |  | 512 | 730 |
| 512 | not run |  | 1,024 | 4,900 | not run |  | 1,024 | 4,206 |
| 1024 | not run |  | timeout | >20 s | not run |  | 2,048 | 23,172 |

| Configuration | Counter growth | Time growth | Counter: log-log fit / semi-log fit (upper half of the sizes), local exponents, per-step factors | Fastest other counter | Ends with |
|---|---|---|---|---|---|
| base | n^4 + 100n^3 + 1,731n^2 + 4,200n − 15,475 (exact, n ≥ 3) | n^2.85 for n ≥ 4 (rms 0.14) | n^2.36 (R² 1.000) / 1.28^n (R² 0.981); last local exponents 2.3, 2.4, 2.5; last per-step factors 1.39, 1.27, 1.19 | – | timeout (>120 s) at n=24 |
| FIX | 2n (exact) | n^2.09 for n ≥ 32 (rms 0.21) | n^1.00 (R² 1.000) / 1.01^n (R² 0.813); last local exponents 1.0, 1.0, 1.0; last per-step factors 1.01, 1.01, 1.00 | – | timeout (>20 s) at n=1024 |
| MIN5 | n^2.44 for n ≥ 3 (rms 0.05) | n^2.38 for n ≥ 3 (rms 0.13) | n^2.33 (R² 1.000) / 1.33^n (R² 0.986); last local exponents 2.3, 2.3, 2.4; last per-step factors 1.53, 1.39, 1.27 | – | timeout (>20 s) at n=16 |
| FULL | 2n (exact) | n^2.21 for n ≥ 24 (rms 0.25) | n^1.00 (R² 1.000) / 1.00^n (R² 0.780); last local exponents 1.0, 1.0, 1.0; last per-step factors 1.01, 1.00, 1.00 | – | completed |
| FULL-eqsolve | 10.91^n (rms 0.06) | undecided: n^7.0 (rms 0.39) or 9.44^n (rms 0.23) | n^6.73 (R² 0.982) / 10.63^n (R² 0.999); last local exponents 3.0, 5.4, 8.8; last per-step factors 8.14, 9.09, 12.43 | – | stopped before n=8: predicted timeout: 17 s at n=6, power-law extrapolation gives 74 s at n=8; fitted on n=1..4 (accepted); resource bound (`budget`) hit from n=5; verdict differs from the intended one at n=5..6 |

Leave-one-out configurations (same counter):

| n | FULL-eqsolve count | FULL-eqsolve ms |
|---:|---:|---:|
| 1 | 72 | 6.4 |
| 2 | 586 | 24.9 |
| 3 | 5,324 | 97.2 |
| 4 | 66,171 | 1,381 |
| 5 | 265,019 ✗ [B] | 6,604 |
| 6 | 599,816 ✗ [B] | 16,902 |

### assoceq

Valid: n equalities T{i}.X == T{i+1}.X; goal T0.X == T{n}.X. Intended verdict: accepted. Primary counter: `summon.matches`.

| n | base count | base ms | FIX count | FIX ms | MIN5 count | MIN5 ms | FULL count | FULL ms |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1,110 | 57.3 | 293 | 21.1 | 810 | 27.1 | 293 | 10.3 |
| 2 | 4,423 | 236 | 447 | 23.3 | 4,115 | 118 | 447 | 18.5 |
| 3 | 60,438 | 1,679 | 607 | 49.4 | 60,122 | 1,038 | 607 | 29.8 |
| 4 | 75,042 | 1,800 | 773 | 42.5 | 74,718 | 1,068 | 773 | 46.5 |
| 5 | 91,512 | 2,463 | 945 | 83.1 | 91,180 | 1,662 | 945 | 60.2 |
| 6 | 109,938 | 2,973 | 1,123 | 82.8 | 109,598 | 2,258 | 1,123 | 58.4 |
| 8 | 153,018 | 3,599 | 1,497 | 111 | 152,662 | 2,658 | 1,497 | 108 |
| 12 | 266,610 | 9,148 | 2,317 | 244 | 266,222 | 5,407 | 2,317 | 165 |
| 16 | 421,578 | 16,124 | 3,233 | 374 | 421,158 | 8,522 | 3,233 | 258 |
| 24 | 878,682 | 42,382 | 5,353 | 515 | timeout | >20 s | 5,353 | 478 |
| 32 | crash (out of memory) | 86 s wall | 7,857 | 868 | not run |  | 7,857 | 798 |
| 48 | crash (out of memory) | 103 s wall |  |  |  |  |  |  |
| 64 | not run |  | 21,713 | 4,764 | not run |  | 21,713 | 3,012 |
| 128 | not run |  | timeout | >20 s | not run |  | 67,857 | 15,085 |
| 256 | not run |  | not run |  | not run |  | timeout | >120 s |

| Configuration | Counter growth | Time growth | Counter: log-log fit / semi-log fit (upper half of the sizes), local exponents, per-step factors | Fastest other counter | Ends with |
|---|---|---|---|---|---|
| base | 15n^3 + 753n^2 + 8,778n + 26,922 (exact, n ≥ 3) | n^2.50 for n ≥ 3 (rms 0.07) | n^1.50 (R² 0.992) / 1.12^n (R² 0.987); last local exponents 1.4, 1.6, 1.8; last per-step factors 1.15, 1.12, 1.10 | – | crash (exit 134) at n=32 |
| FIX | 3n^2 + 145n + 145 (exact) | undecided: n^2.7 (rms 0.08) or 1.06^n (rms 0.07) | n^1.29 (R² 0.996) / 1.05^n (R² 0.942); last local exponents 1.2, 1.3, 1.5; last per-step factors 1.07, 1.05, 1.03 | – | timeout (>20 s) at n=128 |
| MIN5 | 15n^3 + 753n^2 + 8,770n + 26,630 (exact, n ≥ 3) | undecided: n^1.8 (rms 0.09) or 1.18^n (rms 0.13) | n^1.32 (R² 0.995) / 1.15^n (R² 0.994); last local exponents 1.2, 1.4, 1.6; last per-step factors 1.18, 1.15, 1.12 | – | timeout (>20 s) at n=24 |
| FULL | 3n^2 + 145n + 145 (exact) | n^1.99 for n ≥ 4 (rms 0.10) | n^1.38 (R² 0.994) / 1.03^n (R² 0.918); last local exponents 1.3, 1.5, 1.6; last per-step factors 1.05, 1.03, 1.02 | – | timeout (>120 s) at n=256 |
| FULL-eqsolve | undecided: no polynomial or 2.93^n (rms 0.63) | undecided: no polynomial or 3.13^n (rms 0.36) | n^-0.28 (R² 0.086) / 0.99^n (R² 0.032); last local exponents 1.9, -5.4, 1.5; last per-step factors 1.10, 0.82, 1.03 | `index.unavailable`: 2n^2 + 136n (exact) | timeout (>20 s) at n=128; fitted on n=4..64 (rejected, resource bound hit); resource bound (`budget`) hit from n=4; verdict differs from the intended one at n=4..64 |

Leave-one-out configurations (same counter):

| n | FULL-eqsolve count | FULL-eqsolve ms |
|---:|---:|---:|
| 1 | 441 | 25.8 |
| 2 | 1,680 | 46.9 |
| 3 | 14,040 | 315 |
| 4 | 68,814 ✗ [B] | 1,408 |
| 5 | 98,041 ✗ [B] | 1,984 |
| 6 | 33,054 ✗ [B] | 929 |
| 8 | 50,960 ✗ [B] | 1,532 |
| 12 | 101,268 ✗ [B] | 3,843 |
| 16 | 51,870 ✗ [B] | 1,496 |
| 24 | 111,662 ✗ [B] | 3,036 |
| 32 | 23,550 ✗ [B] | 2,341 |
| 64 | 66,718 ✗ [B] | 9,487 |
| 128 | timeout | >20 s |

### assocneg

Ill-typed: like assoceq with the middle equality missing. Intended verdict: rejected. Primary counter: `summon.matches`.

| n | base count | base ms | FIX count | FIX ms | MIN5 count | MIN5 ms | FULL count | FULL ms |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 441 | 41.5 | 145 | 7.6 | 5 | 1.1 | 5 | 2.0 |
| 2 | 899 | 43.9 | 295 | 18.0 | 595 | 31.1 | 295 | 22.2 |
| 3 | 47,781 (accepted!) | 954 | 452 | 29.1 | 47,469 (accepted!) | 862 | 452 | 26.8 |
| 4 | 60,817 (accepted!) | 1,384 | 614 | 42.7 | 60,497 (accepted!) | 1,199 | 614 | 42.1 |
| 5 | 75,969 (accepted!) | 1,421 | 782 | 43.9 | 75,641 (accepted!) | 1,420 | 782 | 56.6 |
| 6 | 92,611 (accepted!) | 2,371 | 956 | 127 | 92,275 (accepted!) | 1,845 | 956 | 99.7 |
| 8 | 131,895 (accepted!) | 3,224 | 1,322 | 124 | 131,543 (accepted!) | 3,142 | 1,322 | 96.0 |
| 12 | 236,983 (accepted!) | 6,904 | 2,126 | 181 | 236,599 (accepted!) | 5,732 | 2,126 | 291 |
| 16 | 382,231 (accepted!) | 9,290 | 3,026 | 237 | 381,815 (accepted!) | 9,106 | 3,026 | 376 |
| 24 | 816,247 (accepted!) | 55,601 | 5,114 | 692 | timeout | >20 s | 5,114 | 690 |
| 32 | crash (out of memory) | 102 s wall | 7,586 | 915 | not run |  | 7,586 | 1,155 |
| 64 | not run |  | 21,314 | 4,058 | not run |  | 21,314 | 4,177 |
| 128 | not run |  | timeout | >20 s | not run |  | 67,202 | 16,597 |
| 256 | not run |  | not run |  | not run |  | 232,706 | 116,179 |

| Configuration | Counter growth | Time growth | Counter: log-log fit / semi-log fit (upper half of the sizes), local exponents, per-step factors | Fastest other counter | Ends with |
|---|---|---|---|---|---|
| base | 15n^3 + 715n^2 + 7,412n + 19,159 (exact, n ≥ 5) | undecided: n^4.0 (rms 0.18) or 1.23^n (rms 0.13) | n^1.66 (R² 0.996) / 1.12^n (R² 0.989); last local exponents 1.4, 1.7, 1.9; last per-step factors 1.16, 1.13, 1.10 | – | crash (exit 134) at n=32; fitted on n=3..24 (accepted); verdict differs from the intended one at n=3..24 |
| FIX | 3n^2 + 141n + 2 (exact, n ≥ 3) | n^2.17 for n ≥ 8 (rms 0.11) | n^1.34 (R² 0.997) / 1.05^n (R² 0.936); last local exponents 1.3, 1.4, 1.5; last per-step factors 1.07, 1.05, 1.03 | – | timeout (>20 s) at n=128 |
| MIN5 | n^1.75 (rms 0.01) | n^1.83 (rms 0.04) | n^1.45 (R² 0.997) / 1.15^n (R² 0.994); last local exponents 1.2, 1.4, 1.7; last per-step factors 1.19, 1.16, 1.13 | – | timeout (>20 s) at n=24; fitted on n=3..16 (accepted); verdict differs from the intended one at n=3..16 |
| FULL | 3n^2 + 141n + 2 (exact, n ≥ 3) | n^2.30 for n ≥ 12 (rms 0.11) | n^1.53 (R² 0.996) / 1.02^n (R² 0.902); last local exponents 1.5, 1.7, 1.8; last per-step factors 1.03, 1.02, 1.01 | – | stopped before n=512: predicted timeout: 116 s at n=256, power-law extrapolation gives 813 s at n=512 |
| FULL-eqsolve | undecided: no polynomial or 3.05^n (rms 0.63) | undecided: n^3.7 (rms 0.31) or 1.08^n (rms 0.30) | n^-0.21 (R² 0.050) / 1.00^n (R² 0.013); last local exponents 2.0, -5.3, 1.5; last per-step factors 1.10, 0.83, 1.03 | `index.unavailable`: 2n^2 + 134n − 136 (exact) | stopped before n=128: predicted timeout: 11 s at n=64, power-law extrapolation gives 44 s at n=128; fitted on n=3..64 (rejected, resource bound hit); resource bound (`budget`) hit from n=3 |

Leave-one-out configurations (same counter):

| n | FULL-eqsolve count | FULL-eqsolve ms |
|---:|---:|---:|
| 1 | 5 | 2.2 |
| 2 | 295 | 30.2 |
| 3 | 70,446 [B] | 1,636 |
| 4 | 124,827 [B] | 2,677 |
| 5 | 69,682 [B] | 1,283 |
| 6 | 99,234 [B] | 2,083 |
| 8 | 41,916 [B] | 954 |
| 12 | 87,628 [B] | 3,081 |
| 16 | 46,741 [B] | 1,534 |
| 24 | 103,453 [B] | 3,478 |
| 32 | 22,698 [B] | 2,671 |
| 64 | 65,386 [B] | 10,872 |

### breadth-traits

Valid: n conformances A{i} is P{i} (n traits, n types) and one lookup. Intended verdict: accepted. Primary counter: `summon.matches`.

| n | base count | base ms | FIX count | FIX ms | MIN5 count | MIN5 ms | FULL count | FULL ms |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 8 | 79 | 19.6 | 79 | 18.1 | 2 | 0.8 | 2 | 1.8 |
| 16 | 87 | 37.7 | 87 | 7.6 | 2 | 1.0 | 2 | 2.5 |
| 32 | 103 | 18.2 | 103 | 9.6 | 2 | 1.9 | 2 | 3.9 |
| 64 | 135 | 30.6 | 135 | 18.4 | 2 | 2.3 | 2 | 9.5 |
| 128 | 199 | 38.3 | 199 | 39.3 | 2 | 9.1 | 2 | 7.9 |
| 256 | 327 | 208 | 327 | 217 | 2 | 9.3 | 2 | 18.1 |
| 512 | 583 | 352 | 583 | 302 | 2 | 30.9 | 2 | 24.4 |
| 1024 | 1,095 | 1,805 | 1,095 | 2,022 | 2 | 61.6 | 2 | 41.7 |

| Configuration | Counter growth | Time growth | Counter: log-log fit / semi-log fit (upper half of the sizes), local exponents, per-step factors | Fastest other counter | Ends with |
|---|---|---|---|---|---|
| base | n + 71 (exact) | n^1.87 for n ≥ 32 (rms 0.26) | n^0.82 (R² 0.997) / 1.00^n (R² 0.945); last local exponents 0.7, 0.8, 0.9; last per-step factors 1.00, 1.00, 1.00 | – | completed |
| FIX | n + 71 (exact) | n^1.80 for n ≥ 16 (rms 0.28) | n^0.82 (R² 0.997) / 1.00^n (R² 0.945); last local exponents 0.7, 0.8, 0.9; last per-step factors 1.00, 1.00, 1.00 | – | completed |
| MIN5 | flat | n^1.17 (rms 0.23) | – | `solver.goalSteps`: 2n + 6 (exact) | completed |
| FULL | flat | below 50 ms throughout | – | `absmodel.facts`: n + 63 (exact) | completed |

### breadth-types

Valid: n conformances A{i} is P (one trait, n types) and one lookup. Intended verdict: accepted. Primary counter: `summon.matches`.

| n | base count | base ms | FIX count | FIX ms | MIN5 count | MIN5 ms | FULL count | FULL ms |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 8 | 79 | 71.9 | 79 | 11.5 | 9 | 0.7 | 9 | 1.9 |
| 16 | 87 | 32.9 | 87 | 14.8 | 17 | 0.9 | 17 | 2.4 |
| 32 | 103 | 18.9 | 103 | 11.2 | 33 | 1.3 | 33 | 2.2 |
| 64 | 135 | 27.7 | 135 | 31.5 | 65 | 2.9 | 65 | 3.9 |
| 128 | 199 | 36.0 | 199 | 38.5 | 129 | 6.2 | 129 | 10.9 |
| 256 | 327 | 104 | 327 | 76.3 | 257 | 7.7 | 257 | 11.7 |
| 512 | 583 | 378 | 583 | 369 | 513 | 15.7 | 513 | 62.8 |
| 1024 | 1,095 | 1,992 | 1,095 | 1,862 | 1,025 | 43.5 | 1,025 | 69.4 |

| Configuration | Counter growth | Time growth | Counter: log-log fit / semi-log fit (upper half of the sizes), local exponents, per-step factors | Fastest other counter | Ends with |
|---|---|---|---|---|---|
| base | n + 71 (exact) | n^2.27 for n ≥ 32 (rms 0.09) | n^0.82 (R² 0.997) / 1.00^n (R² 0.945); last local exponents 0.7, 0.8, 0.9; last per-step factors 1.00, 1.00, 1.00 | – | completed |
| FIX | n + 71 (exact) | n^2.60 for n ≥ 64 (rms 0.05) | n^0.82 (R² 0.997) / 1.00^n (R² 0.945); last local exponents 0.7, 0.8, 0.9; last per-step factors 1.00, 1.00, 1.00 | – | completed |
| MIN5 | n + 1 (exact) | below 50 ms throughout | n^1.00 (R² 1.000) / 1.00^n (R² 0.920); last local exponents 1.0, 1.0, 1.0; last per-step factors 1.01, 1.00, 1.00 | – | completed |
| FULL | n + 1 (exact) | n^1.25 (rms 0.30) | n^1.00 (R² 1.000) / 1.00^n (R² 0.920); last local exponents 1.0, 1.0, 1.0; last per-step factors 1.01, 1.00, 1.00 | – | completed |

### breadth-square

Valid: n traits x n types = n*n conformances and n lookups (the shape of breadth40). Intended verdict: accepted. Primary counter: `summon.matches`.

| n | base count | base ms | FIX count | FIX ms | MIN5 count | MIN5 ms | FULL count | FULL ms |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 4 | 348 | 39.1 | 348 | 30.1 | 20 | 0.9 | 20 | 2.7 |
| 6 | 642 | 32.9 | 642 | 20.6 | 42 | 1.7 | 42 | 3.1 |
| 8 | 1,080 | 63.4 | 1,080 | 44.5 | 72 | 4.2 | 72 | 4.1 |
| 12 | 2,580 | 146 | 2,580 | 64.0 | 156 | 5.6 | 156 | 6.4 |
| 16 | 5,232 | 342 | 5,232 | 311 | 272 | 7.4 | 272 | 20.2 |
| 24 | 15,528 | 965 | 15,528 | 907 | 600 | 24.0 | 600 | 35.7 |
| 32 | 35,040 | 2,437 | 35,040 | 2,228 | 1,056 | 27.1 | 1,056 | 53.7 |
| 40 | 66,840 | 6,537 | 66,840 | 5,668 | 1,640 | 53.3 | 1,640 | 58.1 |
| 48 | 114,000 | 14,921 | 114,000 | 11,618 | 2,352 | 50.5 | 2,352 | 79.7 |

| Configuration | Counter growth | Time growth | Counter: log-log fit / semi-log fit (upper half of the sizes), local exponents, per-step factors | Fastest other counter | Ends with |
|---|---|---|---|---|---|
| base | n^3 + 71n (exact) | undecided: n^3.9 (rms 0.12) or 1.13^n (rms 0.14) | n^2.81 (R² 1.000) / 1.10^n (R² 0.980); last local exponents 2.8, 2.9, 2.9; last per-step factors 1.11, 1.08, 1.07 | – | completed |
| FIX | n^3 + 71n (exact) | n^3.56 for n ≥ 12 (rms 0.18) | n^2.81 (R² 1.000) / 1.10^n (R² 0.980); last local exponents 2.8, 2.9, 2.9; last per-step factors 1.11, 1.08, 1.07 | – | completed |
| MIN5 | n^2 + n (exact) | undecided: n^1.7 (rms 0.19) or 1.07^n (rms 0.30) | n^1.96 (R² 1.000) / 1.07^n (R² 0.975); last local exponents 2.0, 2.0, 2.0; last per-step factors 1.07, 1.06, 1.05 | – | completed |
| FULL | n^2 + n (exact) | n^1.66 for n ≥ 6 (rms 0.22) | n^1.96 (R² 1.000) / 1.07^n (R² 0.975); last local exponents 2.0, 2.0, 2.0; last per-step factors 1.07, 1.06, 1.05 | – | completed |

### div-branch

Ill-typed: Yb is P is underivable; b givens `S_j<T> is P => T is P` make the search grow. Intended verdict: rejected. Primary counter: `summon.matches`.

| n | base count | base ms | FIX count | FIX ms | MIN5 count | MIN5 ms | FULL count | FULL ms |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1,350 | 29.2 | 1,350 | 15.6 | 20 | 2.8 | 1 | 2.4 |
| 2 | 110,449 | 1,400 | 110,449 | 1,909 | 3,069 | 207 | 1 | 6.4 |
| 3 | timeout | >20 s | 159,579 [B] | 3,362 | 118,096 | 10,239 | 1 | 2.4 |
| 4 | not run |  | 202,021 [B] | 6,422 | not run |  | 1 | 2.5 |
| 5 | not run |  | 117,151 [B] | 4,309 | not run |  | 1 | 5.4 |
| 6 | not run |  | 236,361 [B] | 9,622 | not run |  | 1 | 4.0 |
| 8 | not run |  | 91,261 [B] | 5,332 | not run |  | 1 | 2.9 |
| 12 | not run |  | 25,749 [B] | 2,353 | not run |  | 1 | 3.2 |
| 16 | not run |  | 46,957 [B] | 5,730 | not run |  | 1 | 7.7 |
| 32 | not run |  | not run |  | not run |  | 1 | 4.3 |

| Configuration | Counter growth | Time growth | Counter: log-log fit / semi-log fit (upper half of the sizes), local exponents, per-step factors | Fastest other counter | Ends with |
|---|---|---|---|---|---|
| base | too few points (2) | too few points (2) | n^6.35 (R² 1.000) / 81.81^n (R² 1.000); last local exponents 6.4; last per-step factors 81.81 | – | timeout (>20 s) at n=3 |
| FIX | undecided: n^8.8 (rms 1.13) or 1.87^n (rms 1.13) | undecided: no polynomial or 40.00^n (rms 0.49) | n^-1.86 (R² 0.721) / 0.85^n (R² 0.605); last local exponents -3.3, -3.1, 2.1; last per-step factors 0.62, 0.73, 1.16 | `solver.goalSteps`: 6n + 6 (exact) | stopped before n=32: predicted timeout: 6 s at n=16, power-law extrapolation gives 49 s at n=32; fitted on n=3..16 (rejected, resource bound hit); resource bound (`budget`) hit from n=3 |
| MIN5 | too few points (3) | too few points (3) | n^7.83 (R² 0.997) / 76.84^n (R² 0.992); last local exponents 7.3, 9.0; last per-step factors 153.45, 38.48 | – | stopped before n=4: predicted timeout: 10 s at n=3, power-law extrapolation gives 163 s at n=4 |
| FULL | flat | below 50 ms throughout | – | `solver.goalSteps`: 6n + 6 (exact) | completed |
| FULL-absmodel | too few points (2) | too few points (2) | n^7.26 (R² 1.000) / 153.45^n (R² 1.000); last local exponents 7.3; last per-step factors 153.45 | – | timeout (>20 s) at n=3 |

Leave-one-out configurations (same counter):

| n | FULL-absmodel count | FULL-absmodel ms |
|---:|---:|---:|
| 1 | 20 | 5.5 |
| 2 | 3,069 | 385 |
| 3 | timeout | >20 s |

### div-branch-eq

Ill-typed: div_branch with an unrelated equality A == B in scope. Intended verdict: rejected. Primary counter: `summon.matches`.

| n | base count | base ms | FIX count | FIX ms | MIN5 count | MIN5 ms | FULL count | FULL ms |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1,369 | 67.5 | 1,369 | 28.2 | 1,369 | 16.1 | 1 | 4.2 |
| 2 | 111,983 | 1,954 | 111,983 | 2,008 | 111,983 | 1,472 | 1 | 5.0 |
| 3 | timeout | >20 s | 161,765 [B] | 4,458 | timeout | >20 s | 1 | 7.8 |
| 4 | not run |  | 204,751 [B] | 7,567 | not run |  | 1 | 3.7 |
| 5 | not run |  | 118,713 [B] | 5,319 | not run |  | 1 | 8.5 |
| 6 | not run |  | 239,471 [B] | 11,422 | not run |  | 1 | 4.5 |
| 8 | not run |  | 92,431 [B] | 6,522 | not run |  | 1 | 4.7 |
| 12 | not run |  | 26,063 [B] | 2,888 | not run |  | 1 | 4.8 |
| 16 | not run |  | 47,503 [B] | 6,871 | not run |  | 1 | 5.9 |
| 32 | not run |  | not run |  | not run |  | 1 | 10.1 |

| Configuration | Counter growth | Time growth | Counter: log-log fit / semi-log fit (upper half of the sizes), local exponents, per-step factors | Fastest other counter | Ends with |
|---|---|---|---|---|---|
| base | too few points (2) | too few points (2) | n^6.35 (R² 1.000) / 81.80^n (R² 1.000); last local exponents 6.4; last per-step factors 81.80 | – | timeout (>20 s) at n=3 |
| FIX | undecided: n^8.8 (rms 1.13) or 1.87^n (rms 1.13) | undecided: no polynomial or 40.00^n (rms 0.47) | n^-1.86 (R² 0.722) / 0.85^n (R² 0.606); last local exponents -3.3, -3.1, 2.1; last per-step factors 0.62, 0.73, 1.16 | `solver.goalSteps`: 6n + 6 (exact) | stopped before n=32: predicted timeout: 7 s at n=16, power-law extrapolation gives 55 s at n=32; fitted on n=3..16 (rejected, resource bound hit); resource bound (`budget`) hit from n=3 |
| MIN5 | too few points (2) | too few points (2) | n^6.35 (R² 1.000) / 81.80^n (R² 1.000); last local exponents 6.4; last per-step factors 81.80 | – | timeout (>20 s) at n=3 |
| FULL | flat | below 50 ms throughout | – | `solver.goalSteps`: 6n + 6 (exact) | completed |
| FULL-absmodel | undecided: no polynomial or 40.00^n (rms 0.21) | undecided: no polynomial or 40.00^n (rms 0.31) | n^0.28 (R² 0.024) / 1.08^n (R² 0.045); last local exponents 0.8, -2.4, 3.8; last per-step factors 1.27, 0.58, 2.02 | `solver.goalSteps`: 6n + 6 (exact) | stopped before n=8: predicted timeout: 15 s at n=6, power-law extrapolation gives 72 s at n=8; fitted on n=3..6 (rejected, resource bound hit); resource bound (`budget`) hit from n=3 |
| FULL-absquotient | undecided: no polynomial or 40.00^n (rms 0.21) | undecided: no polynomial or 40.00^n (rms 0.23) | n^0.28 (R² 0.024) / 1.08^n (R² 0.045); last local exponents 0.8, -2.4, 3.8; last per-step factors 1.27, 0.58, 2.02 | `solver.goalSteps`: 6n + 6 (exact) | stopped before n=8: predicted timeout: 15 s at n=6, power-law extrapolation gives 79 s at n=8; fitted on n=3..6 (rejected, resource bound hit); resource bound (`budget`) hit from n=3 |

Leave-one-out configurations (same counter):

| n | FULL-absmodel count | FULL-absmodel ms | FULL-absquotient count | FULL-absquotient ms |
|---:|---:|---:|---:|---:|
| 1 | 1,369 | 29.0 | 1,369 | 18.7 |
| 2 | 111,983 | 1,822 | 111,983 | 2,114 |
| 3 | 161,765 [B] | 4,026 | 161,765 [B] | 4,433 |
| 4 | 204,751 [B] | 8,892 | 204,751 [B] | 8,043 |
| 5 | 118,713 [B] | 5,388 | 118,713 [B] | 5,365 |
| 6 | 239,471 [B] | 14,693 | 239,471 [B] | 15,217 |

### div-trunc

Ill-typed: div_branch with base facts S_j<S_j<Xi>> is P (deeper than the model's truncation). Intended verdict: rejected. Primary counter: `summon.matches`.

| n | base count | base ms | FIX count | FIX ms | MIN5 count | MIN5 ms | FULL count | FULL ms |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1,369 | 30.4 | 1,369 | 35.6 | 39 | 1.4 | 39 | 7.0 |
| 2 | 113,517 | 2,047 | 113,517 | 2,369 | 6,137 | 231 | 6,137 | 293 |
| 3 | timeout | >20 s | 166,137 [B] | 4,586 | 236,191 | 12,397 | 118,093 [B] | 7,230 |
| 4 | not run |  | 212,941 [B] | 8,465 | not run |  | 87,377 [B] | 5,611 |
| 5 | not run |  | 124,961 [B] | 6,541 | not run |  | 78,121 [B] | 6,880 |
| 6 | not run |  | 42,477 [B] | 2,341 | not run |  | 223,945 [B] | 20,185 |
| 8 | not run |  | 100,621 [B] | 8,045 | not run |  | 149,793 [B] | 18,758 |
| 12 | not run |  | not run |  | not run |  | 90,481 [B] | 14,434 |
| 16 | not run |  | not run |  | not run |  | 17,473 [B] | 3,412 |
| 32 | not run |  | not run |  | not run |  | crash (out of memory) | 45 s wall |

| Configuration | Counter growth | Time growth | Counter: log-log fit / semi-log fit (upper half of the sizes), local exponents, per-step factors | Fastest other counter | Ends with |
|---|---|---|---|---|---|
| base | too few points (2) | too few points (2) | n^6.37 (R² 1.000) / 82.92^n (R² 1.000); last local exponents 6.4; last per-step factors 82.92 | – | timeout (>20 s) at n=3 |
| FIX | undecided: n^4.3 (rms 0.76) or 1.73^n (rms 0.76) | undecided: no polynomial or 40.00^n (rms 0.54) | n^-0.15 (R² 0.004) / 1.00^n (R² 0.000); last local exponents -2.4, -5.9, 3.0; last per-step factors 0.59, 0.34, 1.54 | `solver.goalSteps`: 12n + 6 (exact) | stopped before n=12: predicted timeout: 8 s at n=8, power-law extrapolation gives 46 s at n=12; fitted on n=3..8 (rejected, resource bound hit); resource bound (`budget`) hit from n=3 |
| MIN5 | too few points (3) | too few points (3) | n^7.86 (R² 0.997) / 77.82^n (R² 0.991); last local exponents 7.3, 9.0; last per-step factors 157.36, 38.49 | – | stopped before n=4: predicted timeout: 12 s at n=3, power-law extrapolation gives 209 s at n=4 |
| FULL | undecided: no polynomial or no exponential | undecided: no polynomial or no exponential | n^-2.40 (R² 0.863) / 0.78^n (R² 0.931); last local exponents -1.4, -1.2, -5.7; last per-step factors 0.82, 0.88, 0.66 | `absmodel.work`: n^2 + n + 654 (exact) | crash (exit 134) at n=32; fitted on n=3..16 (rejected, resource bound hit); resource bound (`budget`) hit from n=3 |
| FULL-absmodel | too few points (2) | too few points (2) | n^7.30 (R² 1.000) / 157.36^n (R² 1.000); last local exponents 7.3; last per-step factors 157.36 | – | stopped before n=4: predicted timeout: 13 s at n=3, power-law extrapolation gives 154 s at n=4; fitted on n=1..2 (rejected); resource bound (`budget`) hit from n=3 |

Leave-one-out configurations (same counter):

| n | FULL-absmodel count | FULL-absmodel ms |
|---:|---:|---:|
| 1 | 39 | 9.8 |
| 2 | 6,137 | 386 |
| 3 | 118,093 [B] | 12,825 |

### div-depth

Ill-typed: div_branch with b = 2; the size is the depth bound HYLO_TC_MAXDEPTH = d (>= 5, below which the standard library fails). Intended verdict: rejected. Primary counter: `summon.matches`. Environment: `HYLO_TC_MAXDEPTH=n`.

| n | base count | base ms | FIX count | FIX ms | MIN5 count | MIN5 ms | FULL count | FULL ms |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 5 | 3,313 | 44.7 | 3,313 | 37.3 | 93 | 3.7 | 1 | 5.8 |
| 6 | 6,769 | 148 | 6,769 | 129 | 189 | 19.9 | 1 | 4.5 |
| 8 | 27,505 | 365 | 27,505 | 339 | 765 | 78.2 | 1 | 2.3 |
| 10 | 110,449 | 1,953 | 110,449 | 2,241 | 3,069 | 179 | 1 | 1.9 |
| 12 | 442,225 | 8,442 | 294,769 [B] | 5,115 | 12,285 | 1,405 | 1 | 2.0 |
| 14 | timeout | >20 s | 294,769 [B] | 5,758 | 49,149 | 4,208 | 1 | 22.4 |
| 16 | not run |  | 294,769 [B] | 5,599 | timeout | >20 s | 1 | 1.9 |
| 20 | not run |  | 294,769 [B] | 5,345 | not run |  | 1 | 6.2 |
| 24 | not run |  | 294,769 [B] | 5,346 | not run |  | 1 | 7.1 |
| 32 | not run |  | 294,769 [B] | 5,407 | not run |  | 1 | 2.0 |
| 40 | not run |  | 294,769 [B] | 5,506 | not run |  | 1 | 2.3 |

| Configuration | Counter growth | Time growth | Counter: log-log fit / semi-log fit (upper half of the sizes), local exponents, per-step factors | Fastest other counter | Ends with |
|---|---|---|---|---|---|
| base | 2.01^n (rms 0.01) | undecided: n^6.9 (rms 0.26) or 2.06^n (rms 0.19) | n^6.83 (R² 0.997) / 2.00^n (R² 1.000); last local exponents 4.9, 6.2, 7.6; last per-step factors 2.02, 2.00, 2.00 | – | timeout (>20 s) at n=14 |
| FIX | 2.02^n (rms 0.01) | undecided: n^6.3 (rms 0.28) or 2.16^n (rms 0.23) | n^5.44 (R² 0.995) / 2.01^n (R² 1.000); last local exponents 3.9, 4.9, 6.2; last per-step factors 2.04, 2.02, 2.00 | – | completed; fitted on n=5..10 (rejected); resource bound (`budget`) hit from n=12 |
| MIN5 | 2.01^n (rms 0.01) | undecided: n^6.7 (rms 0.43) or 2.12^n (rms 0.39) | n^8.22 (R² 0.998) / 2.00^n (R² 1.000); last local exponents 6.2, 7.6, 9.0; last per-step factors 2.00, 2.00, 2.00 | – | timeout (>20 s) at n=16 |
| FULL | flat | below 50 ms throughout | – | – | completed |
| FULL-absmodel | 2.01^n (rms 0.01) | too small a range (2.8x); n^8.6 fits (rms 0.07) | n^8.22 (R² 0.998) / 2.00^n (R² 1.000); last local exponents 6.2, 7.6, 9.0; last per-step factors 2.00, 2.00, 2.00 | – | timeout (>20 s) at n=16 |

Leave-one-out configurations (same counter):

| n | FULL-absmodel count | FULL-absmodel ms |
|---:|---:|---:|
| 5 | 93 | 13.9 |
| 6 | 189 | 16.6 |
| 8 | 765 | 75.4 |
| 10 | 3,069 | 431 |
| 12 | 12,285 | 1,725 |
| 14 | 49,149 | 7,937 |
| 16 | timeout | >20 s |

### div-trunc-depth

Ill-typed: div_trunc with b = 2; the size is the depth bound HYLO_TC_MAXDEPTH = d. Intended verdict: rejected. Primary counter: `summon.matches`. Environment: `HYLO_TC_MAXDEPTH=n`.

| n | base count | base ms | FIX count | FIX ms | MIN5 count | MIN5 ms | FULL count | FULL ms |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 5 | 3,405 | 129 | 3,405 | 95.0 | 185 | 16.6 | 185 | 15.4 |
| 6 | 6,957 | 108 | 6,957 | 135 | 377 | 19.1 | 377 | 16.2 |
| 8 | 28,269 | 560 | 28,269 | 510 | 1,529 | 90.0 | 1,529 | 67.9 |
| 10 | 113,517 | 2,556 | 113,517 | 3,576 | 6,137 | 228 | 6,137 | 373 |
| 12 | 454,509 | 11,472 | 302,957 [B] | 7,634 | 24,569 | 1,128 | 24,569 | 1,985 |
| 14 | not run |  | 302,957 [B] | 7,944 | 98,297 | 5,660 | 98,297 | 6,874 |
| 16 | not run |  | 302,957 [B] | 7,453 | timeout | >20 s | 262,137 [B] | 13,304 |
| 20 | not run |  | 302,957 [B] | 6,904 | not run |  | 262,137 [B] | 17,736 |
| 24 | not run |  | 302,957 [B] | 7,038 | not run |  | 262,137 [B] | 17,945 |
| 32 | not run |  | 302,957 [B] | 6,719 | not run |  | 262,137 [B] | 14,815 |
| 40 | not run |  | 302,957 [B] | 7,182 | not run |  | 262,137 [B] | 13,868 |

| Configuration | Counter growth | Time growth | Counter: log-log fit / semi-log fit (upper half of the sizes), local exponents, per-step factors | Fastest other counter | Ends with |
|---|---|---|---|---|---|
| base | 2.01^n (rms 0.01) | undecided: n^8.4 (rms 0.15) or 2.35^n (rms 0.20) | n^6.83 (R² 0.997) / 2.00^n (R² 1.000); last local exponents 4.9, 6.2, 7.6; last per-step factors 2.02, 2.00, 2.00 | – | stopped before n=14: predicted timeout: 11 s at n=12, power-law extrapolation gives 41 s at n=14 |
| FIX | 2.02^n (rms 0.01) | 2.81^n (rms 0.01) | n^5.44 (R² 0.995) / 2.01^n (R² 1.000); last local exponents 3.9, 4.9, 6.2; last per-step factors 2.04, 2.02, 2.00 | – | completed; fitted on n=5..10 (rejected); resource bound (`budget`) hit from n=12 |
| MIN5 | 2.01^n (rms 0.01) | undecided: n^8.2 (rms 0.23) or 2.11^n (rms 0.16) | n^8.22 (R² 0.998) / 2.00^n (R² 1.000); last local exponents 6.2, 7.6, 9.0; last per-step factors 2.00, 2.00, 2.00 | – | timeout (>20 s) at n=16 |
| FULL | 2.01^n (rms 0.01) | too small a range (2.8x); n^8.8 fits (rms 0.06) | n^8.22 (R² 0.998) / 2.00^n (R² 1.000); last local exponents 6.2, 7.6, 9.0; last per-step factors 2.00, 2.00, 2.00 | – | completed; fitted on n=5..14 (rejected); resource bound (`budget`) hit from n=16 |

### div-valid

Valid: two growing givens; Xi is P holds through S1^d<Xi> is P (a derivation of depth d). Intended verdict: accepted. Primary counter: `summon.matches`.

| n | base count | base ms | FIX count | FIX ms | MIN5 count | MIN5 ms | FULL count | FULL ms |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 220 | 38.5 | 220 | 7.8 | 10 | 0.8 | 10 | 1.9 |
| 2 | 512 | 21.9 | 512 | 10.5 | 22 | 1.1 | 22 | 2.2 |
| 3 | 1,096 | 54.7 | 1,096 | 17.6 | 46 | 1.6 | 46 | 6.2 |
| 4 | 2,264 | 40.7 | 2,264 | 41.2 | 94 | 3.0 | 94 | 5.2 |
| 5 | 4,600 | 118 | 4,600 | 139 | 190 | 6.0 | 190 | 13.5 |
| 6 | 9,272 | 194 | 9,272 | 129 | 382 | 10.1 | 382 | 20.0 |
| 7 | 18,616 | 413 | 18,616 | 398 | 766 | 17.8 | 766 | 25.8 |
| 8 | 37,304 | 601 | 37,304 | 622 | 1,534 | 54.3 | 1,534 | 82.8 |

| Configuration | Counter growth | Time growth | Counter: log-log fit / semi-log fit (upper half of the sizes), local exponents, per-step factors | Fastest other counter | Ends with |
|---|---|---|---|---|---|
| base | 2.04^n for n ≥ 2 (rms 0.02) | undecided: n^4.2 (rms 0.25) or 1.90^n (rms 0.25) | n^4.44 (R² 0.995) / 2.01^n (R² 1.000); last local exponents 3.8, 4.5, 5.2; last per-step factors 2.02, 2.01, 2.00 | – | completed |
| FIX | 2.04^n for n ≥ 2 (rms 0.02) | undecided: n^4.1 (rms 0.21) or 2.05^n (rms 0.24) | n^4.44 (R² 0.995) / 2.01^n (R² 1.000); last local exponents 3.8, 4.5, 5.2; last per-step factors 2.02, 2.01, 2.00 | – | completed |
| MIN5 | 2.03^n for n ≥ 2 (rms 0.01) | undecided: n^4.3 (rms 0.18) or 2.10^n (rms 0.11) | n^4.43 (R² 0.995) / 2.01^n (R² 1.000); last local exponents 3.8, 4.5, 5.2; last per-step factors 2.01, 2.01, 2.00 | – | completed |
| FULL | 2.03^n for n ≥ 2 (rms 0.01) | undecided: n^3.5 (rms 0.29) or 1.83^n (rms 0.26) | n^4.43 (R² 0.995) / 2.01^n (R² 1.000); last local exponents 3.8, 4.5, 5.2; last per-step factors 2.01, 2.01, 2.00 | – | completed |

### div-valid-deep

Valid: two growing givens; Xi is P holds through S1^d<Xi> is P (a derivation of depth d). Intended verdict: accepted. Primary counter: `summon.matches`. Environment: `HYLO_TC_MAXDEPTH=1000`.

| n | base count | base ms | FIX count | FIX ms | MIN5 count | MIN5 ms | FULL count | FULL ms |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2 | 512 | 59.1 | 512 | 21.4 | 22 | 1.4 | 22 | 2.8 |
| 4 | 2,264 | 87.3 | 2,264 | 55.1 | 94 | 3.8 | 94 | 5.7 |
| 6 | 9,272 | 319 | 9,272 | 203 | 382 | 16.3 | 382 | 15.3 |
| 8 | 37,304 | 983 | 37,304 | 764 | 1,534 | 51.8 | 1,534 | 65.5 |
| 10 | 149,432 | 3,730 | 149,432 | 2,525 | 6,142 | 228 | 6,142 | 437 |
| 12 | 597,944 | 13,388 | 298,863 ✗ [B] | 5,857 | 24,574 | 1,435 | 24,574 | 1,521 |
| 14 | timeout | >20 s | 298,863 ✗ [B] | 6,004 | 98,302 | 6,524 | 98,302 | 7,854 |
| 16 | not run |  | 298,863 ✗ [B] | 5,595 | timeout | >20 s | 393,211 ✗ [B] | 30,469 |
| 20 | not run |  | 298,863 ✗ [B] | 5,551 | not run |  | not run |  |

| Configuration | Counter growth | Time growth | Counter: log-log fit / semi-log fit (upper half of the sizes), local exponents, per-step factors | Fastest other counter | Ends with |
|---|---|---|---|---|---|
| base | 2.02^n (rms 0.03) | undecided: n^5.7 (rms 0.13) or 1.96^n (rms 0.09) | n^6.82 (R² 0.997) / 2.00^n (R² 1.000); last local exponents 4.8, 6.2, 7.6; last per-step factors 2.01, 2.00, 2.00 | – | timeout (>20 s) at n=14 |
| FIX | 2.03^n (rms 0.03) | undecided: n^4.8 (rms 0.08) or 1.93^n (rms 0.05) | n^5.41 (R² 0.995) / 2.00^n (R² 1.000); last local exponents 3.5, 4.8, 6.2; last per-step factors 2.02, 2.01, 2.00 | – | completed; fitted on n=2..10 (accepted); resource bound (`budget`) hit from n=12; verdict differs from the intended one at n=12..20 |
| MIN5 | 2.01^n (rms 0.02) | 2.16^n (rms 0.13) | n^7.40 (R² 0.993) / 2.00^n (R² 1.000); last local exponents 6.2, 7.6, 9.0; last per-step factors 2.00, 2.00, 2.00 | – | timeout (>20 s) at n=16 |
| FULL | 2.01^n (rms 0.02) | 2.21^n (rms 0.12) | n^7.40 (R² 0.993) / 2.00^n (R² 1.000); last local exponents 6.2, 7.6, 9.0; last per-step factors 2.00, 2.00, 2.00 | – | stopped before n=20: predicted timeout: 30 s at n=16, power-law extrapolation gives 294 s at n=20; fitted on n=2..14 (accepted); resource bound (`budget`) hit from n=16; verdict differs from the intended one at n=16 |

### cyc-ring

Ill-typed: a ring of n givens A{i+1} is P => A{i} is P with no base case. Intended verdict: rejected. Primary counter: `summon.matches`.

| n | base count | base ms | FIX count | FIX ms | MIN5 count | MIN5 ms | FULL count | FULL ms |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2 | 1,369 | 28.7 | 1,369 | 24.9 | 39 | 1.4 | 1 | 2.1 |
| 3 | 1,388 | 23.4 | 1,388 | 14.4 | 58 | 1.3 | 1 | 3.7 |
| 4 | 1,407 | 23.4 | 1,407 | 19.4 | 77 | 1.5 | 1 | 7.3 |
| 6 | 1,445 | 50.6 | 1,445 | 32.9 | 115 | 1.5 | 1 | 3.5 |
| 8 | 1,483 | 52.5 | 1,483 | 49.0 | 153 | 1.4 | 1 | 2.1 |
| 12 | 1,559 | 36.0 | 1,559 | 61.3 | 229 | 1.9 | 1 | 6.6 |
| 16 | 1,635 | 44.4 | 1,635 | 71.2 | 305 | 7.0 | 1 | 7.7 |
| 32 | 1,939 | 113 | 1,939 | 109 | 609 | 4.8 | 1 | 10.1 |
| 64 | 2,547 | 225 | 2,547 | 280 | 1,217 | 9.3 | 1 | 5.8 |

| Configuration | Counter growth | Time growth | Counter: log-log fit / semi-log fit (upper half of the sizes), local exponents, per-step factors | Fastest other counter | Ends with |
|---|---|---|---|---|---|
| base | 19n + 1,331 (exact) | undecided: n^1.9 (rms 0.20) or 1.03^n (rms 0.22) | n^0.26 (R² 0.960) / 1.01^n (R² 0.995); last local exponents 0.2, 0.2, 0.4; last per-step factors 1.01, 1.01, 1.01 | – | completed |
| FIX | 19n + 1,331 (exact) | undecided: n^1.1 (rms 0.11) or 1.03^n (rms 0.15) | n^0.26 (R² 0.960) / 1.01^n (R² 0.995); last local exponents 0.2, 0.2, 0.4; last per-step factors 1.01, 1.01, 1.01 | – | completed |
| MIN5 | 19n + 1 (exact) | below 50 ms throughout | n^1.00 (R² 1.000) / 1.04^n (R² 0.930); last local exponents 1.0, 1.0, 1.0; last per-step factors 1.07, 1.04, 1.02 | – | completed |
| FULL | flat | below 50 ms throughout | – | `solver.goalSteps`: 4n + 6 (exact) | completed |
| FULL-absmodel | 19n + 1 (exact) | below 50 ms throughout | n^1.00 (R² 1.000) / 1.04^n (R² 0.930); last local exponents 1.0, 1.0, 1.0; last per-step factors 1.07, 1.04, 1.02 | – | completed |

Leave-one-out configurations (same counter):

| n | FULL-absmodel count | FULL-absmodel ms |
|---:|---:|---:|
| 2 | 39 | 1.5 |
| 3 | 58 | 1.1 |
| 4 | 77 | 1.9 |
| 6 | 115 | 5.7 |
| 8 | 153 | 2.2 |
| 12 | 229 | 7.5 |
| 16 | 305 | 2.6 |
| 32 | 609 | 3.4 |
| 64 | 1,217 | 17.1 |

### cyc-clique

Ill-typed: n types, A{j} is P => A{i} is P for every i != j (branching n - 1), no base case. Intended verdict: rejected. Primary counter: `summon.matches`.

| n | base count | base ms | FIX count | FIX ms | MIN5 count | MIN5 ms | FULL count | FULL ms |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2 | 1,369 | 43.7 | 1,369 | 26.6 | 39 | 5.1 | 1 | 6.7 |
| 3 | 116,585 | 2,789 | 116,585 | 2,082 | 9,205 | 63.6 | 1 | 7.8 |
| 4 | not run |  | not run |  | 472,381 | 3,975 | 1 | 3.3 |
| 5 | not run |  | not run |  | not run |  | 1 | 4.3 |
| 6 | not run |  | not run |  | not run |  | 1 | 10.1 |
| 8 | not run |  | not run |  | not run |  | 1 | 7.0 |
| 12 | not run |  | not run |  | not run |  | 1 | 11.9 |
| 16 | not run |  | not run |  | not run |  | 1 | 30.9 |

| Configuration | Counter growth | Time growth | Counter: log-log fit / semi-log fit (upper half of the sizes), local exponents, per-step factors | Fastest other counter | Ends with |
|---|---|---|---|---|---|
| base | too few points (2) | too few points (2) | n^10.96 (R² 1.000) / 85.16^n (R² 1.000); last local exponents 11.0; last per-step factors 85.16 | – | stopped before n=4: predicted timeout: 3 s at n=3, power-law extrapolation gives 53 s at n=4 |
| FIX | too few points (2) | too few points (2) | n^10.96 (R² 1.000) / 85.16^n (R² 1.000); last local exponents 11.0; last per-step factors 85.16 | – | stopped before n=4: predicted timeout: 2 s at n=3, power-law extrapolation gives 46 s at n=4 |
| MIN5 | too few points (3) | too few points (3) | n^13.56 (R² 1.000) / 110.06^n (R² 0.991); last local exponents 13.5, 13.7; last per-step factors 236.03, 51.32 | – | stopped before n=5: predicted timeout: 4 s at n=4, power-law extrapolation gives 98 s at n=5 |
| FULL | flat | below 50 ms throughout | – | `solver.goalSteps`: 4n^2 − 4n + 6 (exact) | completed |
| FULL-absmodel | too few points (2) | too few points (2) | n^13.48 (R² 1.000) / 236.03^n (R² 1.000); last local exponents 13.5; last per-step factors 236.03 | – | stopped before n=5: predicted timeout: 3 s at n=4, power-law extrapolation gives 51 s at n=5; fitted on n=2..3 (rejected); resource bound (`budget`) hit from n=4 |

Leave-one-out configurations (same counter):

| n | FULL-absmodel count | FULL-absmodel ms |
|---:|---:|---:|
| 2 | 39 | 1.2 |
| 3 | 9,205 | 81.7 |
| 4 | 236,185 [B] | 3,052 |

### members-ext

Valid: n extensions over n/10 types, 20 member lookups. Intended verdict: accepted. Primary counter: `names.appliesCalls`.

| n | base count | base ms | FIX count | FIX ms | MIN5 count | MIN5 ms | FULL count | FULL ms |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 20 | 960 | 146 | 20 | 42.5 | 20 | 11.0 | 20 | 4.3 |
| 40 | 1,760 | 166 | 20 | 13.2 | 20 | 3.3 | 20 | 7.4 |
| 80 | 3,360 | 262 | 20 | 55.5 | 20 | 13.8 | 20 | 6.4 |
| 160 | 6,560 | 185 | 20 | 69.8 | 20 | 17.0 | 20 | 13.6 |
| 320 | 12,960 | 241 | 20 | 107 | 20 | 22.0 | 20 | 19.6 |
| 640 | 25,760 | 356 | 20 | 85.2 | 20 | 68.4 | 20 | 41.1 |
| 1280 | 51,360 | 423 | 20 | 129 | 20 | 52.8 | 20 | 73.0 |

| Configuration | Counter growth | Time growth | Counter: log-log fit / semi-log fit (upper half of the sizes), local exponents, per-step factors | Fastest other counter | Ends with |
|---|---|---|---|---|---|
| base | 40n + 160 (exact) | n^0.52 (rms 0.15) | n^0.99 (R² 1.000) / 1.00^n (R² 0.922); last local exponents 1.0, 1.0, 1.0; last per-step factors 1.00, 1.00, 1.00 | – | completed |
| FIX | flat | undecided: n^0.6 (rms 0.44) or 1.01^n (rms 1.13) | – | – | completed |
| MIN5 | flat | n^0.63 for n ≥ 80 (rms 0.28) | – | – | completed |
| FULL | flat | n^0.86 for n ≥ 80 (rms 0.08) | – | – | completed |

### members-use

Valid: 100 extensions over 10 types, m member lookups. Intended verdict: accepted. Primary counter: `names.appliesCalls`.

| n | base count | base ms | FIX count | FIX ms | MIN5 count | MIN5 ms | FULL count | FULL ms |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 10 | 2,080 | 171 | 10 | 50.9 | 10 | 8.4 | 10 | 4.9 |
| 20 | 4,160 | 235 | 20 | 25.2 | 20 | 14.3 | 20 | 5.0 |
| 40 | 8,320 | 400 | 40 | 47.4 | 40 | 6.9 | 40 | 10.7 |
| 80 | 16,640 | 248 | 80 | 101 | 80 | 18.8 | 80 | 11.8 |
| 160 | 33,280 | 915 | 160 | 104 | 160 | 40.0 | 160 | 40.9 |
| 320 | 66,560 | 1,584 | 320 | 77.5 | 320 | 74.6 | 320 | 29.7 |
| 640 | 133,120 | 3,459 | 640 | 263 | 640 | 88.9 | 640 | 77.8 |

| Configuration | Counter growth | Time growth | Counter: log-log fit / semi-log fit (upper half of the sizes), local exponents, per-step factors | Fastest other counter | Ends with |
|---|---|---|---|---|---|
| base | 208n (exact) | n^1.35 (rms 0.28) | n^1.00 (R² 1.000) / 1.00^n (R² 0.920); last local exponents 1.0, 1.0, 1.0; last per-step factors 1.01, 1.00, 1.00 | – | completed |
| FIX | n (exact) | undecided: n^8.9 (rms 0.32) or 1.01^n (rms 0.32) | n^1.00 (R² 1.000) / 1.00^n (R² 0.920); last local exponents 1.0, 1.0, 1.0; last per-step factors 1.01, 1.00, 1.00 | – | completed |
| MIN5 | n (exact) | n^0.93 for n ≥ 40 (rms 0.23) | n^1.00 (R² 1.000) / 1.00^n (R² 0.920); last local exponents 1.0, 1.0, 1.0; last per-step factors 1.01, 1.00, 1.00 | – | completed |
| FULL | n (exact) | n^0.83 (rms 0.29) | n^1.00 (R² 1.000) / 1.00^n (R² 0.920); last local exponents 1.0, 1.0, 1.0; last per-step factors 1.01, 1.00, 1.00 | – | completed |

### members-both

Valid: n extensions over n/10 types and n member lookups. Intended verdict: accepted. Primary counter: `names.appliesCalls`.

| n | base count | base ms | FIX count | FIX ms | MIN5 count | MIN5 ms | FULL count | FULL ms |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 20 | 960 | 119 | 20 | 32.8 | 20 | 2.8 | 20 | 3.9 |
| 40 | 3,520 | 193 | 40 | 32.3 | 40 | 13.8 | 40 | 20.2 |
| 80 | 13,440 | 495 | 80 | 48.8 | 80 | 10.9 | 80 | 19.8 |
| 160 | 52,480 | 882 | 160 | 99.3 | 160 | 54.9 | 160 | 31.8 |
| 320 | 207,360 | 2,917 | 320 | 278 | 320 | 164 | 320 | 50.3 |
| 640 | 824,320 | 7,004 | 640 | 547 | 640 | 423 | 640 | 139 |

| Configuration | Counter growth | Time growth | Counter: log-log fit / semi-log fit (upper half of the sizes), local exponents, per-step factors | Fastest other counter | Ends with |
|---|---|---|---|---|---|
| base | 2n^2 + 8n (exact) | n^1.42 (rms 0.10) | n^1.99 (R² 1.000) / 1.01^n (R² 0.965); last local exponents 2.0, 2.0, 2.0; last per-step factors 1.02, 1.01, 1.00 | – | completed |
| FIX | n (exact) | n^1.49 (rms 0.11) | n^1.00 (R² 1.000) / 1.00^n (R² 0.964); last local exponents 1.0, 1.0, 1.0; last per-step factors 1.01, 1.00, 1.00 | – | completed |
| MIN5 | n (exact) | n^1.98 for n ≥ 40 (rms 0.32) | n^1.00 (R² 1.000) / 1.00^n (R² 0.964); last local exponents 1.0, 1.0, 1.0; last per-step factors 1.01, 1.00, 1.00 | – | completed |
| FULL | n (exact) | n^1.77 for n ≥ 40 (rms 0.07) | n^1.00 (R² 1.000) / 1.00^n (R² 0.964); last local exponents 1.0, 1.0, 1.0; last per-step factors 1.01, 1.00, 1.00 | – | completed |

### condext

Valid: n conditional extensions of Box<T> (each needs T is P{i}), 8 member lookups. Intended verdict: accepted. Primary counter: `names.appliesCalls`.

| n | base count | base ms | FIX count | FIX ms | MIN5 count | MIN5 ms | FULL count | FULL ms |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2 | 96 | 87.7 | 8 | 12.4 | 8 | 3.0 | 8 | 7.9 |
| 4 | 128 | 47.8 | 8 | 40.4 | 8 | 7.5 | 8 | 7.6 |
| 8 | 192 | 68.2 | 8 | 20.6 | 8 | 8.8 | 8 | 8.1 |
| 16 | 320 | 87.0 | 8 | 64.9 | 8 | 9.0 | 8 | 17.2 |
| 32 | 576 | 265 | 8 | 112 | 8 | 23.4 | 8 | 15.7 |
| 64 | 1,088 | 903 | 8 | 216 | 8 | 17.5 | 8 | 31.4 |
| 128 | 2,112 | 4,258 | 8 | 537 | 8 | 23.8 | 8 | 39.6 |

| Configuration | Counter growth | Time growth | Counter: log-log fit / semi-log fit (upper half of the sizes), local exponents, per-step factors | Fastest other counter | Ends with |
|---|---|---|---|---|---|
| base | 16n + 64 (exact) | n^2.18 for n ≥ 4 (rms 0.08) | n^0.91 (R² 0.999) / 1.02^n (R² 0.933); last local exponents 0.8, 0.9, 1.0; last per-step factors 1.04, 1.02, 1.01 | `summon.matches`: n^2 + 105n + 2,444 (exact) | completed |
| FIX | flat | n^1.11 for n ≥ 8 (rms 0.13) | – | `solver.goalSteps`: 6n + 104 (exact) | completed |
| MIN5 | flat | below 50 ms throughout | – | `memberskip.settled`: 16n + 24 (exact) | completed |
| FULL | flat | below 50 ms throughout | – | `absmodel.facts`: n + 63 (exact) | completed |

### ovl-calls

Valid: one expression with k calls, each choosing among 4 overloads by argument type. Intended verdict: accepted. Primary counter: `solver.forks`.

| n | base count | base ms | FIX count | FIX ms | MIN5 count | MIN5 ms | FULL count | FULL ms |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 4 | 40.0 | 4 | 25.3 | 4 | 4.9 | 4 | 6.4 |
| 2 | 8 | 80.3 | 8 | 9.7 | 8 | 1.0 | 8 | 2.1 |
| 3 | 16 | 35.1 | 16 | 30.7 | 16 | 5.6 | 16 | 6.6 |
| 4 | 44 | 66.3 | 44 | 43.2 | 44 | 6.9 | 44 | 7.9 |
| 5 | 144 | 200 | 144 | 54.5 | 144 | 15.1 | 144 | 22.1 |
| 6 | 448 | 731 | 448 | 72.9 | 448 | 70.5 | 448 | 71.2 |
| 7 | 1,248 | 2,243 | 1,248 | 213 | 1,248 | 124 | 1,248 | 145 |
| 8 | 3,184 | 5,410 | 3,184 | 437 | 3,184 | 371 | 3,184 | 430 |
| 9 | 7,316 | 13,063 | 7,316 | 964 | 7,316 | 673 | 7,316 | 878 |
| 10 | timeout | >20 s | 15,396 | 1,686 | 15,396 | 1,780 | 15,396 | 1,569 |
| 12 | not run |  | 59,820 | 7,026 | 59,820 | 7,093 | 59,820 | 6,367 |
| 14 | not run |  | timeout | >20 s | 246,632 | 19,059 | 246,632 | 17,915 |
| 16 | not run |  | not run |  | not run |  | 1,190,192 | 112,532 |

| Configuration | Counter growth | Time growth | Counter: log-log fit / semi-log fit (upper half of the sizes), local exponents, per-step factors | Fastest other counter | Ends with |
|---|---|---|---|---|---|
| base | undecided: n^6.5 (rms 0.09) or 2.83^n (rms 0.12) | undecided: n^7.7 (rms 0.25) or 3.26^n (rms 0.34) | n^6.69 (R² 0.999) / 2.67^n (R² 0.996); last local exponents 6.6, 7.0, 7.1; last per-step factors 2.79, 2.55, 2.30 | – | timeout (>20 s) at n=10 |
| FIX | undecided: n^6.9 (rms 0.05) or 2.54^n (rms 0.30) | undecided: n^7.0 (rms 0.11) or 2.16^n (rms 0.15) | n^7.06 (R² 1.000) / 2.25^n (R² 0.992); last local exponents 7.1, 7.1, 7.4; last per-step factors 2.30, 2.10, 1.97 | `summon.matches`: 2.07^n for n ≥ 3 (rms 0.05) | timeout (>20 s) at n=14 |
| MIN5 | undecided: n^7.2 (rms 0.12) or 2.41^n (rms 0.39) | undecided: n^7.1 (rms 0.15) or 2.22^n (rms 0.36) | n^7.54 (R² 0.997) / 2.10^n (R² 0.997); last local exponents 7.1, 7.4, 9.2; last per-step factors 2.10, 1.97, 2.03 | `summon.matches`: 2.20^n (rms 0.13) | stopped before n=16: predicted timeout: 19 s at n=14, power-law extrapolation gives 45 s at n=16 |
| FULL | undecided: n^7.8 (rms 0.22) or 2.29^n (rms 0.36) | undecided: n^7.3 (rms 0.25) or 2.14^n (rms 0.32) | n^8.10 (R² 0.991) / 2.10^n (R² 0.998); last local exponents 7.4, 9.2, 11.8; last per-step factors 1.97, 2.03, 2.20 | – | stopped before n=20: predicted timeout: 113 s at n=16, power-law extrapolation gives 2426 s at n=20 |

### ovl-width

Valid: one expression with 4 calls, each choosing among m overloads by argument type. Intended verdict: accepted. Primary counter: `solver.forks`.

| n | base count | base ms | FIX count | FIX ms | MIN5 count | MIN5 ms | FULL count | FULL ms |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2 | 14 | 69.6 | 14 | 23.5 | 14 | 2.3 | 14 | 6.8 |
| 3 | 30 | 55.9 | 30 | 15.2 | 30 | 3.6 | 30 | 3.9 |
| 4 | 44 | 207 | 44 | 19.2 | 44 | 7.9 | 44 | 10.8 |
| 6 | 78 | 216 | 78 | 24.6 | 78 | 11.2 | 78 | 10.6 |
| 8 | 120 | 372 | 120 | 35.0 | 120 | 23.5 | 120 | 24.6 |
| 12 | 228 | 433 | 228 | 38.3 | 228 | 19.1 | 228 | 25.5 |
| 16 | 368 | 1,127 | 368 | 59.3 | 368 | 23.6 | 368 | 31.7 |

| Configuration | Counter growth | Time growth | Counter: log-log fit / semi-log fit (upper half of the sizes), local exponents, per-step factors | Fastest other counter | Ends with |
|---|---|---|---|---|---|
| base | n^2 + 7n (exact, n ≥ 3) | undecided: n^3.3 (rms 0.16) or 1.28^n (rms 0.14) | n^1.58 (R² 1.000) / 1.17^n (R² 0.988); last local exponents 1.5, 1.6, 1.7; last per-step factors 1.24, 1.17, 1.13 | – | completed |
| FIX | n^2 + 7n (exact, n ≥ 3) | undecided: n^0.9 (rms 0.08) or 1.10^n (rms 0.11) | n^1.58 (R² 1.000) / 1.17^n (R² 0.988); last local exponents 1.5, 1.6, 1.7; last per-step factors 1.24, 1.17, 1.13 | – | completed |
| MIN5 | n^2 + 7n (exact, n ≥ 3) | below 50 ms throughout | n^1.58 (R² 1.000) / 1.17^n (R² 0.988); last local exponents 1.5, 1.6, 1.7; last per-step factors 1.24, 1.17, 1.13 | – | completed |
| FULL | n^2 + 7n (exact, n ≥ 3) | below 50 ms throughout | n^1.58 (R² 1.000) / 1.17^n (R² 0.988); last local exponents 1.5, 1.6, 1.7; last per-step factors 1.24, 1.17, 1.13 | – | completed |

### ovl-stmts

Valid: k separate statements, each one call choosing among 4 overloads. Intended verdict: accepted. Primary counter: `solver.forks`.

| n | base count | base ms | FIX count | FIX ms | MIN5 count | MIN5 ms | FULL count | FULL ms |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 4 | 43.2 | 4 | 15.4 | 4 | 0.9 | 4 | 9.8 |
| 2 | 8 | 82.6 | 8 | 21.1 | 8 | 1.4 | 8 | 10.8 |
| 4 | 16 | 108 | 16 | 21.0 | 16 | 6.0 | 16 | 12.4 |
| 8 | 32 | 171 | 32 | 39.9 | 32 | 6.7 | 32 | 7.7 |
| 16 | 64 | 213 | 64 | 29.9 | 64 | 12.1 | 64 | 13.6 |
| 32 | 128 | 393 | 128 | 40.6 | 128 | 16.5 | 128 | 30.4 |
| 64 | 256 | 652 | 256 | 57.6 | 256 | 31.0 | 256 | 25.1 |

| Configuration | Counter growth | Time growth | Counter: log-log fit / semi-log fit (upper half of the sizes), local exponents, per-step factors | Fastest other counter | Ends with |
|---|---|---|---|---|---|
| base | 4n (exact) | n^0.62 (rms 0.10) | n^1.00 (R² 1.000) / 1.04^n (R² 0.920); last local exponents 1.0, 1.0, 1.0; last per-step factors 1.09, 1.04, 1.02 | – | completed |
| FIX | 4n (exact) | undecided: n^0.3 (rms 0.16) or 1.02^n (rms 0.25) | n^1.00 (R² 1.000) / 1.04^n (R² 0.920); last local exponents 1.0, 1.0, 1.0; last per-step factors 1.09, 1.04, 1.02 | – | completed |
| MIN5 | 4n (exact) | below 50 ms throughout | n^1.00 (R² 1.000) / 1.04^n (R² 0.920); last local exponents 1.0, 1.0, 1.0; last per-step factors 1.09, 1.04, 1.02 | – | completed |
| FULL | 4n (exact) | below 50 ms throughout | n^1.00 (R² 1.000) / 1.04^n (R² 0.920); last local exponents 1.0, 1.0, 1.0; last per-step factors 1.09, 1.04, 1.02 | – | completed |

### ovr-args

Valid: g(h(), ..., h()) with n arguments; h has 3 overloads differing in return type only. Intended verdict: accepted. Primary counter: `solver.forks`.

| n | base count | base ms | FIX count | FIX ms | MIN5 count | MIN5 ms | FULL count | FULL ms |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 3 | 56.6 | 3 | 12.7 | 3 | 5.2 | 3 | 10.8 |
| 2 | 12 | 57.4 | 12 | 22.6 | 12 | 1.1 | 12 | 5.5 |
| 3 | 39 | 71.8 | 39 | 27.0 | 39 | 5.7 | 39 | 2.5 |
| 4 | 120 | 68.0 | 120 | 24.9 | 120 | 6.4 | 120 | 12.3 |
| 5 | 363 | 76.6 | 363 | 20.4 | 363 | 9.8 | 363 | 16.0 |
| 6 | 1,092 | 112 | 1,092 | 28.1 | 1,092 | 27.0 | 1,092 | 53.1 |
| 7 | 3,279 | 304 | 3,279 | 169 | 3,279 | 154 | 3,279 | 159 |
| 8 | 9,840 | 620 | 9,840 | 264 | 9,840 | 509 | 9,840 | 397 |
| 9 | 29,523 | 1,888 | 29,523 | 1,047 | 29,523 | 1,714 | 29,523 | 1,176 |
| 10 | 88,572 | 4,877 | 88,572 | 3,544 | 88,572 | 3,975 | 88,572 | 3,624 |
| 12 | timeout | >20 s | timeout | >20 s | timeout | >20 s | 797,160 | 34,237 |

| Configuration | Counter growth | Time growth | Counter: log-log fit / semi-log fit (upper half of the sizes), local exponents, per-step factors | Fastest other counter | Ends with |
|---|---|---|---|---|---|
| base | 3.03^n for n ≥ 2 (rms 0.03) | undecided: n^8.7 (rms 0.09) or 2.93^n (rms 0.09) | n^8.58 (R² 0.994) / 3.00^n (R² 1.000); last local exponents 8.2, 9.3, 10.4; last per-step factors 3.00, 3.00, 3.00 | – | timeout (>20 s) at n=12 |
| FIX | 3.03^n for n ≥ 2 (rms 0.03) | undecided: n^10.5 (rms 0.25) or 3.72^n (rms 0.28) | n^8.58 (R² 0.994) / 3.00^n (R² 1.000); last local exponents 8.2, 9.3, 10.4; last per-step factors 3.00, 3.00, 3.00 | – | timeout (>20 s) at n=12 |
| MIN5 | 3.03^n for n ≥ 2 (rms 0.03) | undecided: n^8.7 (rms 0.57) or 3.24^n (rms 0.42) | n^8.58 (R² 0.994) / 3.00^n (R² 1.000); last local exponents 8.2, 9.3, 10.4; last per-step factors 3.00, 3.00, 3.00 | – | timeout (>20 s) at n=12 |
| FULL | 3.02^n for n ≥ 2 (rms 0.03) | 2.85^n for n ≥ 3 (rms 0.22) | n^9.46 (R² 0.988) / 3.00^n (R² 1.000); last local exponents 9.3, 10.4, 12.1; last per-step factors 3.00, 3.00, 3.00 | – | completed |

### ovr-width

Valid: g(h(), h(), h(), h()); h has m overloads differing in return type only. Intended verdict: accepted. Primary counter: `solver.forks`.

| n | base count | base ms | FIX count | FIX ms | MIN5 count | MIN5 ms | FULL count | FULL ms |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2 | 30 | 49.8 | 30 | 25.7 | 30 | 1.4 | 30 | 6.4 |
| 3 | 120 | 75.8 | 120 | 32.5 | 120 | 7.1 | 120 | 7.4 |
| 4 | 340 | 65.3 | 340 | 39.4 | 340 | 9.3 | 340 | 14.1 |
| 6 | 1,554 | 107 | 1,554 | 95.9 | 1,554 | 55.5 | 1,554 | 45.8 |
| 8 | 4,680 | 225 | 4,680 | 223 | 4,680 | 153 | 4,680 | 144 |
| 12 | 22,620 | 1,255 | 22,620 | 679 | 22,620 | 770 | 22,620 | 660 |
| 16 | 69,904 | 3,057 | 69,904 | 2,302 | 69,904 | 2,291 | 69,904 | 2,297 |

| Configuration | Counter growth | Time growth | Counter: log-log fit / semi-log fit (upper half of the sizes), local exponents, per-step factors | Fastest other counter | Ends with |
|---|---|---|---|---|---|
| base | n^4 + n^3 + n^2 + n (exact) | n^4.31 for n ≥ 3 (rms 0.12) | n^3.88 (R² 1.000) / 1.46^n (R² 0.984); last local exponents 3.8, 3.9, 3.9; last per-step factors 1.74, 1.48, 1.33 | – | completed |
| FIX | n^4 + n^3 + n^2 + n (exact) | undecided: n^3.5 (rms 0.08) or 1.39^n (rms 0.12) | n^3.88 (R² 1.000) / 1.46^n (R² 0.984); last local exponents 3.8, 3.9, 3.9; last per-step factors 1.74, 1.48, 1.33 | – | completed |
| MIN5 | n^4 + n^3 + n^2 + n (exact) | n^3.94 for n ≥ 4 (rms 0.06) | n^3.88 (R² 1.000) / 1.46^n (R² 0.984); last local exponents 3.8, 3.9, 3.9; last per-step factors 1.74, 1.48, 1.33 | – | completed |
| FULL | n^4 + n^3 + n^2 + n (exact) | n^4.08 (rms 0.05) | n^3.88 (R² 1.000) / 1.46^n (R² 0.984); last local exponents 3.8, 3.9, 3.9; last per-step factors 1.74, 1.48, 1.33 | – | completed |

### nest

Valid: S<S<...<Z>>> is P at depth d through `T is P => S<T> is P`. Intended verdict: accepted. Primary counter: `summon.matches`.

| n | base count | base ms | FIX count | FIX ms | MIN5 count | MIN5 ms | FULL count | FULL ms |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 145 | 34.3 | 145 | 16.5 | 5 | 0.7 | 5 | 1.5 |
| 2 | 217 | 47.4 | 217 | 22.1 | 7 | 0.6 | 7 | 2.0 |
| 3 | 289 | 40.8 | 289 | 13.7 | 9 | 0.8 | 9 | 2.1 |
| 4 | 361 | 41.7 | 361 | 21.3 | 11 | 0.9 | 11 | 5.7 |
| 5 | 433 | 41.1 | 433 | 18.8 | 13 | 0.7 | 13 | 2.2 |
| 6 | 505 | 42.0 | 505 | 18.7 | 15 | 0.7 | 15 | 6.3 |
| 7 | 577 | 47.4 | 577 | 24.9 | 17 | 4.9 | 17 | 5.8 |
| 8 | 649 | 46.2 | 649 | 25.1 | 19 | 0.8 | 19 | 2.3 |

| Configuration | Counter growth | Time growth | Counter: log-log fit / semi-log fit (upper half of the sizes), local exponents, per-step factors | Fastest other counter | Ends with |
|---|---|---|---|---|---|
| base | 72n + 73 (exact) | below 50 ms throughout | n^0.86 (R² 1.000) / 1.14^n (R² 0.996); last local exponents 0.8, 0.9, 0.9; last per-step factors 1.17, 1.14, 1.12 | – | completed |
| FIX | 72n + 73 (exact) | below 50 ms throughout | n^0.86 (R² 1.000) / 1.14^n (R² 0.996); last local exponents 0.8, 0.9, 0.9; last per-step factors 1.17, 1.14, 1.12 | – | completed |
| MIN5 | 2n + 3 (exact) | below 50 ms throughout | n^0.81 (R² 1.000) / 1.13^n (R² 0.997); last local exponents 0.8, 0.8, 0.8; last per-step factors 1.15, 1.13, 1.12 | – | completed |
| FULL | 2n + 3 (exact) | below 50 ms throughout | n^0.81 (R² 1.000) / 1.13^n (R² 0.997); last local exponents 0.8, 0.8, 0.8; last per-step factors 1.15, 1.13, 1.12 | – | completed |

### nest-deep

Valid: S<S<...<Z>>> is P at depth d through `T is P => S<T> is P`. Intended verdict: accepted. Primary counter: `summon.matches`. Environment: `HYLO_TC_MAXDEPTH=1000`.

| n | base count | base ms | FIX count | FIX ms | MIN5 count | MIN5 ms | FULL count | FULL ms |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 4 | 361 | 76.5 | 361 | 16.7 | 11 | 0.8 | 11 | 5.8 |
| 8 | 649 | 43.0 | 649 | 18.0 | 19 | 1.8 | 19 | 6.4 |
| 16 | 1,225 | 61.7 | 1,225 | 31.3 | 35 | 1.5 | 35 | 4.0 |
| 32 | 2,377 | 67.6 | 2,377 | 79.6 | 67 | 2.7 | 67 | 9.3 |
| 64 | 4,681 | 107 | 4,681 | 158 | 131 | 8.1 | 131 | 18.3 |
| 128 | 9,289 | 240 | 9,289 | 177 | 259 | 24.0 | 259 | 26.6 |

| Configuration | Counter growth | Time growth | Counter: log-log fit / semi-log fit (upper half of the sizes), local exponents, per-step factors | Fastest other counter | Ends with |
|---|---|---|---|---|---|
| base | 72n + 73 (exact) | undecided: n^1.5 (rms 0.08) or 1.01^n (rms 0.08) | n^0.98 (R² 1.000) / 1.01^n (R² 0.965); last local exponents 1.0, 1.0, 1.0; last per-step factors 1.04, 1.02, 1.01 | – | completed |
| FIX | 72n + 73 (exact) | n^0.89 for n ≥ 8 (rms 0.20) | n^0.98 (R² 1.000) / 1.01^n (R² 0.965); last local exponents 1.0, 1.0, 1.0; last per-step factors 1.04, 1.02, 1.01 | – | completed |
| MIN5 | 2n + 3 (exact) | below 50 ms throughout | n^0.98 (R² 1.000) / 1.01^n (R² 0.966); last local exponents 0.9, 1.0, 1.0; last per-step factors 1.04, 1.02, 1.01 | – | completed |
| FULL | 2n + 3 (exact) | below 50 ms throughout | n^0.98 (R² 1.000) / 1.01^n (R² 0.966); last local exponents 0.9, 1.0, 1.0; last per-step factors 1.04, 1.02, 1.01 | – | completed |

### nest-neg

Ill-typed: like nest but the leaf Y is not P. Intended verdict: rejected. Primary counter: `summon.matches`. Environment: `HYLO_TC_MAXDEPTH=1000`.

| n | base count | base ms | FIX count | FIX ms | MIN5 count | MIN5 ms | FULL count | FULL ms |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 4 | 721 | 49.6 | 721 | 30.7 | 21 | 1.1 | 17 | 6.4 |
| 8 | 1,297 | 63.4 | 1,297 | 34.6 | 37 | 1.3 | 33 | 6.5 |
| 16 | 2,449 | 84.4 | 2,449 | 58.2 | 69 | 1.8 | 65 | 3.3 |
| 32 | 4,753 | 109 | 4,753 | 103 | 133 | 7.5 | 129 | 14.4 |
| 64 | 9,361 | 206 | 9,361 | 180 | 261 | 15.4 | 257 | 15.6 |
| 128 | 18,577 | 295 | 18,577 | 490 | 517 | 19.4 | 513 | 32.2 |

| Configuration | Counter growth | Time growth | Counter: log-log fit / semi-log fit (upper half of the sizes), local exponents, per-step factors | Fastest other counter | Ends with |
|---|---|---|---|---|---|
| base | 144n + 145 (exact) | n^0.83 (rms 0.06) | n^0.98 (R² 1.000) / 1.01^n (R² 0.965); last local exponents 1.0, 1.0, 1.0; last per-step factors 1.04, 1.02, 1.01 | – | completed |
| FIX | 144n + 145 (exact) | n^1.30 (rms 0.07) | n^0.98 (R² 1.000) / 1.01^n (R² 0.965); last local exponents 1.0, 1.0, 1.0; last per-step factors 1.04, 1.02, 1.01 | – | completed |
| MIN5 | 4n + 5 (exact) | below 50 ms throughout | n^0.98 (R² 1.000) / 1.01^n (R² 0.966); last local exponents 0.9, 1.0, 1.0; last per-step factors 1.04, 1.02, 1.01 | – | completed |
| FULL | 4n + 1 (exact) | below 50 ms throughout | n^1.00 (R² 1.000) / 1.01^n (R² 0.965); last local exponents 1.0, 1.0, 1.0; last per-step factors 1.04, 1.02, 1.01 | – | completed |
| FULL-absmodel | 4n + 5 (exact) | below 50 ms throughout | n^0.98 (R² 1.000) / 1.01^n (R² 0.966); last local exponents 0.9, 1.0, 1.0; last per-step factors 1.04, 1.02, 1.01 | – | completed |

Leave-one-out configurations (same counter):

| n | FULL-absmodel count | FULL-absmodel ms |
|---:|---:|---:|
| 4 | 21 | 1.1 |
| 8 | 37 | 1.9 |
| 16 | 69 | 2.3 |
| 32 | 133 | 7.0 |
| 64 | 261 | 9.4 |
| 128 | 517 | 22.1 |

### nest-diamond

Valid: S<T> is P and S<T> is Q each need T is P and T is Q (2^d subgoals without sharing). Intended verdict: accepted. Primary counter: `summon.matches`. Environment: `HYLO_TC_MAXDEPTH=1000`.

| n | base count | base ms | FIX count | FIX ms | MIN5 count | MIN5 ms | FULL count | FULL ms |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 224 | 56.7 | 224 | 8.3 | 8 | 0.8 | 8 | 6.6 |
| 2 | 524 | 55.7 | 524 | 12.3 | 20 | 0.8 | 20 | 6.4 |
| 3 | 1,128 | 68.2 | 1,128 | 48.1 | 48 | 1.2 | 48 | 7.0 |
| 4 | 2,344 | 119 | 2,344 | 81.4 | 112 | 2.0 | 112 | 8.0 |
| 5 | 4,792 | 184 | 4,792 | 184 | 256 | 9.8 | 256 | 14.6 |
| 6 | 9,720 | 501 | 9,720 | 369 | 576 | 22.9 | 576 | 28.9 |
| 7 | 19,640 | 568 | 19,640 | 410 | 1,280 | 42.2 | 1,280 | 47.5 |
| 8 | 39,608 | 1,570 | 39,608 | 1,370 | 2,816 | 178 | 2,816 | 217 |
| 9 | 156,056 ✗(depth) | 3,644 | 156,056 ✗(depth) | 3,685 | 12,128 ✗(depth) | 167 | 12,128 ✗(depth) | 188 |
| 10 | 158,048 ✗(depth) | 5,012 | 158,048 ✗(depth) | 6,216 | 14,120 ✗(depth) | 451 | 14,120 ✗(depth) | 382 |
| 12 | 162,024 ✗(depth) | 5,420 | 162,024 ✗(depth) | 6,985 | 18,096 ✗(depth) | 437 | 18,096 ✗(depth) | 432 |
| 14 | 165,992 ✗(depth) | 6,712 | 165,992 ✗(depth) | 7,298 | 22,064 ✗(depth) | 466 | 22,064 ✗(depth) | 424 |
| 16 | 169,960 ✗(depth) | 7,008 | 169,960 ✗(depth) | 7,095 | 26,032 ✗(depth) | 543 | 26,032 ✗(depth) | 429 |
| 20 | 177,870 ✗(depth) | 6,917 | 177,870 ✗(depth) | 7,877 | 33,942 ✗(depth) | 832 | 33,942 ✗(depth) | 569 |

| Configuration | Counter growth | Time growth | Counter: log-log fit / semi-log fit (upper half of the sizes), local exponents, per-step factors | Fastest other counter | Ends with |
|---|---|---|---|---|---|
| base | 2.05^n for n ≥ 2 (rms 0.02) | undecided: n^4.6 (rms 0.15) or 2.12^n (rms 0.16) | n^4.48 (R² 0.995) / 2.02^n (R² 1.000); last local exponents 3.9, 4.6, 5.3; last per-step factors 2.03, 2.02, 2.02 | – | completed; fitted on n=1..8 (accepted); verdict differs from the intended one at n=9..20 |
| FIX | 2.05^n for n ≥ 2 (rms 0.02) | undecided: n^3.5 (rms 0.23) or 2.04^n (rms 0.26) | n^4.48 (R² 0.995) / 2.02^n (R² 1.000); last local exponents 3.9, 4.6, 5.3; last per-step factors 2.03, 2.02, 2.02 | – | completed; fitted on n=1..8 (accepted); verdict differs from the intended one at n=9..20 |
| MIN5 | 2.28^n for n ≥ 2 (rms 0.03) | undecided: n^6.4 (rms 0.21) or 3.03^n (rms 0.23) | n^5.09 (R² 0.996) / 2.22^n (R² 1.000); last local exponents 4.4, 5.2, 5.9; last per-step factors 2.25, 2.22, 2.20 | – | completed; fitted on n=1..8 (accepted); verdict differs from the intended one at n=9..20 |
| FULL | 2.28^n for n ≥ 2 (rms 0.03) | undecided: n^7.2 (rms 0.19) or 3.03^n (rms 0.15) | n^5.09 (R² 0.996) / 2.22^n (R² 1.000); last local exponents 4.4, 5.2, 5.9; last per-step factors 2.25, 2.22, 2.20 | – | completed; fitted on n=1..8 (accepted); verdict differs from the intended one at n=9..20 |

### nest-diamond-default

Valid: S<T> is P and S<T> is Q each need T is P and T is Q (2^d subgoals without sharing). Intended verdict: accepted. Primary counter: `summon.matches`.

| n | base count | base ms | FIX count | FIX ms | MIN5 count | MIN5 ms | FULL count | FULL ms |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 224 | 31.3 | 224 | 9.7 | 8 | 0.9 | 8 | 2.3 |
| 2 | 524 | 37.9 | 524 | 15.2 | 20 | 0.8 | 20 | 6.0 |
| 3 | 1,432 ✗(depth) | 53.7 | 1,432 ✗(depth) | 31.5 | 64 ✗(depth) | 1.7 | 64 ✗(depth) | 7.8 |
| 4 | 1,448 ✗(depth) | 49.5 | 1,448 ✗(depth) | 35.7 | 80 ✗(depth) | 1.8 | 80 ✗(depth) | 6.9 |
| 5 | 1,462 ✗(depth) | 48.4 | 1,462 ✗(depth) | 32.6 | 94 ✗(depth) | 6.3 | 94 ✗(depth) | 3.8 |
| 6 | 1,472 ✗(depth) | 45.1 | 1,472 ✗(depth) | 35.7 | 104 ✗(depth) | 1.9 | 104 ✗(depth) | 8.0 |
| 8 | 1,486 ✗(depth) | 77.0 | 1,486 ✗(depth) | 34.9 | 118 ✗(depth) | 4.6 | 118 ✗(depth) | 4.0 |
| 12 | 1,488 ✗(depth) | 61.6 | 1,488 ✗(depth) | 35.2 | 120 ✗(depth) | 3.3 | 120 ✗(depth) | 3.7 |
| 16 | 1,488 ✗(depth) | 38.7 | 1,488 ✗(depth) | 39.7 | 120 ✗(depth) | 3.4 | 120 ✗(depth) | 3.4 |
| 32 | 1,488 ✗(depth) | 38.6 | 1,488 ✗(depth) | 53.5 | 120 ✗(depth) | 8.8 | 120 ✗(depth) | 5.0 |
| 64 | 1,488 ✗(depth) | 75.3 | 1,488 ✗(depth) | 34.2 | 120 ✗(depth) | 16.9 | 120 ✗(depth) | 10.6 |

| Configuration | Counter growth | Time growth | Counter: log-log fit / semi-log fit (upper half of the sizes), local exponents, per-step factors | Fastest other counter | Ends with |
|---|---|---|---|---|---|
| base | flat | no clear growth (within a factor 2.5) | – | `solver.goalSteps`: 2n + 26 (exact) | completed; fitted on n=3..64 (rejected); verdict differs from the intended one at n=3..64 |
| FIX | flat | no clear growth (within a factor 2.5) | – | `solver.goalSteps`: 2n + 26 (exact) | completed; fitted on n=3..64 (rejected); verdict differs from the intended one at n=3..64 |
| MIN5 | undecided: n^0.1 (rms 0.07) or 1.01^n (rms 0.08) | below 50 ms throughout | n^0.01 (R² 0.382) / 1.00^n (R² 0.202); last local exponents 0.0, 0.0, 0.0; last per-step factors 1.00, 1.00, 1.00 | `solver.goalSteps`: 2n + 26 (exact) | completed; fitted on n=3..64 (rejected); verdict differs from the intended one at n=3..64 |
| FULL | undecided: n^0.1 (rms 0.07) or 1.01^n (rms 0.08) | below 50 ms throughout | n^0.01 (R² 0.382) / 1.00^n (R² 0.202); last local exponents 0.0, 0.0, 0.0; last per-step factors 1.00, 1.00, 1.00 | `solver.goalSteps`: 2n + 26 (exact) | completed; fitted on n=3..64 (rejected); verdict differs from the intended one at n=3..64 |

### nest-diamond-neg

Ill-typed: nest_diamond whose leaf Z is P but not Q. Intended verdict: rejected. Primary counter: `summon.matches`. Environment: `HYLO_TC_MAXDEPTH=1000`.

| n | base count | base ms | FIX count | FIX ms | MIN5 count | MIN5 ms | FULL count | FULL ms |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 295 | 22.4 | 295 | 21.6 | 9 | 5.8 | 1 | 10.2 |
| 2 | 445 | 44.1 | 445 | 48.0 | 15 | 5.5 | 1 | 2.5 |
| 3 | 597 | 70.4 | 597 | 37.0 | 23 | 1.6 | 1 | 2.1 |
| 4 | 751 | 50.8 | 751 | 32.6 | 33 | 1.7 | 1 | 6.1 |
| 5 | 907 | 72.6 | 907 | 47.0 | 45 | 6.0 | 1 | 2.4 |
| 6 | 1,065 | 83.0 | 1,065 | 56.1 | 59 | 6.2 | 1 | 2.6 |
| 8 | 1,387 | 81.7 | 1,387 | 57.7 | 93 | 14.5 | 1 | 5.3 |
| 10 | 1,717 | 99.8 | 1,717 | 62.8 | 135 | 6.4 | 1 | 2.8 |
| 12 | 2,055 | 124 | 2,055 | 88.7 | 185 | 7.7 | 1 | 6.6 |
| 14 | 2,401 | 136 | 2,401 | 109 | 243 | 20.7 | 1 | 6.2 |
| 16 | 2,755 | 144 | 2,755 | 201 | 309 | 13.3 | 1 | 2.1 |
| 20 | 3,487 | 136 | 3,487 | 153 | 465 | 5.8 | 1 | 6.4 |

| Configuration | Counter growth | Time growth | Counter: log-log fit / semi-log fit (upper half of the sizes), local exponents, per-step factors | Fastest other counter | Ends with |
|---|---|---|---|---|---|
| base | n^2 + 147n + 147 (exact) | undecided: n^0.6 (rms 0.10) or 1.06^n (rms 0.15) | n^1.01 (R² 1.000) / 1.08^n (R² 0.985); last local exponents 1.0, 1.0, 1.1; last per-step factors 1.08, 1.07, 1.06 | – | completed |
| FIX | n^2 + 147n + 147 (exact) | undecided: n^1.7 (rms 0.18) or 1.10^n (rms 0.19) | n^1.01 (R² 1.000) / 1.08^n (R² 0.985); last local exponents 1.0, 1.0, 1.1; last per-step factors 1.08, 1.07, 1.06 | – | completed |
| MIN5 | n^2 + 3n + 5 (exact) | below 50 ms throughout | n^1.76 (R² 1.000) / 1.14^n (R² 0.985); last local exponents 1.8, 1.8, 1.8; last per-step factors 1.15, 1.13, 1.11 | – | completed |
| FULL | flat | below 50 ms throughout | – | `solver.goalSteps`: 2n + 24 (exact) | completed |
| FULL-absmodel | n^2 + 3n + 5 (exact) | below 50 ms throughout | n^1.76 (R² 1.000) / 1.14^n (R² 0.985); last local exponents 1.8, 1.8, 1.8; last per-step factors 1.15, 1.13, 1.11 | – | completed |

Leave-one-out configurations (same counter):

| n | FULL-absmodel count | FULL-absmodel ms |
|---:|---:|---:|
| 1 | 9 | 1.1 |
| 2 | 15 | 1.2 |
| 3 | 23 | 5.6 |
| 4 | 33 | 1.4 |
| 5 | 45 | 1.9 |
| 6 | 59 | 2.2 |
| 8 | 93 | 6.5 |
| 10 | 135 | 8.6 |
| 12 | 185 | 8.7 |
| 14 | 243 | 21.6 |
| 16 | 309 | 8.6 |
| 20 | 465 | 13.2 |

### refine

Valid: T is Q{n} where Q{i} refines Q{i-1} ... refines P; the goal is T is P. Intended verdict: accepted. Primary counter: `summon.matches`.

| n | base count | base ms | FIX count | FIX ms | MIN5 count | MIN5 ms | FULL count | FULL ms |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 146 | 62.7 | 146 | 35.2 | 4 | 6.7 | 4 | 8.8 |
| 2 | 221 | 80.2 | 221 | 38.8 | 5 | 11.0 | 5 | 8.0 |
| 3 | 298 | 87.3 | 298 | 37.9 | 6 | 6.6 | 6 | 8.0 |
| 4 | 377 | 81.9 | 377 | 40.4 | 7 | 2.8 | 7 | 8.2 |
| 5 | 458 | 85.2 | 458 | 46.4 | 8 | 7.3 | 8 | 12.6 |
| 6 | 541 | 108 | 541 | 96.0 | 9 | 11.6 | 9 | 9.5 |
| 7 | 626 | 105 | 626 | 46.7 | 10 | 7.8 | 10 | 14.0 |
| 8 | 713 | 129 | 713 | 82.0 | 11 | 11.2 | 11 | 12.9 |

| Configuration | Counter growth | Time growth | Counter: log-log fit / semi-log fit (upper half of the sizes), local exponents, per-step factors | Fastest other counter | Ends with |
|---|---|---|---|---|---|
| base | n^2 + 72n + 73 (exact) | no clear growth (within a factor 2.5) | n^0.94 (R² 1.000) / 1.16^n (R² 0.997); last local exponents 0.9, 0.9, 1.0; last per-step factors 1.18, 1.16, 1.14 | – | completed |
| FIX | n^2 + 72n + 73 (exact) | undecided: n^2.0 (rms 0.24) or 1.26^n (rms 0.24) | n^0.94 (R² 1.000) / 1.16^n (R² 0.997); last local exponents 0.9, 0.9, 1.0; last per-step factors 1.18, 1.16, 1.14 | – | completed |
| MIN5 | n + 3 (exact) | below 50 ms throughout | n^0.68 (R² 0.999) / 1.11^n (R² 0.998); last local exponents 0.6, 0.7, 0.7; last per-step factors 1.12, 1.11, 1.10 | – | completed |
| FULL | n + 3 (exact) | below 50 ms throughout | n^0.68 (R² 0.999) / 1.11^n (R² 0.998); last local exponents 0.6, 0.7, 0.7; last per-step factors 1.12, 1.11, 1.10 | – | completed |

### refine-deep

Valid: T is Q{n} where Q{i} refines Q{i-1} ... refines P; the goal is T is P. Intended verdict: accepted. Primary counter: `summon.matches`. Environment: `HYLO_TC_MAXDEPTH=1000`.

| n | base count | base ms | FIX count | FIX ms | MIN5 count | MIN5 ms | FULL count | FULL ms |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 4 | 377 | 99.6 | 377 | 40.4 | 7 | 6.5 | 7 | 7.7 |
| 8 | 713 | 170 | 713 | 62.2 | 11 | 3.1 | 11 | 14.4 |
| 16 | 1,481 | 211 | 1,481 | 157 | 19 | 7.8 | 19 | 17.9 |
| 32 | 3,401 | 532 | 3,401 | 452 | 35 | 21.4 | 35 | 13.6 |
| 64 | 8,777 | 2,751 | 8,777 | 2,256 | 67 | 20.7 | 67 | 31.2 |

| Configuration | Counter growth | Time growth | Counter: log-log fit / semi-log fit (upper half of the sizes), local exponents, per-step factors | Fastest other counter | Ends with |
|---|---|---|---|---|---|
| base | n^2 + 72n + 73 (exact) | undecided: n^2.4 (rms 0.15) or 1.05^n (rms 0.11) | n^1.28 (R² 0.999) / 1.04^n (R² 0.977); last local exponents 1.1, 1.2, 1.4; last per-step factors 1.10, 1.05, 1.03 | – | completed |
| FIX | n^2 + 72n + 73 (exact) | n^2.12 (rms 0.07) | n^1.28 (R² 0.999) / 1.04^n (R² 0.977); last local exponents 1.1, 1.2, 1.4; last per-step factors 1.10, 1.05, 1.03 | – | completed |
| MIN5 | n + 3 (exact) | below 50 ms throughout | n^0.91 (R² 1.000) / 1.03^n (R² 0.971); last local exponents 0.8, 0.9, 0.9; last per-step factors 1.07, 1.04, 1.02 | – | completed |
| FULL | n + 3 (exact) | below 50 ms throughout | n^0.91 (R² 1.000) / 1.03^n (R² 0.971); last local exponents 0.8, 0.9, 0.9; last per-step factors 1.07, 1.04, 1.02 | – | completed |

### nestwide

Valid: n traits each declaring a nested given; n lookups, one per nested given. Intended verdict: accepted. Primary counter: `summon.matches`.

| n | base count | base ms | FIX count | FIX ms | MIN5 count | MIN5 ms | FULL count | FULL ms |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2 | 300 | 72.2 | 300 | 14.3 | 10 | 7.4 | 10 | 8.6 |
| 4 | 632 | 116 | 632 | 48.2 | 28 | 7.7 | 28 | 8.5 |
| 8 | 1,392 | 134 | 1,392 | 143 | 88 | 8.7 | 88 | 10.8 |
| 16 | 3,296 | 305 | 3,296 | 286 | 304 | 11.7 | 304 | 24.0 |
| 32 | 8,640 | 1,085 | 8,640 | 1,156 | 1,120 | 48.6 | 1,120 | 54.6 |
| 64 | 25,472 | 5,021 | 25,472 | 5,113 | 4,288 | 125 | 4,288 | 177 |

| Configuration | Counter growth | Time growth | Counter: log-log fit / semi-log fit (upper half of the sizes), local exponents, per-step factors | Fastest other counter | Ends with |
|---|---|---|---|---|---|
| base | 4n^2 + 142n (exact) | n^2.18 (rms 0.12) | n^1.48 (R² 0.999) / 1.04^n (R² 0.976); last local exponents 1.2, 1.4, 1.6; last per-step factors 1.11, 1.06, 1.03 | – | completed |
| FIX | 4n^2 + 142n (exact) | n^1.96 for n ≥ 4 (rms 0.15) | n^1.48 (R² 0.999) / 1.04^n (R² 0.976); last local exponents 1.2, 1.4, 1.6; last per-step factors 1.11, 1.06, 1.03 | – | completed |
| MIN5 | n^2 + 3n (exact) | undecided: n^2.1 (rms 0.14) or 1.05^n (rms 0.22) | n^1.91 (R² 1.000) / 1.05^n (R² 0.967); last local exponents 1.8, 1.9, 1.9; last per-step factors 1.17, 1.08, 1.04 | – | completed |
| FULL | n^2 + 3n (exact) | n^1.80 (rms 0.06) | n^1.91 (R² 1.000) / 1.05^n (R² 0.967); last local exponents 1.8, 1.9, 1.9; last per-step factors 1.17, 1.08, 1.04 | – | completed |

### open-chain

Valid: pick<T, U where U is Q, T == U>(x) with U inferred; A0 == ... == A{n}, A{n} is Q. Intended verdict: accepted. Primary counter: `summon.matches`.

| n | base count | base ms | FIX count | FIX ms | MIN5 count | MIN5 ms | FULL count | FULL ms |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 365 | 99.5 | 76 | 14.1 | 365 | 29.0 | 76 | 8.5 |
| 2 | 4,105 | 201 | 77 | 28.3 | 4,105 | 124 | 77 | 4.4 |
| 3 | 19,036 | 646 | 78 | 23.3 | 19,036 | 783 | 78 | 14.2 |
| 4 | 23,509 | 784 | 79 | 24.7 | 23,509 | 757 | 79 | 7.7 |
| 5 | 28,420 | 1,099 | 80 | 30.4 | 28,420 | 946 | 80 | 8.7 |
| 6 | 33,781 | 1,268 | 81 | 45.9 | 33,781 | 1,261 | 81 | 7.2 |
| 8 | 45,901 | 1,895 | 83 | 25.1 | 45,901 | 1,738 | 83 | 14.7 |
| 12 | 76,069 | 3,074 | 87 | 42.4 | 76,069 | 2,817 | 87 | 13.3 |
| 16 | 114,781 | 4,568 | 91 | 45.2 | 114,781 | 4,272 | 91 | 9.7 |
| 24 | 220,909 | 11,460 | 99 | 40.5 | 220,909 | 8,208 | 99 | 10.0 |
| 32 | timeout | >20 s | 107 | 36.9 | 370,429 | 14,854 | 107 | 10.2 |
| 64 | not run |  | 139 | 77.9 | not run |  | 139 | 15.8 |
| 128 | not run |  | 203 | 70.7 | not run |  | 203 | 17.1 |
| 256 | not run |  | 331 | 37.0 | not run |  | 331 | 23.0 |
| 512 | not run |  | 587 | 50.7 | not run |  | 587 | 37.5 |

| Configuration | Counter growth | Time growth | Counter: log-log fit / semi-log fit (upper half of the sizes), local exponents, per-step factors | Fastest other counter | Ends with |
|---|---|---|---|---|---|
| base | 2n^3 + 195n^2 + 3,034n + 8,125 (exact, n ≥ 3) | n^1.82 for n ≥ 3 (rms 0.07) | n^1.35 (R² 0.994) / 1.11^n (R² 0.985); last local exponents 1.2, 1.4, 1.6; last per-step factors 1.13, 1.11, 1.09 | – | timeout (>20 s) at n=32 |
| FIX | n + 75 (exact) | undecided: n^0.1 (rms 0.28) or 1.01^n (rms 0.38) | n^0.50 (R² 0.954) / 1.00^n (R² 0.939); last local exponents 0.5, 0.7, 0.8; last per-step factors 1.01, 1.00, 1.00 | – | completed |
| MIN5 | 2n^3 + 195n^2 + 3,034n + 8,125 (exact, n ≥ 3) | n^1.83 for n ≥ 3 (rms 0.06) | n^1.43 (R² 0.992) / 1.10^n (R² 0.980); last local exponents 1.4, 1.6, 1.8; last per-step factors 1.11, 1.09, 1.07 | – | stopped before n=64: predicted timeout: 15 s at n=32, power-law extrapolation gives 62 s at n=64 |
| FULL | n + 75 (exact) | below 50 ms throughout | n^0.50 (R² 0.954) / 1.00^n (R² 0.939); last local exponents 0.5, 0.7, 0.8; last per-step factors 1.01, 1.00, 1.00 | – | completed |
| FULL-eqsolve | undecided: n^1.9 (rms 0.97) or 1.03^n (rms 0.97) | undecided: no polynomial or 3.03^n (rms 0.59) | n^-0.56 (R² 0.085) / 0.99^n (R² 0.038); last local exponents 1.8, -6.7, 1.4; last per-step factors 1.10, 0.79, 1.03 | – | timeout (>20 s) at n=128; fitted on n=8..64 (rejected, resource bound hit); resource bound (`budget`) hit from n=8; verdict differs from the intended one at n=4..64 |

Leave-one-out configurations (same counter):

| n | FULL-eqsolve count | FULL-eqsolve ms |
|---:|---:|---:|
| 1 | 222 | 14.3 |
| 2 | 1,278 | 31.3 |
| 3 | 13,007 | 462 |
| 4 | 17,806 ✗(depth) | 429 |
| 5 | 23,399 ✗(depth) | 653 |
| 6 | 29,816 ✗(depth) | 1,064 |
| 8 | 45,242 ✗ [B] | 1,284 |
| 12 | 87,302 ✗ [B] | 3,889 |
| 16 | 41,448 ✗ [B] | 1,147 |
| 24 | 85,696 ✗ [B] | 2,866 |
| 32 | 12,408 ✗ [B] | 955 |
| 64 | 32,216 ✗ [B] | 4,232 |
| 128 | timeout | >20 s |

### open-neg

Ill-typed: open_chain without any conformance to Q. Intended verdict: rejected. Primary counter: `summon.matches`.

| n | base count | base ms | FIX count | FIX ms | MIN5 count | MIN5 ms | FULL count | FULL ms |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | timeout | >20 s | 73 | 10.5 | timeout | >20 s | 2 | 4.3 |
| 2 | not run |  | 74 | 10.1 | not run |  | 2 | 4.5 |
| 3 | not run |  | 75 | 14.1 | not run |  | 2 | 8.1 |
| 4 | not run |  | 76 | 10.4 | not run |  | 2 | 5.8 |
| 5 | not run |  | 77 | 10.4 | not run |  | 2 | 11.8 |
| 6 | not run |  | 78 | 10.3 | not run |  | 2 | 4.5 |
| 8 | not run |  | 80 | 11.2 | not run |  | 2 | 4.5 |
| 12 | not run |  | 84 | 18.9 | not run |  | 2 | 6.3 |
| 16 | not run |  | 88 | 12.6 | not run |  | 2 | 4.7 |
| 24 | not run |  | 96 | 30.9 | not run |  | 2 | 13.1 |
| 32 | not run |  | 104 | 31.4 | not run |  | 2 | 3.9 |
| 64 | not run |  | 136 | 16.7 | not run |  | 2 | 10.1 |
| 128 | not run |  | 200 | 18.1 | not run |  | 2 | 13.8 |
| 256 | not run |  | 328 | 44.5 | not run |  | 2 | 13.2 |
| 512 | not run |  | 584 | 77.6 | not run |  | 2 | 34.2 |

| Configuration | Counter growth | Time growth | Counter: log-log fit / semi-log fit (upper half of the sizes), local exponents, per-step factors | Fastest other counter | Ends with |
|---|---|---|---|---|---|
| base | – | – | – | – | timeout (>20 s) at n=1 |
| FIX | n + 72 (exact) | undecided: n^2.2 (rms 0.29) or 1.01^n (rms 0.35) | n^0.51 (R² 0.955) / 1.00^n (R² 0.937); last local exponents 0.6, 0.7, 0.8; last per-step factors 1.01, 1.00, 1.00 | – | completed |
| MIN5 | – | – | – | – | timeout (>20 s) at n=1 |
| FULL | flat | below 50 ms throughout | – | – | completed |

### open-wide

Valid: pick has n inferred arguments U{i}, each with U{i} is Q and T == U{i}. Intended verdict: accepted. Primary counter: `summon.matches`.

| n | base count | base ms | FIX count | FIX ms | MIN5 count | MIN5 ms | FULL count | FULL ms |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 289 | 90.3 | 73 | 16.3 | 219 | 4.9 | 3 | 5.8 |
| 2 | 4,857 | 193 | 219 | 20.3 | 4,577 | 115 | 79 | 4.4 |
| 3 | 154,231 | 4,182 | 1,911 | 79.4 | 151,711 | 4,355 | 1,351 | 9.9 |
| 4 | timeout | >20 s | 28,201 | 749 | not run |  | 24,281 | 226 |
| 5 | not run |  | 93,136 ✗ [B] | 3,615 | not run |  | 93,136 ✗ [B] | 1,335 |
| 6 | not run |  | 48,436 ✗ [B] | 2,198 | not run |  | 48,436 ✗ [B] | 1,010 |
| 8 | not run |  | 105,372 ✗ [B] | 6,223 | not run |  | 105,372 ✗ [B] | 3,492 |
| 12 | not run |  | 70,731 ✗ [B] | 3,277 | not run |  | 70,731 ✗ [B] | 2,434 |
| 16 | not run |  | 11,051 ✗ [B] | 854 | not run |  | 11,051 ✗ [B] | 869 |

| Configuration | Counter growth | Time growth | Counter: log-log fit / semi-log fit (upper half of the sizes), local exponents, per-step factors | Fastest other counter | Ends with |
|---|---|---|---|---|---|
| base | too few points (3) | too few points (3) | n^5.54 (R² 0.957) / 23.10^n (R² 0.997); last local exponents 4.1, 8.5; last per-step factors 16.81, 31.75 | – | timeout (>20 s) at n=4 |
| FIX | 13.76^n (rms 0.05) | 11.80^n (rms 0.02) | n^6.90 (R² 0.975) / 11.35^n (R² 0.996); last local exponents 1.6, 5.3, 9.4; last per-step factors 3.00, 8.73, 14.76 | – | completed; fitted on n=1..4 (accepted); resource bound (`budget`) hit from n=5; verdict differs from the intended one at n=5..16 |
| MIN5 | too few points (3) | too few points (3) | n^5.78 (R² 0.964) / 26.32^n (R² 0.998); last local exponents 4.4, 8.6; last per-step factors 20.90, 33.15 | – | stopped before n=4: predicted timeout: 4 s at n=3, power-law extrapolation gives 57 s at n=4 |
| FULL | 19.76^n (rms 0.11) | undecided: n^13.3 (rms 0.10) or 40.00^n (rms 0.11) | n^8.18 (R² 0.989) / 17.53^n (R² 1.000); last local exponents 4.7, 7.0, 10.0; last per-step factors 26.33, 17.10, 17.97 | – | completed; fitted on n=1..4 (accepted); resource bound (`budget`) hit from n=5; verdict differs from the intended one at n=5..16 |

### open-wide-nobudget

Valid: pick has n inferred arguments U{i}, each with U{i} is Q and T == U{i}. Intended verdict: accepted. Primary counter: `summon.matches`. Environment: `HYLO_TC_BUDGET=1000000000`.

| n | base count | base ms | FIX count | FIX ms | MIN5 count | MIN5 ms | FULL count | FULL ms |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 289 | 34.9 | 73 | 17.6 | 219 | 3.8 | 3 | 8.2 |
| 2 | 4,857 | 252 | 219 | 26.5 | 4,577 | 81.7 | 79 | 8.7 |
| 3 | 154,231 | 4,773 | 1,911 | 64.8 | 151,711 | 4,092 | 1,351 | 32.5 |
| 4 | timeout | >20 s | 28,201 | 639 | not run |  | 24,281 | 314 |
| 5 | not run |  | 232,660 ✗(depth) | 5,876 | not run |  | 232,660 ✗(depth) | 3,724 |
| 6 | not run |  | timeout | >20 s | not run |  | 642,047 ✗(depth) | 13,902 |
| 7 | not run |  | not run |  | not run |  | 1,297,200 ✗(depth) | 35,154 |
| 8 | not run |  | not run |  | not run |  | crash (out of memory) | 35 s wall |

| Configuration | Counter growth | Time growth | Counter: log-log fit / semi-log fit (upper half of the sizes), local exponents, per-step factors | Fastest other counter | Ends with |
|---|---|---|---|---|---|
| base | too few points (3) | too few points (3) | n^5.54 (R² 0.957) / 23.10^n (R² 0.997); last local exponents 4.1, 8.5; last per-step factors 16.81, 31.75 | – | timeout (>20 s) at n=4 |
| FIX | 13.76^n (rms 0.05) | undecided: n^8.9 (rms 0.13) or 12.16^n (rms 0.09) | n^6.90 (R² 0.975) / 11.35^n (R² 0.996); last local exponents 1.6, 5.3, 9.4; last per-step factors 3.00, 8.73, 14.76 | – | timeout (>20 s) at n=6; fitted on n=1..4 (accepted); verdict differs from the intended one at n=5 |
| MIN5 | too few points (3) | too few points (3) | n^5.78 (R² 0.964) / 26.32^n (R² 0.998); last local exponents 4.4, 8.6; last per-step factors 20.90, 33.15 | – | stopped before n=4: predicted timeout: 4 s at n=3, power-law extrapolation gives 66 s at n=4 |
| FULL | 19.76^n (rms 0.11) | n^8.80 (rms 0.01) | n^8.18 (R² 0.989) / 17.53^n (R² 1.000); last local exponents 4.7, 7.0, 10.0; last per-step factors 26.33, 17.10, 17.97 | – | crash (exit 134) at n=8; fitted on n=1..4 (accepted); verdict differs from the intended one at n=5..7 |

### req-traits

Valid: f<T where T is P1..Pn> calls g<T> with the same n requirements. Intended verdict: accepted. Primary counter: `summon.matches`.

| n | base count | base ms | FIX count | FIX ms | MIN5 count | MIN5 ms | FULL count | FULL ms |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 72 | 71.3 | 72 | 15.4 | 2 | 8.0 | 2 | 7.9 |
| 2 | 146 | 61.1 | 146 | 27.9 | 4 | 2.5 | 4 | 3.9 |
| 4 | 303 | 64.8 | 303 | 18.4 | 11 | 6.8 | 11 | 8.0 |
| 8 | 653 | 90.1 | 653 | 46.8 | 37 | 3.1 | 37 | 8.3 |
| 9 | 748 | 122 | 748 | 30.0 | 46 | 2.7 | 46 | 3.6 |
| 10 | 1,566 ✗(depth) | 107 | 1,566 ✗(depth) | 44.2 | 65 ✗(depth) | 3.3 | 65 ✗(depth) | 4.1 |
| 11 | 1,675 ✗(depth) | 113 | 1,675 ✗(depth) | 86.1 | 75 ✗(depth) | 3.3 | 75 ✗(depth) | 8.1 |
| 12 | 1,786 ✗(depth) | 109 | 1,786 ✗(depth) | 74.2 | 85 ✗(depth) | 3.3 | 85 ✗(depth) | 4.8 |
| 16 | 2,250 ✗(depth) | 100 | 2,250 ✗(depth) | 83.0 | 125 ✗(depth) | 8.5 | 125 ✗(depth) | 9.4 |
| 32 | 4,426 ✗(depth) | 311 | 4,426 ✗(depth) | 280 | 285 ✗(depth) | 7.5 | 285 ✗(depth) | 8.3 |
| 64 | 10,314 ✗(depth) | 668 | 10,314 ✗(depth) | 988 | 605 ✗(depth) | 50.5 | 605 ✗(depth) | 13.3 |
| 128 | 28,234 ✗(depth) | 3,862 | 28,234 ✗(depth) | 4,743 | 1,245 ✗(depth) | 147 | 1,245 ✗(depth) | 30.2 |

| Configuration | Counter growth | Time growth | Counter: log-log fit / semi-log fit (upper half of the sizes), local exponents, per-step factors | Fastest other counter | Ends with |
|---|---|---|---|---|---|
| base | 1.5n^2 + 69.5n + 1 (exact) | no clear growth (within a factor 2.5) | n^1.11 (R² 1.000) / 1.20^n (R² 0.997); last local exponents 1.1, 1.1, 1.2; last per-step factors 1.44, 1.21, 1.15 | – | completed; fitted on n=1..9 (accepted); verdict differs from the intended one at n=10..128 |
| FIX | 1.5n^2 + 69.5n + 1 (exact) | below 50 ms throughout | n^1.11 (R² 1.000) / 1.20^n (R² 0.997); last local exponents 1.1, 1.1, 1.2; last per-step factors 1.44, 1.21, 1.15 | – | completed; fitted on n=1..9 (accepted); verdict differs from the intended one at n=10..128 |
| MIN5 | 0.5n^2 + 0.5n + 1 (exact) | below 50 ms throughout | n^1.76 (R² 1.000) / 1.34^n (R² 0.998); last local exponents 1.5, 1.8, 1.8; last per-step factors 1.66, 1.35, 1.24 | – | completed; fitted on n=1..9 (accepted); verdict differs from the intended one at n=10..128 |
| FULL | 0.5n^2 + 0.5n + 1 (exact) | below 50 ms throughout | n^1.76 (R² 1.000) / 1.34^n (R² 0.998); last local exponents 1.5, 1.8, 1.8; last per-step factors 1.66, 1.35, 1.24 | – | completed; fitted on n=1..9 (accepted); verdict differs from the intended one at n=10..128 |

### req-params

Valid: f<T1..Tn where Ti is P> calls g<T1, ..., Tn> with the same n requirements. Intended verdict: accepted. Primary counter: `summon.matches`.

| n | base count | base ms | FIX count | FIX ms | MIN5 count | MIN5 ms | FULL count | FULL ms |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 72 | 36.1 | 72 | 28.4 | 2 | 2.2 | 2 | 7.5 |
| 2 | 146 | 35.7 | 146 | 19.8 | 6 | 7.1 | 6 | 7.2 |
| 4 | 303 | 32.8 | 303 | 16.3 | 23 | 6.5 | 23 | 9.3 |
| 8 | 653 | 89.6 | 653 | 40.2 | 93 | 3.3 | 93 | 8.3 |
| 9 | 748 | 84.7 | 748 | 43.1 | 118 | 3.3 | 118 | 4.6 |
| 10 | 1,566 ✗(depth) | 126 | 1,566 ✗(depth) | 105 | 236 ✗(depth) | 10.0 | 236 ✗(depth) | 8.8 |
| 11 | 1,675 ✗(depth) | 143 | 1,675 ✗(depth) | 67.9 | 275 ✗(depth) | 10.4 | 275 ✗(depth) | 6.6 |
| 12 | 1,786 ✗(depth) | 87.0 | 1,786 ✗(depth) | 58.2 | 316 ✗(depth) | 15.0 | 316 ✗(depth) | 9.8 |
| 16 | 2,250 ✗(depth) | 154 | 2,250 ✗(depth) | 58.1 | 500 ✗(depth) | 9.8 | 500 ✗(depth) | 14.8 |
| 32 | 4,426 ✗(depth) | 192 | 4,426 ✗(depth) | 190 | 1,556 ✗(depth) | 28.9 | 1,556 ✗(depth) | 18.8 |
| 64 | 10,314 ✗(depth) | 823 | 10,314 ✗(depth) | 973 | 5,204 ✗(depth) | 106 | 5,204 ✗(depth) | 40.8 |
| 128 | 28,234 ✗(depth) | 4,691 | 28,234 ✗(depth) | 4,045 | 18,644 ✗(depth) | 162 | 18,644 ✗(depth) | 157 |

| Configuration | Counter growth | Time growth | Counter: log-log fit / semi-log fit (upper half of the sizes), local exponents, per-step factors | Fastest other counter | Ends with |
|---|---|---|---|---|---|
| base | 1.5n^2 + 69.5n + 1 (exact) | undecided: n^3.4 (rms 0.12) or 1.53^n (rms 0.14) | n^1.11 (R² 1.000) / 1.20^n (R² 0.997); last local exponents 1.1, 1.1, 1.2; last per-step factors 1.44, 1.21, 1.15 | – | completed; fitted on n=1..9 (accepted); verdict differs from the intended one at n=10..128 |
| FIX | 1.5n^2 + 69.5n + 1 (exact) | below 50 ms throughout | n^1.11 (R² 1.000) / 1.20^n (R² 0.997); last local exponents 1.1, 1.1, 1.2; last per-step factors 1.44, 1.21, 1.15 | – | completed; fitted on n=1..9 (accepted); verdict differs from the intended one at n=10..128 |
| MIN5 | 1.5n^2 − 0.5n + 1 (exact) | below 50 ms throughout | n^2.02 (R² 1.000) / 1.40^n (R² 0.997); last local exponents 1.9, 2.0, 2.0; last per-step factors 1.96, 1.42, 1.27 | – | completed; fitted on n=1..9 (accepted); verdict differs from the intended one at n=10..128 |
| FULL | 1.5n^2 − 0.5n + 1 (exact) | below 50 ms throughout | n^2.02 (R² 1.000) / 1.40^n (R² 0.997); last local exponents 1.9, 2.0, 2.0; last per-step factors 1.96, 1.42, 1.27 | – | completed; fitted on n=1..9 (accepted); verdict differs from the intended one at n=10..128 |

### req-eq

Valid: f<T1..Tn, U1..Un where Ti == Ui> calls g with the same n equality requirements. Intended verdict: accepted. Primary counter: `summon.matches`.

| n | base count | base ms | FIX count | FIX ms | MIN5 count | MIN5 ms | FULL count | FULL ms |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 72 | 40.1 | 2 | 5.6 | 72 | 1.4 | 2 | 1.0 |
| 2 | 296 | 18.9 | 3 | 10.8 | 296 | 3.7 | 3 | 0.9 |
| 4 | 6,818 | 176 | 5 | 14.9 | 6,818 | 212 | 5 | 1.0 |
| 8 | timeout | >20 s | 9 | 11.1 | timeout | >20 s | 9 | 2.0 |
| 9 | not run |  | 10 | 7.7 | not run |  | 10 | 1.6 |
| 10 | not run |  | 20 ✗(depth) | 17.5 | not run |  | 20 ✗(depth) | 6.3 |
| 11 | not run |  | 21 ✗(depth) | 17.5 | not run |  | 21 ✗(depth) | 7.7 |
| 12 | not run |  | 22 ✗(depth) | 9.8 | not run |  | 22 ✗(depth) | 2.8 |
| 16 | not run |  | 26 ✗(depth) | 17.8 | not run |  | 26 ✗(depth) | 9.1 |
| 32 | not run |  | 42 ✗(depth) | 20.2 | not run |  | 42 ✗(depth) | 19.1 |
| 64 | not run |  | 74 ✗(depth) | 48.8 | not run |  | 74 ✗(depth) | 25.6 |
| 128 | not run |  | 138 ✗(depth) | 60.7 | not run |  | 138 ✗(depth) | 113 |
| 256 | not run |  | 266 ✗(depth) | 463 | not run |  | 266 ✗(depth) | 369 |
| 512 | not run |  | 522 ✗(depth) | 1,304 | not run |  | 522 ✗(depth) | 1,139 |

| Configuration | Counter growth | Time growth | Counter: log-log fit / semi-log fit (upper half of the sizes), local exponents, per-step factors | Fastest other counter | Ends with |
|---|---|---|---|---|---|
| base | too few points (3) | too few points (3) | n^3.28 (R² 0.954) / 4.59^n (R² 0.999); last local exponents 2.0, 4.5; last per-step factors 4.11, 4.80 | – | timeout (>20 s) at n=8 |
| FIX | n + 1 (exact) | below 50 ms throughout | n^0.85 (R² 1.000) / 1.15^n (R² 0.998); last local exponents 0.7, 0.8, 0.9; last per-step factors 1.29, 1.16, 1.11 | – | completed; fitted on n=1..9 (accepted); verdict differs from the intended one at n=10..512 |
| MIN5 | too few points (3) | too few points (3) | n^3.28 (R² 0.954) / 4.59^n (R² 0.999); last local exponents 2.0, 4.5; last per-step factors 4.11, 4.80 | – | timeout (>20 s) at n=8 |
| FULL | n + 1 (exact) | below 50 ms throughout | n^0.85 (R² 1.000) / 1.15^n (R² 0.998); last local exponents 0.7, 0.8, 0.9; last per-step factors 1.29, 1.16, 1.11 | – | completed; fitted on n=1..9 (accepted); verdict differs from the intended one at n=10..512 |

### req-traits-deep

Valid: f<T where T is P1..Pn> calls g<T> with the same n requirements. Intended verdict: accepted. Primary counter: `summon.matches`. Environment: `HYLO_TC_MAXDEPTH=1000`.

| n | base count | base ms | FIX count | FIX ms | MIN5 count | MIN5 ms | FULL count | FULL ms |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 72 | 47.5 | 72 | 36.1 | 2 | 2.2 | 2 | 3.7 |
| 2 | 146 | 30.0 | 146 | 11.2 | 4 | 2.4 | 4 | 5.7 |
| 4 | 303 | 58.6 | 303 | 26.2 | 11 | 4.3 | 11 | 5.0 |
| 8 | 653 | 62.1 | 653 | 43.3 | 37 | 3.0 | 37 | 4.2 |
| 16 | 1,497 | 126 | 1,497 | 82.0 | 137 | 4.4 | 137 | 8.2 |
| 32 | 3,761 | 297 | 3,761 | 197 | 529 | 9.6 | 529 | 7.9 |
| 64 | 10,593 | 999 | 10,593 | 1,329 | 2,081 | 107 | 2,081 | 24.8 |
| 128 | 33,473 | 7,080 | 33,473 | 8,280 | 8,257 | 874 | 8,257 | 105 |
| 256 | not run |  | not run |  | 32,897 | 7,841 | 32,897 | 754 |

| Configuration | Counter growth | Time growth | Counter: log-log fit / semi-log fit (upper half of the sizes), local exponents, per-step factors | Fastest other counter | Ends with |
|---|---|---|---|---|---|
| base | 1.5n^2 + 69.5n + 1 (exact) | n^2.35 for n ≥ 4 (rms 0.14) | n^1.49 (R² 0.998) / 1.03^n (R² 0.944); last local exponents 1.3, 1.5, 1.7; last per-step factors 1.06, 1.03, 1.02 | – | stopped before n=256: predicted timeout: 7 s at n=128, power-law extrapolation gives 50 s at n=256 |
| FIX | 1.5n^2 + 69.5n + 1 (exact) | n^2.76 for n ≥ 8 (rms 0.10) | n^1.49 (R² 0.998) / 1.03^n (R² 0.944); last local exponents 1.3, 1.5, 1.7; last per-step factors 1.06, 1.03, 1.02 | – | stopped before n=256: predicted timeout: 8 s at n=128, power-law extrapolation gives 52 s at n=256 |
| MIN5 | 0.5n^2 + 0.5n + 1 (exact) | n^3.30 for n ≥ 8 (rms 0.13) | n^1.98 (R² 1.000) / 1.02^n (R² 0.874); last local exponents 2.0, 2.0, 2.0; last per-step factors 1.04, 1.02, 1.01 | – | completed |
| FULL | 0.5n^2 + 0.5n + 1 (exact) | n^2.81 for n ≥ 16 (rms 0.10) | n^1.98 (R² 1.000) / 1.02^n (R² 0.874); last local exponents 2.0, 2.0, 2.0; last per-step factors 1.04, 1.02, 1.01 | – | completed |

### req-params-deep

Valid: f<T1..Tn where Ti is P> calls g<T1, ..., Tn> with the same n requirements. Intended verdict: accepted. Primary counter: `summon.matches`. Environment: `HYLO_TC_MAXDEPTH=1000`.

| n | base count | base ms | FIX count | FIX ms | MIN5 count | MIN5 ms | FULL count | FULL ms |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 72 | 58.8 | 72 | 24.1 | 2 | 6.7 | 2 | 3.8 |
| 2 | 146 | 102 | 146 | 23.0 | 6 | 5.2 | 6 | 7.7 |
| 4 | 303 | 83.8 | 303 | 49.1 | 23 | 3.1 | 23 | 4.0 |
| 8 | 653 | 104 | 653 | 53.4 | 93 | 3.1 | 93 | 7.8 |
| 16 | 1,497 | 111 | 1,497 | 47.6 | 377 | 6.4 | 377 | 9.6 |
| 32 | 3,761 | 410 | 3,761 | 139 | 1,521 | 19.8 | 1,521 | 26.8 |
| 64 | 10,593 | 1,090 | 10,593 | 1,423 | 6,113 | 162 | 6,113 | 79.8 |
| 128 | 33,473 | 8,709 | 33,473 | 8,391 | 24,513 | 1,141 | 24,513 | 489 |
| 256 | not run |  | not run |  | 98,177 | 15,451 | 98,177 | 3,184 |

| Configuration | Counter growth | Time growth | Counter: log-log fit / semi-log fit (upper half of the sizes), local exponents, per-step factors | Fastest other counter | Ends with |
|---|---|---|---|---|---|
| base | 1.5n^2 + 69.5n + 1 (exact) | undecided: n^2.6 (rms 0.17) or 1.04^n (rms 0.23) | n^1.49 (R² 0.998) / 1.03^n (R² 0.944); last local exponents 1.3, 1.5, 1.7; last per-step factors 1.06, 1.03, 1.02 | – | stopped before n=256: predicted timeout: 9 s at n=128, power-law extrapolation gives 70 s at n=256 |
| FIX | 1.5n^2 + 69.5n + 1 (exact) | n^3.23 for n ≥ 4 (rms 0.17) | n^1.49 (R² 0.998) / 1.03^n (R² 0.944); last local exponents 1.3, 1.5, 1.7; last per-step factors 1.06, 1.03, 1.02 | – | stopped before n=256: predicted timeout: 8 s at n=128, power-law extrapolation gives 49 s at n=256 |
| MIN5 | 1.5n^2 − 0.5n + 1 (exact) | n^3.30 for n ≥ 16 (rms 0.12) | n^2.01 (R² 1.000) / 1.02^n (R² 0.870); last local exponents 2.0, 2.0, 2.0; last per-step factors 1.04, 1.02, 1.01 | – | completed |
| FULL | 1.5n^2 − 0.5n + 1 (exact) | n^2.56 for n ≥ 8 (rms 0.11) | n^2.01 (R² 1.000) / 1.02^n (R² 0.870); last local exponents 2.0, 2.0, 2.0; last per-step factors 1.04, 1.02, 1.01 | – | completed |

### req-eq-deep

Valid: f<T1..Tn, U1..Un where Ti == Ui> calls g with the same n equality requirements. Intended verdict: accepted. Primary counter: `summon.matches`. Environment: `HYLO_TC_MAXDEPTH=1000`.

| n | base count | base ms | FIX count | FIX ms | MIN5 count | MIN5 ms | FULL count | FULL ms |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 72 | 39.8 | 2 | 9.5 | 72 | 1.1 | 2 | 0.9 |
| 2 | 296 | 49.1 | 3 | 4.9 | 296 | 2.8 | 3 | 0.9 |
| 4 | 6,818 | 241 | 5 | 21.9 | 6,818 | 155 | 5 | 0.9 |
| 8 | timeout | >20 s | 9 | 15.7 | timeout | >20 s | 9 | 1.4 |
| 16 | not run |  | 17 | 16.1 | not run |  | 17 | 6.6 |
| 32 | not run |  | 33 | 26.8 | not run |  | 33 | 23.1 |
| 64 | not run |  | 65 | 52.9 | not run |  | 65 | 27.2 |
| 128 | not run |  | 129 | 172 | not run |  | 129 | 95.8 |
| 256 | not run |  | 257 | 814 | not run |  | 257 | 411 |

| Configuration | Counter growth | Time growth | Counter: log-log fit / semi-log fit (upper half of the sizes), local exponents, per-step factors | Fastest other counter | Ends with |
|---|---|---|---|---|---|
| base | too few points (3) | too few points (3) | n^3.28 (R² 0.954) / 4.59^n (R² 0.999); last local exponents 2.0, 4.5; last per-step factors 4.11, 4.80 | – | timeout (>20 s) at n=8 |
| FIX | n + 1 (exact) | n^2.15 for n ≥ 8 (rms 0.07) | n^0.98 (R² 1.000) / 1.01^n (R² 0.876); last local exponents 1.0, 1.0, 1.0; last per-step factors 1.02, 1.01, 1.01 | – | completed |
| MIN5 | too few points (3) | too few points (3) | n^3.28 (R² 0.954) / 4.59^n (R² 0.999); last local exponents 2.0, 4.5; last per-step factors 4.11, 4.80 | – | timeout (>20 s) at n=8 |
| FULL | n + 1 (exact) | undecided: n^1.7 (rms 0.29) or 1.02^n (rms 0.43) | n^0.98 (R² 1.000) / 1.01^n (R² 0.876); last local exponents 1.0, 1.0, 1.0; last per-step factors 1.02, 1.01, 1.01 | – | completed |
| FULL-eqsolve | too few points (3) | too few points (3) | n^0.02 (R² 0.001) / 1.01^n (R² 0.049); last local exponents -1.3, 1.4; last per-step factors 0.89, 1.06 | – | timeout (>20 s) at n=64; fitted on n=8..32 (rejected, resource bound hit); resource bound (`budget`) hit from n=8; verdict differs from the intended one at n=8..32 |

Leave-one-out configurations (same counter):

| n | FULL-eqsolve count | FULL-eqsolve ms |
|---:|---:|---:|
| 1 | 72 | 6.4 |
| 2 | 223 | 4.1 |
| 4 | 3,592 | 78.6 |
| 8 | 42,330 ✗ [B] | 1,271 |
| 16 | 16,968 ✗ [B] | 1,035 |
| 32 | 43,816 ✗ [B] | 4,406 |
| 64 | timeout | >20 s |

### req-neg

Ill-typed: req_traits where the caller lacks the last requirement. Intended verdict: rejected. Primary counter: `summon.matches`.

| n | base count | base ms | FIX count | FIX ms | MIN5 count | MIN5 ms | FULL count | FULL ms |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 141 | 30.8 | 141 | 17.1 | 1 | 1.3 | 1 | 3.2 |
| 2 | 215 | 51.6 | 215 | 16.3 | 3 | 2.6 | 2 | 8.4 |
| 4 | 369 | 64.9 | 369 | 26.9 | 7 | 3.1 | 4 | 4.5 |
| 8 | 701 | 38.1 | 701 | 34.0 | 15 | 7.7 | 8 | 5.4 |
| 16 | 1,461 | 140 | 1,461 | 57.1 | 31 | 3.4 | 16 | 8.4 |
| 32 | 3,365 | 386 | 3,365 | 126 | 63 | 5.6 | 32 | 6.5 |
| 64 | 8,709 | 1,098 | 8,709 | 639 | 127 | 19.1 | 64 | 8.6 |
| 128 | 25,541 | 4,591 | 25,541 | 3,407 | 255 | 40.0 | 128 | 25.9 |

| Configuration | Counter growth | Time growth | Counter: log-log fit / semi-log fit (upper half of the sizes), local exponents, per-step factors | Fastest other counter | Ends with |
|---|---|---|---|---|---|
| base | n^2 + 71n + 69 (exact) | n^1.69 for n ≥ 8 (rms 0.10) | n^1.38 (R² 0.997) / 1.02^n (R² 0.948); last local exponents 1.2, 1.4, 1.6; last per-step factors 1.05, 1.03, 1.02 | – | completed |
| FIX | n^2 + 71n + 69 (exact) | n^2.43 for n ≥ 4 (rms 0.09) | n^1.38 (R² 0.997) / 1.02^n (R² 0.948); last local exponents 1.2, 1.4, 1.6; last per-step factors 1.05, 1.03, 1.02 | – | completed |
| MIN5 | 2n − 1 (exact) | below 50 ms throughout | n^1.01 (R² 1.000) / 1.02^n (R² 0.918); last local exponents 1.0, 1.0, 1.0; last per-step factors 1.05, 1.02, 1.01 | – | completed |
| FULL | n (exact) | below 50 ms throughout | n^1.00 (R² 1.000) / 1.02^n (R² 0.920); last local exponents 1.0, 1.0, 1.0; last per-step factors 1.04, 1.02, 1.01 | – | completed |
| FULL-absmodel | 2n − 1 (exact) | below 50 ms throughout | n^1.01 (R² 1.000) / 1.02^n (R² 0.918); last local exponents 1.0, 1.0, 1.0; last per-step factors 1.05, 1.02, 1.01 | – | completed |

Leave-one-out configurations (same counter):

| n | FULL-absmodel count | FULL-absmodel ms |
|---:|---:|---:|
| 1 | 1 | 4.8 |
| 2 | 3 | 7.3 |
| 4 | 7 | 2.8 |
| 8 | 15 | 7.5 |
| 16 | 31 | 12.1 |
| 32 | 63 | 9.5 |
| 64 | 127 | 7.4 |
| 128 | 255 | 22.6 |

