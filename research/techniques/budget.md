# `budget`: abandon (and report) runaway implicit resolutions

**Status:** semantic fix (it turns crashes into errors), part of the final configuration.

## How it works

The breadth-first search in `takeSummonResults` keeps every live thread of a layer. On divergent or branching givens that the abstract model cannot refute, the frontier grows exponentially until allocation fails. Review2's `div-trunc-b3.hylo` and the FIX column of `div-eq-ovl-*` ended in "failed to allocate".

With `budget`:
- When a layer completes with no result and a frontier larger than `HYLO_TC_BUDGET` threads (default 100,000), the resolution is abandoned.
- The checker reports "implicit resolution is too complex: more than N candidate derivations; consider adding explicit type arguments or annotations", once per scope.

## Why it is sound

- Abandoning a resolution can only make a goal fail.
- A failed resolution could still steer overload or extension selection to another candidate. Because the abandonment is reported as an error, the program is rejected in every case.
- No accepted program changes meaning, and no program the depth cap rejects becomes accepted.
- The corpus oracle is identical: no corpus resolution comes near the limit.

## What it speeds up

It bounds memory and time on runaway searches:

| program | before | with `budget` |
|---|---|---|
| div-trunc-b3, FIX | out of memory after 38 s | rejected in 3.4 s |
| div-trunc-b3, FULL | rejected in 11.9 s | rejected in 5.8 s |

## Costs

- A valid program that genuinely needs a frontier above the limit is rejected. The baseline would run out of memory on it, or reach the depth cap.
- The limit is a tunable, not a semantic rule. A principled replacement is an abstract model that refutes these goals (see `absmodel` §4.3, `div-branch-trunc`).
