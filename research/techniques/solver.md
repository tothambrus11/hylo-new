# `solver` (unsound, needs a redesign): deferred overload branching with forward checking

## How it works

1. Overload constraints are parked until the other goals have been processed.
2. Each candidate is probed in a forked solver that propagates to quiescence.
3. Candidates with more errors than the best are dropped.
4. A sole survivor is committed in place. Otherwise the solver branches on the set with the fewest survivors.

This turns kⁿ exploration of independent overload sets into a sum:
- ovl-8-8: 38.7 s → 31 ms;
- ovl-4-8: 7.4 s → 5 ms;
- ovr-3-8: 375 → 4 ms.

## Why it is NOT sound

The baseline's result depends on the order in which overloads are branched on and ranked. Parking and most-constrained-first change that order. Confirmed counterexamples (`research/review/solver/`):
- **S1.** A valid program is rejected: parking changes how a join variable is bound under a `where T == U` equality.
- **S2.** Choosing the set with the fewest survivors changes which set is ranked at the outer level. The bindings differ, and acceptance flips in both directions.
- **S3.** In `positive/overload-priority.hylo`, node 0:75 is typed `A<Void>` instead of the alias `X`, because of the processing order.
- Not verified: the coercion witnesses differ, and the diagnostics differ under nested ambiguity.

It also gives no benefit on the stdlib (338 probes, 0 pruned).

## Way forward

The verifiers' fix keeps the baseline's branch points:
1. Resolve each overload set where the baseline pops it, instead of parking it.
2. Probe with "stop at the next overload", so the probe's error count is a lower bound for that choice.
3. Commit only a sole survivor, and otherwise branch in baseline order.

This keeps the exponential-to-linear win on independent overload sets (`solver1` in `ideas/RESULTS-round2.md`). It still has to pass semtest plus `review/solver/*.hylo`.
